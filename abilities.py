"""
abilities.py — Vampire leveling and ability system.

XP is earned by successfully using powers.
Level ups grant a choice between a passive buff OR an active power unlock.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class AbilityType(Enum):
    PASSIVE = auto()
    ACTIVE = auto()


@dataclass
class Ability:
    id: str
    name: str
    description: str
    kind: AbilityType
    unlock_level: int  # minimum level required
    # For passives: applied automatically each interaction
    # For actives: triggered manually (key 6/7/8 in interact screen)
    active_key: Optional[str] = None  # e.g. "6"
    active_cost: int = 0  # blood cost for active use


# ── All abilities in the game ─────────────────────────────────────────────────

ALL_ABILITIES = [

    # ── Passives ──────────────────────────────────────────────────────────────
    Ability(
        id="ancient_presence",
        name="Ancient Presence",
        description="Your 1000 years radiate power. All power rolls gain +1.",
        kind=AbilityType.PASSIVE,
        unlock_level=2,
    ),
    Ability(
        id="blood_efficiency",
        name="Blood Efficiency",
        description="Centuries of control honed your technique. All powers cost 3 less blood.",
        kind=AbilityType.PASSIVE,
        unlock_level=2,
    ),
    Ability(
        id="predators_eye",
        name="Predator's Eye",
        description="You see weakness before you strike. Resistance bars are always revealed.",
        kind=AbilityType.PASSIVE,
        unlock_level=3,
    ),
    Ability(
        id="dark_charisma",
        name="Dark Charisma",
        description="Your charm is supernaturally potent. Charm rolls gain +3.",
        kind=AbilityType.PASSIVE,
        unlock_level=3,
    ),
    Ability(
        id="iron_will",
        name="Iron Will",
        description="Failed powers no longer raise suspicion by more than 10.",
        kind=AbilityType.PASSIVE,
        unlock_level=4,
    ),
    Ability(
        id="lords_authority",
        name="Lord's Authority",
        description="Intimidate rolls gain +4. Terrified NPCs never flee.",
        kind=AbilityType.PASSIVE,
        unlock_level=4,
    ),
    Ability(
        id="blood_bond",
        name="Blood Bond",
        description="Enthrall costs 10 less blood for all NPCs.",
        kind=AbilityType.PASSIVE,
        unlock_level=5,
    ),

    # ── Actives ───────────────────────────────────────────────────────────────
    Ability(
        id="bat_swarm",
        name="Bat Swarm",
        description="Summon a swarm of bats. Hostile NPCs in the room are stunned — you escape without suspicion.",
        kind=AbilityType.ACTIVE,
        unlock_level=2,
        active_key="6",
        active_cost=20,
    ),
    Ability(
        id="mist_form",
        name="Mist Form",
        description="Dissolve into shadow. Pass through a room without being detected by any NPC.",
        kind=AbilityType.ACTIVE,
        unlock_level=3,
        active_key="7",
        active_cost=25,
    ),
    Ability(
        id="dominate",
        name="Dominate",
        description="Overwhelm a mind instantly. Force an NPC into thrall with no roll — but costs massive blood.",
        kind=AbilityType.ACTIVE,
        unlock_level=5,
        active_key="8",
        active_cost=50,
    ),
    Ability(
        id="blood_feast",
        name="Blood Feast",
        description="Feed deeply on a charmed NPC. Restore 40 blood but reduce their loyalty.",
        kind=AbilityType.ACTIVE,
        unlock_level=3,
        active_key="6",
        active_cost=0,  # gives blood instead
    ),
    Ability(
        id="psychic_shriek",
        name="Psychic Shriek",
        description="Unleash a mental scream. All NPCs in the room lose 3 resistance for the rest of the run.",
        kind=AbilityType.ACTIVE,
        unlock_level=4,
        active_key="7",
        active_cost=30,
    ),
]

ABILITY_BY_ID = {a.id: a for a in ALL_ABILITIES}

# ── XP thresholds ─────────────────────────────────────────────────────────────

XP_PER_LEVEL = [0, 0, 30, 70, 130, 200]  # xp needed to reach each level
MAX_LEVEL = 5

# ── Level up offers ──────────────────────────────────────────────────────────

LEVEL_OFFERS: dict[int, list[str]] = {
    2: ["ancient_presence", "blood_efficiency", "bat_swarm"],
    3: ["predators_eye", "dark_charisma", "mist_form", "blood_feast"],
    4: ["iron_will", "lords_authority", "psychic_shriek"],
    5: ["blood_bond", "dominate"],
}


@dataclass
class AbilitySystem:
    xp: int = 0
    level: int = 1
    unlocked: list = field(default_factory=list)  # list of ability IDs
    pending_levelup: bool = False
    pending_offers: list = field(default_factory=list)  # ability IDs to choose from

    def add_xp(self, amount: int) -> bool:
        """Add XP. Returns True if leveled up."""
        if self.level >= MAX_LEVEL:
            return False
        self.xp += amount
        if self.xp >= XP_PER_LEVEL[self.level + 1]:
            self.level += 1
            self.pending_levelup = True
            offers = LEVEL_OFFERS.get(self.level, [])
            # Only offer abilities not already unlocked
            self.pending_offers = [o for o in offers if o not in self.unlocked][:3]
            return True
        return False

    def unlock(self, ability_id: str) -> None:
        if ability_id not in self.unlocked:
            self.unlocked.append(ability_id)
        self.pending_levelup = False
        self.pending_offers = []

    def has(self, ability_id: str) -> bool:
        return ability_id in self.unlocked

    def get_actives(self) -> list:
        return [ABILITY_BY_ID[aid] for aid in self.unlocked
                if ABILITY_BY_ID[aid].kind == AbilityType.ACTIVE]

    def get_passives(self) -> list:
        return [ABILITY_BY_ID[aid] for aid in self.unlocked
                if ABILITY_BY_ID[aid].kind == AbilityType.PASSIVE]

    def xp_to_next(self) -> int:
        if self.level >= MAX_LEVEL:
            return 0
        return XP_PER_LEVEL[self.level + 1] - self.xp

    def xp_progress(self) -> float:
        """0.0 – 1.0 progress to next level."""
        if self.level >= MAX_LEVEL:
            return 1.0
        needed = XP_PER_LEVEL[self.level + 1] - XP_PER_LEVEL[self.level]
        earned = self.xp - XP_PER_LEVEL[self.level]
        return min(1.0, earned / max(1, needed))

    # ── Passive bonus getters ─────────────────────────────────────────────────

    def roll_bonus(self) -> int:
        bonus = 0
        if self.has("ancient_presence"): bonus += 1
        return bonus

    def blood_cost_reduction(self) -> int:
        red = 0
        if self.has("blood_efficiency"): red += 3
        return red

    def charm_roll_bonus(self) -> int:
        bonus = 0
        if self.has("dark_charisma"): bonus += 3
        return bonus

    def intimidate_roll_bonus(self) -> int:
        bonus = 0
        if self.has("lords_authority"): bonus += 4
        return bonus

    def max_suspicion_on_fail(self) -> int:
        """Cap on suspicion gain per failure."""
        if self.has("iron_will"):
            return 10
        return 999  # no cap

    def enthrall_discount(self) -> int:
        if self.has("blood_bond"):
            return 10
        return 0

    # ── XP awards by action ───────────────────────────────────────────────────

    XP_TABLE = {
        "read_success": 5,
        "charm_success": 15,
        "charm_partial": 5,
        "intimidate_success": 12,
        "intimidate_partial": 4,
        "enthrall_success": 20,
        "enthrall_partial": 8,
        "court_joined": 10,
    }

    def award(self, event: str) -> int:
        """Award XP for an event. Returns XP gained."""
        amount = self.XP_TABLE.get(event, 0)
        self.add_xp(amount)
        return amount
