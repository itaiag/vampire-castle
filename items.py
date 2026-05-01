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

    # ── Common ────────────────────────────────────────────────────────────────

    Item(
        id="bone_ring",
        name="Bone Ring",
        description="Intimidate skill +1",
        flavor="Carved from the finger-bone of a condemned man. Carries his last terror.",
        rarity="common",
        effect=ItemEffect(type="skill_intimidate", value=1),
    ),

    Item(
        id="charm_dust",
        name="Vial of Compulsion Dust",
        description="Charm skill +1",
        flavor="A pinch of this powder in the air and lesser minds grow... agreeable.",
        rarity="common",
        effect=ItemEffect(type="skill_charm", value=1),
    ),

    Item(
        id="grave_soil",
        name="Pouch of Grave Soil",
        description="Feed restores +5 extra blood",
        flavor="Soil from the oldest grave in the castle yard. It remembers older hungers.",
        rarity="common",
        effect=ItemEffect(type="feed_bonus", value=5),
    ),

    Item(
        id="hollow_candle",
        name="Hollow Black Candle",
        description="Max blood +10",
        flavor="Burns without melting. Inside, something ancient pulses like a second heart.",
        rarity="common",
        effect=ItemEffect(type="max_blood", value=10),
    ),

    Item(
        id="iron_talisman",
        name="Iron Talisman",
        description="Reduces suspicion gained by 10%",
        flavor="An unremarkable iron disc. But no one seems to notice you when you hold it.",
        rarity="common",
        effect=ItemEffect(type="suspicion_mult", value=10),
    ),

    # ── Rare ──────────────────────────────────────────────────────────────────

    Item(
        id="witches_brooch",
        name="Witch's Gilded Brooch",
        description="Charm skill +2",
        flavor="Found on a hanged woman who they say could make men love her at will.",
        rarity="rare",
        effect=ItemEffect(type="skill_charm", value=2),
    ),

    Item(
        id="terror_cloak",
        name="Mantle of Dread",
        description="Intimidate skill +2",
        flavor="A cloak stitched from the skins of your old enemies' fears. They never forget.",
        rarity="rare",
        effect=ItemEffect(type="skill_intimidate", value=2),
    ),

    Item(
        id="obsidian_eye",
        name="Obsidian Eye",
        description="Max blood +25",
        flavor="A carved stone eye, black as a collapsed star. It drinks in light — and vitality.",
        rarity="rare",
        effect=ItemEffect(type="max_blood", value=25),
    ),

    Item(
        id="shadow_coin",
        name="Shadow Coin",
        description="Feed restores +20 extra blood",
        flavor="Old currency from a kingdom that fed its royalty on the life-force of servants.",
        rarity="rare",
        effect=ItemEffect(type="feed_bonus", value=20),
    ),

    Item(
        id="mindshackle_chain",
        name="Mindshackle Chain",
        description="Enthrall skill +2",
        flavor="Thin silver links etched with runes that bypass will entirely. Not subtle. Effective.",
        rarity="rare",
        effect=ItemEffect(type="skill_enthrall", value=2),
    ),

    Item(
        id="wraithskin_wrap",
        name="Wraithskin Wrap",
        description="Reduces suspicion gained by 30%",
        flavor="Dried membrane from a ghost-touched corpse. Wrapping it around your wrist makes you feel... less present.",
        rarity="rare",
        effect=ItemEffect(type="suspicion_mult", value=30),
    ),

    # ── Legendary ─────────────────────────────────────────────────────────────

    Item(
        id="crown_of_old_night",
        name="Crown of Old Night",
        description="Max blood +50",
        flavor="Your crown from the first age. It sat in the dark a thousand years waiting. It remembers your name.",
        rarity="legendary",
        effect=ItemEffect(type="max_blood", value=50),
    ),

    Item(
        id="ancient_signet",
        name="Signet of the Blood Lords",
        description="Enthrall skill +3",
        flavor="The seal of the ancient vampire council. Showing it does not ask for obedience. It simply takes it.",
        rarity="legendary",
        effect=ItemEffect(type="skill_enthrall", value=3),
    ),

    Item(
        id="veil_of_ages",
        name="Veil of Ages",
        description="Reduces suspicion gained by 50%",
        flavor="Woven from centuries of practiced deception. Wearing it, you are whatever anyone needs you to be.",
        rarity="legendary",
        effect=ItemEffect(type="suspicion_mult", value=50),
    ),

    Item(
        id="lords_chalice",
        name="The Tyrant's Chalice",
        description="Charm skill +3",
        flavor="Passed between conquerors for a thousand years. It learned something from each one: how to make them loved.",
        rarity="legendary",
        effect=ItemEffect(type="skill_charm", value=3),
    ),

    Item(
        id="eternal_harvest",
        name="Eternal Harvest Flask",
        description="Feed restores +35 extra blood",
        flavor="A flask that is never empty. Its previous owners all died well-fed, and very, very old.",
        rarity="legendary",
        effect=ItemEffect(type="feed_bonus", value=35),
    ),
]}
