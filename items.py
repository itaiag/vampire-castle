"""
items.py — Magic items system for Vampire Castle.

Items are passive relics found by inspecting rooms or claiming quest rewards.
Each item has an always-active effect that modifies player stats permanently
when added to the inventory.
"""

from dataclasses import dataclass


@dataclass
class ItemEffect:
    type: str    # "max_blood" | "skill_charm" | "skill_intimidate" | "skill_enthrall"
                 # | "suspicion_mult" | "feed_bonus"
    value: int   # flat bonus; for suspicion_mult: percentage reduction (e.g. 25 = 25% less)


@dataclass
class Item:
    id: str
    name: str
    description: str   # one line: what it does mechanically
    flavor: str        # gothic flavor text
    rarity: str        # "common" | "rare" | "legendary"
    effect: ItemEffect


# ── Item Definitions ──────────────────────────────────────────────────────────

ITEMS: dict[str, Item] = {item.id: item for item in [

    Item(
        id="crimson_chalice",
        name="Crimson Chalice",
        description="Max blood +20",
        flavor="An ancient vessel still humming with forgotten vitality.",
        rarity="rare",
        effect=ItemEffect(type="max_blood", value=20),
    ),

    Item(
        id="shadow_amulet",
        name="Shadow Amulet",
        description="Intimidate skill +1",
        flavor="Cold obsidian that makes your presence feel heavier, darker.",
        rarity="common",
        effect=ItemEffect(type="skill_intimidate", value=1),
    ),

    Item(
        id="silver_tongue",
        name="Silver Tongue Ring",
        description="Charm skill +1",
        flavor="An old ring engraved with words that bend lesser wills.",
        rarity="common",
        effect=ItemEffect(type="skill_charm", value=1),
    ),

    Item(
        id="mist_veil",
        name="Veil of Mist",
        description="Reduces suspicion gained by 25%",
        flavor="A shred of consecrated cloth that muffles the supernatural.",
        rarity="rare",
        effect=ItemEffect(type="suspicion_mult", value=25),
    ),

    Item(
        id="philosophers_stone",
        name="Philosopher's Stone",
        description="Enthrall skill +1",
        flavor="Amber crystal that resonates with the psychic frequencies of the mind.",
        rarity="rare",
        effect=ItemEffect(type="skill_enthrall", value=1),
    ),

    Item(
        id="court_medallion",
        name="Court Medallion",
        description="Feed restores +10 extra blood",
        flavor="The sigil of your old house, still radiating dominion over the castle.",
        rarity="common",
        effect=ItemEffect(type="feed_bonus", value=10),
    ),

    Item(
        id="blood_ruby",
        name="Blood Ruby",
        description="Max blood +15",
        flavor="A deep-red gem that pulses with stored vitality.",
        rarity="common",
        effect=ItemEffect(type="max_blood", value=15),
    ),

    Item(
        id="hunters_mask",
        name="Hunter's Mask",
        description="Reduces suspicion gained by 15%",
        flavor="Worn by the very hunters who once stalked you. Turned to your service now.",
        rarity="common",
        effect=ItemEffect(type="suspicion_mult", value=15),
    ),

    Item(
        id="",
        name="",
        description="",
        flavor=".",
        rarity="",
        effect=ItemEffect(type="skill_charm", value=9999),
    ),
]}
