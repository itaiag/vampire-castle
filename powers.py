"""
powers.py — Vampire power resolution engine.

Every power attempt rolls against the NPC's resistance stat,
modified by the player's blood level and skill.
Failure always has consequences.
"""

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npc import NPC
    from player import Player


class PowerResult(Enum):
    SUCCESS       = auto()
    PARTIAL       = auto()   # costs extra blood, partial effect
    FAIL          = auto()   # no effect, NPC reacts negatively
    CRITICAL_FAIL = auto()   # worst case — alarm raised, NPC hostile


@dataclass
class ActionResult:
    power: str
    result: PowerResult
    dialogue: str          # what the NPC says
    log_message: str       # what appears in the event log
    suspicion_delta: int   # how much castle suspicion changes
    blood_cost: int        # blood actually spent


# ── Consequence helpers ───────────────────────────────────────────────────────

def _apply_charm_success(npc: "NPC") -> None:
    from npc import NPCState
    npc.state = NPCState.LOYAL
    npc.suspicion = max(0, npc.suspicion - 10)


def _apply_charm_fail(npc: "NPC", critical: bool) -> int:
    """Returns suspicion delta."""
    from npc import NPCState
    if critical:
        npc.state = NPCState.HOSTILE
        npc.suspicion += 30
        return 30
    else:
        npc.state = NPCState.SUSPICIOUS
        npc.suspicion += 15
        return 15


def _apply_intimidate_success(npc: "NPC") -> None:
    from npc import NPCState
    npc.state = NPCState.TERRIFIED
    npc.suspicion += 5   # they're scared but contained for now


def _apply_intimidate_fail(npc: "NPC", critical: bool) -> int:
    from npc import NPCState
    if critical:
        npc.state = NPCState.FLED
        npc.suspicion += 40
        return 40
    else:
        npc.state = NPCState.HOSTILE
        npc.suspicion += 25
        return 25


def _apply_enthrall_success(npc: "NPC") -> None:
    from npc import NPCState
    npc.state = NPCState.THRALL
    npc.suspicion = 0


def _apply_enthrall_fail(npc: "NPC", critical: bool) -> int:
    from npc import NPCState
    if critical:
        npc.state = NPCState.HOSTILE
        npc.suspicion += 50
        return 50
    else:
        npc.state = NPCState.SUSPICIOUS
        npc.suspicion += 20
        return 20


# ── Roll logic ────────────────────────────────────────────────────────────────

def _roll(player_power: int, npc_resistance: int, blood_percent: float) -> PowerResult:
    """
    Roll a d20, add player_power, subtract npc_resistance.
    blood_percent (0.0–1.0) gives a bonus when high, penalty when low.

    Thresholds:
      >= 15  → SUCCESS
      10–14  → PARTIAL
      5–9    → FAIL
      < 5    → CRITICAL_FAIL
    """
    blood_bonus = int((blood_percent - 0.5) * 6)   # -3 to +3
    roll = random.randint(1, 20) + player_power - npc_resistance + blood_bonus

    if roll >= 15:
        return PowerResult.SUCCESS
    elif roll >= 10:
        return PowerResult.PARTIAL
    elif roll >= 5:
        return PowerResult.FAIL
    else:
        return PowerResult.CRITICAL_FAIL


# ── Public power functions ────────────────────────────────────────────────────

def use_read_thoughts(player: "Player", npc: "NPC") -> ActionResult:
    blood_cost = 5
    if player.blood < blood_cost:
        return ActionResult(
            power="Read Thoughts",
            result=PowerResult.FAIL,
            dialogue="You lack the blood to reach into their mind.",
            log_message="Not enough blood to read thoughts.",
            suspicion_delta=0,
            blood_cost=0,
        )

    result = _roll(player.charm_skill, npc.charm_resistance, player.blood / player.max_blood)
    player.blood -= blood_cost

    if result in (PowerResult.SUCCESS, PowerResult.PARTIAL):
        npc.thoughts_read = True
        return ActionResult(
            power="Read Thoughts",
            result=PowerResult.SUCCESS,
            dialogue=npc.thought_read_line,
            log_message=f"You read {npc.name}'s thoughts. Secret revealed.",
            suspicion_delta=0,
            blood_cost=blood_cost,
        )
    elif result == PowerResult.FAIL:
        npc.suspicion += 10
        npc.state = __import__('npc').NPCState.SUSPICIOUS
        return ActionResult(
            power="Read Thoughts",
            result=PowerResult.FAIL,
            dialogue="Something feels wrong. Stay back!",
            log_message=f"{npc.name} felt your intrusion. They are now suspicious.",
            suspicion_delta=10,
            blood_cost=blood_cost,
        )
    else:  # CRITICAL_FAIL
        npc.suspicion += 25
        npc.state = __import__('npc').NPCState.HOSTILE
        return ActionResult(
            power="Read Thoughts",
            result=PowerResult.CRITICAL_FAIL,
            dialogue="GET OUT OF MY HEAD! HELP! THERE'S A MONSTER!",
            log_message=f"Critical fail! {npc.name} felt the violation and turned hostile. Suspicion +25.",
            suspicion_delta=25,
            blood_cost=blood_cost,
        )


