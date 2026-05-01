"""
player.py — The vampire player character.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npc import NPC


@dataclass
class Player:
    # Blood resource (0–100)
    blood: int = 80
    max_blood: int = 100

    # Skill levels (1–10); affect power roll success chance
    charm_skill: int = 4
    intimidate_skill: int = 3
    enthrall_skill: int = 3

    # Castle suspicion (0–100); hits 100 = hunters arrive, run ends
    castle_suspicion: int = 0

    # NPCs currently in your court
    court: list = field(default_factory=list)

    # Secrets learned (NPC names whose thoughts have been read)
    secrets_known: list = field(default_factory=list)

    # Position on the map (room index)
    current_room: int = 0

    # Marriage (for victory conditions)
    married_to: str = ""  # NPC name if married, empty string otherwise

    def add_to_court(self, npc: "NPC") -> None:
        if npc not in self.court:
            self.court.append(npc)

    def raise_suspicion(self, amount: int) -> None:
        self.castle_suspicion = min(100, self.castle_suspicion + amount)

    def lower_suspicion(self, amount: int) -> None:
        self.castle_suspicion = max(0, self.castle_suspicion - amount)

    def feed(self, amount: int = 25) -> str:
        gained = min(amount, self.max_blood - self.blood)
        self.blood += gained
        return f"You feed. Blood restored by {gained}."

    def is_alert_triggered(self) -> bool:
        return self.castle_suspicion >= 100

    def suspicion_label(self) -> str:
        s = self.castle_suspicion
        if s < 20:  return "Calm"
        if s < 40:  return "Uneasy"
        if s < 60:  return "Suspicious"
        if s < 80:  return "Alarmed"
        if s < 100: return "Hunting"
        return "HUNTERS ARRIVE"

    def suspicion_color(self) -> tuple:
        s = self.castle_suspicion
        if s < 20:  return (100, 200, 120)
        if s < 40:  return (200, 200, 80)
        if s < 60:  return (220, 160, 60)
        if s < 80:  return (220, 100, 60)
        return (220, 60, 60)
