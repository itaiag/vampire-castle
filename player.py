"""
player.py — The vampire player character.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from npc import NPC
    from items import Item


@dataclass
class Player:
    # Blood resource
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
    married_to: str = ""

    # Inventory
    inventory: list = field(default_factory=list)   # list of Item objects
    item_ids: set = field(default_factory=set)      # IDs already owned (prevents duplicates)

    # ── Court ─────────────────────────────────────────────────────────────────

    def add_to_court(self, npc: "NPC") -> None:
        if npc not in self.court:
            self.court.append(npc)

    # ── Items ─────────────────────────────────────────────────────────────────

    def add_item(self, item: "Item") -> str:
        """Add an item to inventory and apply its permanent effect. Returns a log message."""
        if item.id in self.item_ids:
            return f"You already carry the {item.name}."
        self.item_ids.add(item.id)
        self.inventory.append(item)
        effect = item.effect
        if effect.type == "max_blood":
            self.max_blood += effect.value
        elif effect.type == "skill_charm":
            self.charm_skill += effect.value
        elif effect.type == "skill_intimidate":
            self.intimidate_skill += effect.value
        elif effect.type == "skill_enthrall":
            self.enthrall_skill += effect.value
        # "suspicion_mult" and "feed_bonus" are computed dynamically from inventory
        labels = {"common": "Common", "rare": "Rare", "legendary": "LEGENDARY"}
        rarity = labels.get(item.rarity, item.rarity.title())
        return f"★ Found [{rarity}] {item.name}: {item.description}"

    def suspicion_reduction_pct(self) -> float:
        """Fractional suspicion reduction from all held items (capped at 0.90)."""
        total = sum(i.effect.value for i in self.inventory if i.effect.type == "suspicion_mult")
        return min(0.90, total / 100.0)

    def extra_feed(self) -> int:
        """Flat bonus blood gained per Feed action from held items."""
        return sum(i.effect.value for i in self.inventory if i.effect.type == "feed_bonus")

    # ── Blood & suspicion ─────────────────────────────────────────────────────

    def raise_suspicion(self, amount: int) -> None:
        if amount <= 0:
            return
        reduction = self.suspicion_reduction_pct()
        reduced = max(1, int(amount * (1.0 - reduction)))
        self.castle_suspicion = min(100, self.castle_suspicion + reduced)

    def lower_suspicion(self, amount: int) -> None:
        self.castle_suspicion = max(0, self.castle_suspicion - amount)

    def feed(self, amount: int = 25) -> str:
        bonus = self.extra_feed()
        total = amount + bonus
        gained = min(total, self.max_blood - self.blood)
        self.blood += gained
        bonus_str = f" (+{bonus} from items)" if bonus > 0 else ""
        return f"You feed. Blood restored by {gained}{bonus_str}."

    # ── Status ────────────────────────────────────────────────────────────────

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