def use_charm(player: "Player", npc: "NPC") -> ActionResult:
    blood_cost = 10
    if player.blood < blood_cost:
        return ActionResult(
            power="Charm",
            result=PowerResult.FAIL,
            dialogue="You lack the blood to project your presence.",
            log_message="Not enough blood to charm.",
            suspicion_delta=0,
            blood_cost=0,
        )

    result = _roll(player.charm_skill, npc.charm_resistance, player.blood / player.max_blood)
    player.blood -= blood_cost

    if result == PowerResult.SUCCESS:
        _apply_charm_success(npc)
        return ActionResult(
            power="Charm",
            result=PowerResult.SUCCESS,
            dialogue=npc.charm_success_line,
            log_message=f"{npc.name} is now loyal to you.",
            suspicion_delta=-10,
            blood_cost=blood_cost,
        )
    elif result == PowerResult.PARTIAL:
        # Partial: they're intrigued but not fully turned — costs extra blood, needs another attempt
        player.blood -= 5
        npc.charm_resistance = max(0, npc.charm_resistance - 2)
        return ActionResult(
            power="Charm",
            result=PowerResult.PARTIAL,
            dialogue="I... feel something. What are you? Come back and speak with me again.",
            log_message=f"Partial charm on {npc.name}. Their resistance weakened. Try again.",
            suspicion_delta=0,
            blood_cost=blood_cost + 5,
        )
    elif result == PowerResult.FAIL:
        delta = _apply_charm_fail(npc, critical=False)
        return ActionResult(
            power="Charm",
            result=PowerResult.FAIL,
            dialogue=npc.charm_fail_line,
            log_message=f"Charm failed. {npc.name} is now suspicious. Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )
    else:  # CRITICAL_FAIL
        delta = _apply_charm_fail(npc, critical=True)
        return ActionResult(
            power="Charm",
            result=PowerResult.CRITICAL_FAIL,
            dialogue=npc.charm_fail_line + " SOMEONE HELP!",
            log_message=f"Critical fail! {npc.name} turned hostile and is raising alarm! Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )


def use_intimidate(player: "Player", npc: "NPC") -> ActionResult:
    blood_cost = 8
    if player.blood < blood_cost:
        return ActionResult(
            power="Intimidate",
            result=PowerResult.FAIL,
            dialogue="You lack the presence to terrify them.",
            log_message="Not enough blood to intimidate.",
            suspicion_delta=0,
            blood_cost=0,
        )

    result = _roll(player.intimidate_skill, npc.intimidate_resistance, player.blood / player.max_blood)
    player.blood -= blood_cost

    if result == PowerResult.SUCCESS:
        _apply_intimidate_success(npc)
        return ActionResult(
            power="Intimidate",
            result=PowerResult.SUCCESS,
            dialogue=npc.intimidate_success_line,
            log_message=f"{npc.name} is terrified and compliant. Unstable — keep watch.",
            suspicion_delta=5,
            blood_cost=blood_cost,
        )
    elif result == PowerResult.PARTIAL:
        npc.intimidate_resistance = max(0, npc.intimidate_resistance - 1)
        return ActionResult(
            power="Intimidate",
            result=PowerResult.PARTIAL,
            dialogue="What... what ARE you? I'm not afraid. I'm not! ...Stay back.",
            log_message=f"{npc.name} is shaken but not broken. Their resolve is weakening.",
            suspicion_delta=8,
            blood_cost=blood_cost,
        )
    elif result == PowerResult.FAIL:
        delta = _apply_intimidate_fail(npc, critical=False)
        return ActionResult(
            power="Intimidate",
            result=PowerResult.FAIL,
            dialogue=npc.intimidate_fail_line,
            log_message=f"Intimidation failed. {npc.name} turned hostile. Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )
    else:  # CRITICAL_FAIL
        delta = _apply_intimidate_fail(npc, critical=True)
        return ActionResult(
            power="Intimidate",
            result=PowerResult.CRITICAL_FAIL,
            dialogue=npc.intimidate_fail_line + " TO ME, ALL OF YOU!",
            log_message=f"Critical fail! {npc.name} fled and is warning the whole castle! Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )


def use_enthrall(player: "Player", npc: "NPC") -> ActionResult:
    blood_cost = npc.enthrall_blood_cost
    if player.blood < blood_cost:
        return ActionResult(
            power="Enthrall",
            result=PowerResult.FAIL,
            dialogue="You don't have enough blood to enthrall them.",
            log_message=f"Not enough blood. Enthralling {npc.name} costs {blood_cost} blood.",
            suspicion_delta=0,
            blood_cost=0,
        )

    result = _roll(player.enthrall_skill, npc.enthrall_resistance, player.blood / player.max_blood)
    player.blood -= blood_cost

    if result == PowerResult.SUCCESS:
        _apply_enthrall_success(npc)
        return ActionResult(
            power="Enthrall",
            result=PowerResult.SUCCESS,
            dialogue=npc.enthrall_success_line,
            log_message=f"{npc.name} is now your thrall. Permanently bound.",
            suspicion_delta=-5,
            blood_cost=blood_cost,
        )
    elif result == PowerResult.PARTIAL:
        player.blood -= blood_cost // 2
        return ActionResult(
            power="Enthrall",
            result=PowerResult.PARTIAL,
            dialogue="There is... something... pulling at me. What... who are you?",
            log_message=f"Partial enthrall. {npc.name}'s will is cracking. Another attempt will cost less.",
            suspicion_delta=5,
            blood_cost=blood_cost + blood_cost // 2,
        )
    elif result == PowerResult.FAIL:
        delta = _apply_enthrall_fail(npc, critical=False)
        return ActionResult(
            power="Enthrall",
            result=PowerResult.FAIL,
            dialogue=npc.enthrall_fail_line,
            log_message=f"Enthrall failed. {npc.name} felt the attempt. Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )
    else:  # CRITICAL_FAIL
        delta = _apply_enthrall_fail(npc, critical=True)
        return ActionResult(
            power="Enthrall",
            result=PowerResult.CRITICAL_FAIL,
            dialogue=npc.enthrall_fail_line,
            log_message=f"Critical fail on enthrall! {npc.name} turned hostile. Castle on high alert! Suspicion +{delta}.",
            suspicion_delta=delta,
            blood_cost=blood_cost,
        )
