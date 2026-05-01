"""
encounters.py — Outside venture system for Vampire Castle.

Once every 20 minutes the player can venture beyond the castle gate.
One encounter is chosen at random from all eligible encounters.

Some encounters are unique (NPC recruit / room unlock) and are removed
from the pool once completed.  All others repeat indefinitely.
"""

import random
from dataclasses import dataclass, field


VENTURE_COOLDOWN = 1   # 1 second for testing (normally 20 * 60 = 1200)


@dataclass
class Encounter:
    id: str
    title: str
    description: str          # atmospheric scene-setting
    outcome: str              # what actually happens / what you receive
    blood_reward: int = 0     # positive = gain, negative = lose
    xp_reward: int = 0
    suspicion_change: int = 0 # positive = more suspicion, negative = reduce
    item_id: str = ""         # optional item reward (key from items.ITEMS)
    recruitable_npc_id: str = ""  # key into ENCOUNTER_NPC_FACTORIES; "" = no NPC
    unlocks_room: int = -1        # room index to unlock; -1 = no room


# ═══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

ENCOUNTERS: list[Encounter] = [

    # ── Blood gain ────────────────────────────────────────────────────────────

    Encounter(
        id="hungry_farmer",
        title="The Desperate Farmer",
        description=(
            "A gaunt farmer staggers along the road, muttering about failed crops "
            "and empty purses. He doesn't notice you until it is too late."
        ),
        outcome="You feed with restraint. He will remember nothing come morning.",
        blood_reward=20, xp_reward=5, suspicion_change=5,
    ),

    Encounter(
        id="wolves_at_dusk",
        title="Wolves at Dusk",
        description=(
            "A pack of wolves circles you through the treeline, growling low. "
            "For one brief moment they mistake you for prey. "
            "Then they smell what you truly are."
        ),
        outcome="The pack scatters. One was too slow. You feed under the cold moon.",
        blood_reward=25,
    ),

    Encounter(
        id="hunters_camp",
        title="The Abandoned Camp",
        description=(
            "A campfire still glows orange in a clearing. "
            "Freshly killed game hangs from a branch nearby. "
            "The hunters have not gone far — but they are not here."
        ),
        outcome="You take what you need and vanish before they return.",
        blood_reward=30, suspicion_change=15,
    ),

    Encounter(
        id="blood_spring",
        title="The Blood Spring",
        description=(
            "Beneath a mossy boulder, you find a spring that runs dark and warm. "
            "Ancient. Supernatural. Fed by something deep underground."
        ),
        outcome="You drink deeply. The spring knows you. Your strength returns in full.",
        blood_reward=40, xp_reward=10,
    ),

    Encounter(
        id="cultists_ritual",
        title="Servants of the Dark",
        description=(
            "A ring of robed figures chants in a clearing, your old sigil drawn in ash. "
            "They are expecting you."
        ),
        outcome="They offer their blood willingly. You accept.",
        blood_reward=25, xp_reward=15, suspicion_change=-5,
    ),

    Encounter(
        id="plague_survivor",
        title="The Plague Survivor",
        description=(
            "A wretched figure drags themselves along the road. "
            "Fever, rags, the unmistakable smell of illness. "
            "The blood will be bitter."
        ),
        outcome="Poor nourishment, but beggars cannot choose.",
        blood_reward=10,
    ),

    Encounter(
        id="quiet_night",
        title="A Quiet Night",
        description=(
            "No prey. No threat. Just cold air, bare trees, "
            "and the distant sound of a river."
        ),
        outcome="The night restores you quietly. Sometimes nothing happening is a gift.",
        blood_reward=15, suspicion_change=-5,
    ),

    Encounter(
        id="moonlit_feast",
        title="A Village in the Dark",
        description=(
            "A small village lies unguarded. Most windows are dark. "
            "One lamp burns in a farmhouse. Inside, someone sits alone."
        ),
        outcome="You are careful. You are quiet. When you leave, the lamp still burns.",
        blood_reward=35, suspicion_change=10,
    ),

    Encounter(
        id="hidden_cellar",
        title="The Hidden Cellar",
        description=(
            "Beneath a collapsed barn you find a cellar still intact. "
            "Someone stored provisions here long ago. "
            "Dark, cold, forgotten — like you were."
        ),
        outcome="The cellar is full of life in every sense of the word.",
        blood_reward=30, xp_reward=5, item_id="grave_soil",
    ),

    Encounter(
        id="frost_fair",
        title="The Frost Fair",
        description=(
            "A travelling fair has set up at the crossroads, torches blazing. "
            "Merchants, performers, and fools crowd together for warmth. "
            "You move through them unseen."
        ),
        outcome="You observe, learn, and feed sparingly from the crowd's warmth.",
        blood_reward=10, xp_reward=20,
    ),

    Encounter(
        id="storm_refuge",
        title="The Storm Refuge",
        description=(
            "A storm rolls in from the east, violent and sudden. "
            "You take shelter in an old watchtower at the forest's edge. "
            "Something carved into the walls seems to calm the weather around you."
        ),
        outcome="The storm passes quickly. The tower seems to approve of you.",
        blood_reward=15, suspicion_change=-15,
    ),

    Encounter(
        id="massacre_site",
        title="The Aftermath",
        description=(
            "A battlefield — or what remains of one. "
            "The village was burned. The bodies were left where they fell. "
            "This was recent. This was done by your hunters."
        ),
        outcome=(
            "You learn something from the dead. Their fear still hangs in the air. "
            "It teaches you what to avoid — and what to become."
        ),
        blood_reward=15, xp_reward=30, suspicion_change=10,
    ),

    Encounter(
        id="old_hermit",
        title="The Hermit's Cave",
        description=(
            "High in the rocky hillside, a hermit has lived alone for thirty years. "
            "He has seen things no one believes. He believes them. "
            "He also believes you are not the worst thing he has seen."
        ),
        outcome="He shares hard-won wisdom. You leave him alive and oddly grateful.",
        blood_reward=5, xp_reward=25, item_id="hollow_candle",
    ),

    # ── XP rewards ────────────────────────────────────────────────────────────

    Encounter(
        id="wandering_herbalist",
        title="The Night Herbalist",
        description=(
            "An old woman gathers roots by moonlight, unafraid. "
            "'I've been waiting for one like you,' she says."
        ),
        outcome="She shares old knowledge. You feel sharper, more capable.",
        blood_reward=5, xp_reward=20, suspicion_change=-5,
    ),

    Encounter(
        id="travelling_bard",
        title="The Travelling Bard",
        description=(
            "A bard sits at a crossroads playing to no audience. "
            "He sings an old song. About a castle. About you, specifically."
        ),
        outcome="He knows more than he should. You take the knowledge and leave him a coin.",
        blood_reward=5, xp_reward=25,
    ),

    Encounter(
        id="ancient_library",
        title="The Burnt Library",
        description=(
            "The shell of a library stands at the edge of a village. "
            "The fire was recent. But books were buried before it spread."
        ),
        outcome="You dig. You read by moonlight. Centuries of knowledge in ash-stained pages.",
        xp_reward=30,
    ),

    Encounter(
        id="mercenary_captain",
        title="The Mercenary Captain",
        description=(
            "A lone soldier camps beside the road, waiting. "
            "He has heard rumours of what stirs in the castle."
        ),
        outcome="You speak cautiously. He knows tactics and alliances.",
        blood_reward=10, xp_reward=20,
    ),

    # ── Item rewards ──────────────────────────────────────────────────────────

    Encounter(
        id="burial_mound",
        title="The Old Burial Mound",
        description=(
            "A grassy hill hides a chamber far older than the castle. "
            "The stone door grinds open at your touch, as if recognising your authority."
        ),
        outcome="Among the dust and forgotten bones: a relic that remembers old power.",
        xp_reward=10, item_id="bone_ring",
    ),

    Encounter(
        id="night_market",
        title="The Midnight Market",
        description=(
            "Lanterns hang between trees where no road should be. "
            "Hooded figures trade in silence."
        ),
        outcome="You trade presence and authority for something they value less than you will.",
        item_id="charm_dust",
    ),

    Encounter(
        id="fallen_star",
        title="The Fallen Star",
        description=(
            "A streak of light splits the sky. "
            "The crater glows a deep, unnatural red."
        ),
        outcome="In the crater, cooling in the soil: something that should not exist.",
        xp_reward=15, item_id="blood_ruby",
    ),

    Encounter(
        id="grave_robbers",
        title="The Grave Robbers",
        description=(
            "Three men work feverishly in an old churchyard, prying open a noble's tomb. "
            "They freeze when you step from the dark."
        ),
        outcome="Their terror is its own reward. You take what they've uncovered.",
        blood_reward=20, item_id="hollow_candle",
    ),

    # ── Suspicion reduction ───────────────────────────────────────────────────

    Encounter(
        id="moonlit_shrine",
        title="The Moonlit Shrine",
        description=(
            "A stone shrine to a forgotten deity stands alone at the forest's edge. "
            "Not Christian — something far older. It has been here since before the castle."
        ),
        outcome=(
            "You kneel before it in recognition of age. "
            "The castle's watchers feel calmer tonight."
        ),
        blood_reward=5, xp_reward=10, suspicion_change=-20,
    ),

    # ── Dangerous encounters ──────────────────────────────────────────────────

    Encounter(
        id="hunter_patrol",
        title="The Hunter Patrol",
        description=(
            "Six silver-armed soldiers march the road in tight formation. "
            "One spots you. Then alarm."
        ),
        outcome="You escape, but not before they see you clearly. Word will spread.",
        blood_reward=-5, suspicion_change=25,
    ),

    Encounter(
        id="old_rival",
        title="The Old Rival",
        description=(
            "A hunter from before your long sleep. Aged, but not forgotten. "
            "They strike first."
        ),
        outcome="A brief, brutal exchange. Both of you survive. This is not over.",
        blood_reward=-15, xp_reward=10, suspicion_change=20,
    ),

    Encounter(
        id="cursed_crossroads",
        title="The Cursed Crossroads",
        description=(
            "Where four roads meet, the air bends wrong. "
            "The ground is saturated with old suffering."
        ),
        outcome="The place costs you vitality — but you find what was buried at the crossing.",
        blood_reward=-10, item_id="iron_talisman",
    ),

    # ── LEGENDARY NPC RECRUITMENT ─────────────────────────────────────────────

    Encounter(
        id="recruit_celestine",
        title="The Lady of Shadows",
        description=(
            "A woman of lethal beauty emerges from the darkness, jewels glinting at her throat. "
            "'I've heard whispers of you,' she says, circling you like a predator. "
            "'A vampire reclaiming his castle. How... ambitious.' Her smile is a knife."
        ),
        outcome=(
            "She plays at seduction while you sense she's calculating every word. "
            "'I could be useful to you, my lord. I have talents that money cannot buy.' "
            "She produces a stolen crown jewel from her pocket with a knowing smirk. "
            "'Shall we discuss terms?'"
        ),
        blood_reward=5, xp_reward=25, suspicion_change=-5, item_id="shadow_coin",
        recruitable_npc_id="celestine",
    ),

    # ── NPC RECRUITMENT (unique — removed from pool once complete) ────────────

    Encounter(
        id="recruit_gregori",
        title="The Gravedigger's Bargain",
        description=(
            "An old man sits on an overturned coffin in the cemetery clearing, "
            "eating black bread and not looking up. "
            "'Been waitin' for the old lord to come back,' he says. 'Work's been terrible.'"
        ),
        outcome=(
            "Gregori has buried half the province's secrets. "
            "He agrees to return to the castle and resume his old duties."
        ),
        blood_reward=5, xp_reward=15,
        recruitable_npc_id="gregori",
    ),

    Encounter(
        id="recruit_esme",
        title="The Witch's Request",
        description=(
            "A woman in patchwork robes crouches beside a dying fire, "
            "muttering over ingredients that glow and smoke. "
            "She looks up with violet eyes. 'I know what you are. I need your help.'"
        ),
        outcome=(
            "Esme has been cursed by a rival. She offers her considerable knowledge "
            "in exchange for sanctuary in your castle."
        ),
        xp_reward=20,
        recruitable_npc_id="esme",
    ),

    Encounter(
        id="recruit_roland",
        title="The Deserter's Confession",
        description=(
            "A man in stripped military clothes is camped under a thorn hedge, "
            "watching the road with hollow eyes. "
            "When he sees you, he doesn't run. 'I deserted the guild,' he says quietly."
        ),
        outcome=(
            "Roland left the hunter guild after witnessing what they truly are. "
            "He has skills. He has reason to help you. And nowhere else to go."
        ),
        xp_reward=15, blood_reward=10,
        recruitable_npc_id="roland",
    ),

    Encounter(
        id="recruit_petyr",
        title="The Merchant's Network",
        description=(
            "A well-dressed man sits in a roadside coaching inn, "
            "nursing wine and watching every face that enters. "
            "He waves you over before you've decided to approach. 'I know who you are.'"
        ),
        outcome=(
            "Petyr's merchant routes are cover for something else entirely. "
            "He offers his network's eyes and ears in exchange for your protection."
        ),
        blood_reward=15,
        recruitable_npc_id="petyr",
    ),

    Encounter(
        id="recruit_agnes",
        title="The Nun's Confession",
        description=(
            "A woman in novice robes kneels at a roadside cross, but prays "
            "in a language that predates the Church. "
            "She sees you and makes no sign of warding. Only relief."
        ),
        outcome=(
            "Sister Agnes has been hiding her true nature for years. "
            "She knows the castle's holy architecture better than anyone — and its gaps."
        ),
        xp_reward=10, suspicion_change=-10,
        recruitable_npc_id="agnes",
    ),

    Encounter(
        id="recruit_caius",
        title="The Knight Without a Lord",
        description=(
            "A man in dented armour sits beside the road, helmet off, "
            "watching the sunrise he can no longer prevent. "
            "'I have no lord,' he says. 'And I am beginning to think I need one.'"
        ),
        outcome=(
            "Sir Caius was stripped of his rank for refusing to massacre a village. "
            "He has been wandering ever since, looking for a cause worth swearing to."
        ),
        blood_reward=5, xp_reward=20,
        recruitable_npc_id="caius",
    ),

    # ── More varied encounters ────────────────────────────────────────────────

    Encounter(
        id="castle_spy",
        title="The Castle Spy",
        description=(
            "A cloaked figure waits at the forest's edge, eyes scanning the road. "
            "'I have information about your castle. About those inside.'"
        ),
        outcome="You learn the castle's secrets. Knowledge is power, after all.",
        xp_reward=35, suspicion_change=-10,
    ),

    Encounter(
        id="desperate_soldier",
        title="The Desperate Soldier",
        description=(
            "A young soldier in tattered colours sits beside the road, bleeding from a wound. "
            "His hand hovers near a sword that shakes in his grip."
        ),
        outcome="You offer mercy. He takes it gratefully. The blood steadies you.",
        blood_reward=20, xp_reward=8,
    ),

    Encounter(
        id="travelling_scholar",
        title="The Travelling Scholar",
        description=(
            "An old scholar sits beneath a tree with a stack of books, documenting the night sky. "
            "'Ah, a creature of darkness. I have been hoping to study you.'"
        ),
        outcome="You trade knowledge for blood. Both of you leave satisfied.",
        blood_reward=12, xp_reward=25,
    ),

    Encounter(
        id="crystal_grove",
        title="The Crystal Grove",
        description=(
            "A clearing shimmers with unnatural light. Crystals the size of trees grow from the earth, "
            "singing a frequency that only you can hear."
        ),
        outcome="The crystals resonate with your power. You feel restored in ways blood alone cannot achieve.",
        blood_reward=18, xp_reward=15, item_id="obsidian_eye",
    ),

    Encounter(
        id="widow_offering",
        title="The Widow's Offering",
        description=(
            "A grieving woman stands at a grave with a vial of blood. "
            "'For my husband's killer. For his memory. Take what you will.'"
        ),
        outcome="Vengeance tastes different from hunger. Darker. Deeper.",
        blood_reward=25, suspicion_change=15,
    ),

    Encounter(
        id="starving_beggar",
        title="The Starving Beggar",
        description=(
            "A skeletal figure stumbles along the road, muttering prayers to gods long forgotten. "
            "They do not even notice your approach."
        ),
        outcome="The blood is thin, but the gratitude is genuine. Almost worth something.",
        blood_reward=8, xp_reward=3,
    ),

    Encounter(
        id="ancient_ruin",
        title="The Ancient Ruin",
        description=(
            "Beneath fallen stone, you find the remains of a structure far older than your castle. "
            "Symbols cover every surface — the old language. Your language."
        ),
        outcome="You remember. Fragments of memory, buried centuries deep, return to you.",
        xp_reward=40, blood_reward=5,
    ),

    Encounter(
        id="moonlit_lake",
        title="The Moonlit Lake",
        description=(
            "A perfectly still lake reflects the moon so clearly it seems bottomless. "
            "The water shimmers with something else. Something old."
        ),
        outcome="You drink from waters that remember your throne. Your strength returns threefold.",
        blood_reward=45, xp_reward=10,
    ),

    Encounter(
        id="witch_sacrifice",
        title="The Witch's Sacrifice",
        description=(
            "A bound figure lies on a stone altar in the forest. A robed woman chants. "
            "As you approach, she smiles. 'Welcome, dark one. I made this offering for you.'"
        ),
        outcome="You feed. The witch watches with satisfaction. Some arrangements benefit all parties.",
        blood_reward=35, suspicion_change=20, item_id="charm_dust",
    ),

    Encounter(
        id="fleeing_noble",
        title="The Fleeing Noble",
        description=(
            "A richly-dressed figure on horseback flees down the road at full gallop. "
            "Behind them, torches. Hunters. They don't see you until too late."
        ),
        outcome="You grant them an escape. Nobility, after all, is a matter of perspective.",
        blood_reward=28, suspicion_change=25,
    ),

    Encounter(
        id="forgotten_shrine",
        title="The Forgotten Shrine",
        description=(
            "A temple, half-swallowed by the earth, dedicated to gods no one remembers. "
            "Inside, candlelight that burns without fuel."
        ),
        outcome="The shrine knows what you are. It welcomes you home.",
        blood_reward=20, xp_reward=15, suspicion_change=-25,
    ),

    Encounter(
        id="beast_den",
        title="The Beast's Den",
        description=(
            "A great creature lairs in the forest — something vast and hungry. "
            "When it sees you, it bows."
        ),
        outcome="The beasts of the night recognize their lord. You feed well this evening.",
        blood_reward=40, xp_reward=12,
    ),

    Encounter(
        id="cursed_village",
        title="The Cursed Village",
        description=(
            "A settlement wreathed in fog where no one moves. Every door is sealed. Every window dark. "
            "The curse here is old — older than the castle."
        ),
        outcome="You learn what cursed blood tastes like. It burns. It teaches.",
        blood_reward=15, xp_reward=20, suspicion_change=10,
    ),

    Encounter(
        id="mystic_caravan",
        title="The Mystic Caravan",
        description=(
            "Wagons painted in symbols of power rumble along the road. Inside, robed figures meditate. "
            "They know what you are. They welcome the darkness."
        ),
        outcome="You travel with them for the night. They ask nothing. You take what you need.",
        blood_reward=30, xp_reward=10, item_id="mist_veil",
    ),

    Encounter(
        id="rival_vampire",
        title="The Rival Vampire",
        description=(
            "Another of your kind steps from the shadows. Older, perhaps. Certainly hungrier. "
            "'This is my territory now,' they hiss."
        ),
        outcome="You remind them that some predators are far more predatory. They flee.",
        blood_reward=-20, xp_reward=30, suspicion_change=5,
    ),

    # ── ROOM UNLOCK (unique — removed from pool once complete) ────────────────

    Encounter(
        id="unlock_cemetery",
        title="The Iron Gate",
        description=(
            "Beyond the castle's eastern wall, half-hidden by decades of ivy, "
            "stands a wrought-iron gate. "
            "Beyond it: rows of old graves, each stone bearing your family's crest."
        ),
        outcome=(
            "The gate is sealed with a lock your old keys still fit. "
            "The castle cemetery is yours again."
        ),
        blood_reward=5, xp_reward=20,
        unlocks_room=16,
    ),

    Encounter(
        id="unlock_forge",
        title="The Rusted Forge",
        description=(
            "A stone building west of the castle gate, its chimney cold for centuries. "
            "Inside: bellows, anvils, a rack of half-finished blades. "
            "Your old armourer's mark is stamped into the door."
        ),
        outcome=(
            "The forge is still functional. The right person could bring it back to life. "
            "You clear the entrance and claim the building."
        ),
        xp_reward=15,
        unlocks_room=17,
    ),

    Encounter(
        id="unlock_catacombs",
        title="The Sunken Passage",
        description=(
            "During a night of heavy rain, the earth behind the dungeon shifts. "
            "A stone door, buried for ages, is now visible in the mud. "
            "The air that seeps through it is cold, still, and very old."
        ),
        outcome=(
            "The passage leads into something far deeper than the dungeon. "
            "The catacombs, sealed before the castle was built, are open."
        ),
        blood_reward=10, xp_reward=25,
        unlocks_room=18,
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER NPC FACTORIES
# ═══════════════════════════════════════════════════════════════════════════════

# Maps recruitable_npc_id → display name (for duplicate-check filtering)
ENCOUNTER_NPC_NAMES: dict[str, str] = {
    "celestine": "Lady Celestine",
    "gregori": "Gregori the Gravedigger",
    "esme":    "Esme the Hedge Witch",
    "roland":  "Roland the Deserter",
    "petyr":   "Petyr the Merchant",
    "agnes":   "Sister Agnes",
    "caius":   "Sir Caius the Knight",
}


def _make_celestine():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Celestine the Shadow",
        role=NPCRole.SPY,
        description="A woman of lethal beauty with calculating eyes. She moves like smoke and smiles like a viper. Every gesture is a weapon, every word a test. There is nothing innocent about her.",
        secret="She is a master thief and manipulator who has seduced her way into a dozen fortunes. She sees you not as a prize but as a tool — a powerful one. She's never loved anyone. Control is her only drug.",
        greeting="Well, well. A real vampire. How delicious. I think we can help each other, my lord. As long as you understand the rules.",
        likes=["power", "wealth", "secrets", "clever minds", "independence", "sharp steel", "winning"],
        dislikes=["sentiment", "weakness", "being caged", "boredom", "fools", "love"],
        charm_resistance=6, intimidate_resistance=4,
        enthrall_resistance=5, enthrall_blood_cost=25,
        charm_success_line="Clever. You might actually be useful. But don't mistake seduction for surrender.",
        charm_fail_line="Better luck next time, my lord. I don't fall easily.",
        intimidate_success_line="Oh, how delightful. A predator with teeth. I respect that. What do you want?",
        intimidate_fail_line="Threaten me and I'll disappear. You'll never find me. Is that what you want?",
        enthrall_success_line="How amusing. You've bent my will. But I'll remember this, master.",
        enthrall_fail_line="Nice try. I've broken stronger wills than yours. Don't waste my time.",
        thought_read_line="A mind like a locked vault filled with secrets, lies, and stolen treasures. She's calculating, always. She wonders what leverage she can find. She fears nothing except being forgettable.",
    )
    npc.add_dialogue(DialogNode(
        id="celestine_1",
        text="What do you want from me?",
        response="Everything I can take without getting caught. Information, resources, power. In exchange, I'll help you keep it. Win-win, don't you think?",
        affinity_change=5, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_2",
        text="I need someone I can trust completely.",
        response="Trust? How quaint. No one can be trusted completely. But I can be bought. And you, my lord, are very wealthy.",
        affinity_change=6, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_3",
        text="Work with me. Not for love, but for power.",
        response="Now that's a conversation. Yes, I'll work with you. Not because I love you — I don't love anyone. But because together, we can take anything we want.",
        requires=["celestine_1"], min_affinity=20,
        affinity_change=15, suspicion_change=-10,
        option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_special",
        text="Teach me your arts. I want to move unseen like you.",
        response="Oh, I like that. You understand. Very well. I'll teach you the shadows. Together we'll own this world.",
        requires=["celestine_3"], min_affinity=35,
        affinity_change=12, suspicion_change=-15,
        option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_steal",
        text="Go steal something precious. Make them paranoid.",
        response="Oh, how I love this. Watch and learn, my lord.",
        requires=["celestine_3"], min_affinity=25,
        affinity_change=8, blood_reward=5, suspicion_change=-20,
        option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_spy",
        text="I need information. Spy for me.",
        response="Spying is what I do best. Give me time. I'll know everything worth knowing.",
        requires=["celestine_3"], min_affinity=30,
        affinity_change=10, suspicion_change=-15,
        option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="celestine_partner",
        text="I'm making you my equal. My partner in shadows.",
        response="Finally. Someone who understands that love is a cage. Partners are so much better. We'll take everything.",
        requires=["celestine_special", "celestine_spy"], min_affinity=50,
        affinity_change=20, blood_reward=20, suspicion_change=-25,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_gregori():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Gregori the Gravedigger",
        role=NPCRole.SERVANT,
        description="A weathered old man in dirt-caked clothes, leaning on a shovel. He smells of earth and candle wax and seems perfectly at ease.",
        secret="He has buried three people alive over the decades — all at Morgana's orders. He regrets only that he did not refuse sooner.",
        greeting="Back at last, my lord. I kept the graves tidy while you slept. Most of 'em.",
        likes=["honesty", "silence", "order", "respect for the dead", "old ways"],
        dislikes=["Morgana", "desecration", "violence", "burning bodies", "hasty work"],
        charm_resistance=2, intimidate_resistance=3,
        enthrall_resistance=3, enthrall_blood_cost=12,
        charm_success_line="As you say, my lord. I'll fetch the spade.",
        charm_fail_line="I'm just a gravedigger. Leave an old man be.",
        intimidate_success_line="Alright, alright. I'll do what you need. No need for all that.",
        intimidate_fail_line="I've dug more graves than you've had warm meals. Don't threaten me.",
        enthrall_success_line="Your will. My hands. As it ever was.",
        enthrall_fail_line="My mind is full of the dead already! There's no room for you!",
        thought_read_line="Centuries of memory, all of it underground. He knows where every secret in this region is buried — literally.",
    )
    npc.add_dialogue(DialogNode(
        id="gregori_1",
        text="What have you been doing all these years?",
        response="Burying people, mostly. Some deserved it. Some didn't. That's the job.",
        affinity_change=5, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="gregori_2",
        text="Do you know the castle grounds well?",
        response="Every inch. I dug half the foundations. There are passages in this castle that aren't on any map.",
        affinity_change=8, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="gregori_3",
        text="Are there any useful things buried nearby?",
        response="Three sealed vaults that Morgana had filled. Old noble goods. I know where they all are.",
        requires=["gregori_2"], min_affinity=20,
        affinity_change=10, blood_reward=10, suspicion_change=-5,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_esme():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Esme the Hedge Witch",
        role=NPCRole.SPY,
        description="A woman in layered patchwork robes, her fingers always moving, always checking invisible threads in the air. Her eyes are an unsettling violet.",
        secret="She was cursed by another witch for stealing a forbidden grimoire. The curse slowly turns her memories to ash. She is running out of time.",
        greeting="I can feel the old power on you. Sit. Don't make any sudden movements near the ingredients.",
        likes=["knowledge", "magic", "honesty about power", "protecting the weak", "rare ingredients"],
        dislikes=["church", "hunters", "burning of knowledge", "cruelty", "waste"],
        charm_resistance=4, intimidate_resistance=2,
        enthrall_resistance=5, enthrall_blood_cost=18,
        charm_success_line="You have a warmth beneath the cold. I'll help you.",
        charm_fail_line="Your vampiric charm doesn't work quite the same on someone who can see magic.",
        intimidate_success_line="Fine! But you'll regret breaking a witch's things.",
        intimidate_fail_line="Threaten me again and I'll fill your coffin with nettles.",
        enthrall_success_line="My spells are yours, master. Use them wisely.",
        enthrall_fail_line="A vampire in my mind? Not today. SMOKE WARD!",
        thought_read_line="A brilliant and terrified mind. Spells, formulas, and underneath everything: the growing silence where her memories used to be.",
    )
    npc.add_dialogue(DialogNode(
        id="esme_1",
        text="What kind of magic do you practice?",
        response="Everything that works. Classification is for scholars. I'm interested in results.",
        affinity_change=5, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="esme_2",
        text="You mentioned a curse.",
        response="A colleague and I had a... disagreement over ownership of a book. She won. I'm still paying for it.",
        affinity_change=7, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="esme_3",
        text="Can you use your magic to help the castle?",
        response="I can ward rooms, brew compounds, spy through reflections. I can do a great deal if I have the ingredients. And the time.",
        requires=["esme_2"], min_affinity=20,
        affinity_change=10, suspicion_change=-8,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_roland():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Roland the Deserter",
        role=NPCRole.GUARD,
        description="A lean man in stripped military clothes, with the careful stillness of someone trained to survive. He watches the door more than he watches you.",
        secret="He witnessed the hunter guild massacre an entire village because of a rumour. He kept the commander's journal as insurance. It has everyone's name in it.",
        greeting="If you're planning to kill me, get it over with. Otherwise, sit down.",
        likes=["honesty", "protecting innocents", "second chances", "direct talk", "loyalty"],
        dislikes=["the hunter guild", "blind obedience", "cruelty", "Morgana", "betrayal"],
        charm_resistance=4, intimidate_resistance=5,
        enthrall_resistance=4, enthrall_blood_cost=20,
        charm_success_line="I'll trust you. God help me if I'm wrong again.",
        charm_fail_line="I've been lied to by better. Try harder.",
        intimidate_success_line="I'm not afraid to die. But I'll cooperate. For now.",
        intimidate_fail_line="You think I haven't been threatened by worse? Back off.",
        enthrall_success_line="I... my will is yours. Use it better than the guild did.",
        enthrall_fail_line="Not happening. I've resisted worse than a vampire's glare.",
        thought_read_line="Military discipline overlaid on deep guilt. The guild's journal is hidden somewhere close. It contains enough to destroy Morgana's alliances.",
    )
    npc.add_dialogue(DialogNode(
        id="roland_1",
        text="Why did you desert the guild?",
        response="I followed orders my whole life. Then the orders became something I couldn't follow and still call myself a person.",
        affinity_change=8, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="roland_2",
        text="What do you know about the hunters' plans?",
        response="I know their routes, their contacts, and two of their safe houses. I know what they're afraid of. I can make them afraid of it.",
        affinity_change=6, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="roland_3",
        text="I could use someone who knows how they operate.",
        response="I can counter them. I know every technique they use against your kind. I'm more valuable as an advisor than as a soldier.",
        requires=["roland_1"], min_affinity=25,
        affinity_change=12, blood_reward=8, suspicion_change=-10,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_petyr():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Petyr the Merchant",
        role=NPCRole.SPY,
        description="A well-dressed man with merchant's rings on every finger, whose eyes move faster than his smile. He always seems to know more than he lets on.",
        secret="He runs an underground intelligence network disguised as a trading company. He has sold information to every faction in the region — including the hunters.",
        greeting="I've been expecting someone from the castle. Sit down. You want information, yes?",
        likes=["good business", "mutually beneficial deals", "clever people", "discretion", "profit"],
        dislikes=["violence", "unprofitability", "poor negotiators", "loyalty without incentive"],
        charm_resistance=3, intimidate_resistance=4,
        enthrall_resistance=3, enthrall_blood_cost=15,
        charm_success_line="An excellent arrangement. I look forward to a profitable partnership.",
        charm_fail_line="I've negotiated with kings. Try again with better leverage.",
        intimidate_success_line="Fine, fine. Threatening a merchant is bad for business. I'll cooperate.",
        intimidate_fail_line="Violence is very bad for trade relationships. I must protest.",
        enthrall_success_line="My network is at your disposal, master. Every route, every contact.",
        enthrall_fail_line="I have friends everywhere. And yes, that is a threat.",
        thought_read_line="A web of information spanning half the continent. He has contacts in the hunter guild, the church, and three noble houses. He's sold everyone out. He'll sell you out too, unless you make it unprofitable.",
    )
    npc.add_dialogue(DialogNode(
        id="petyr_1",
        text="What exactly is your business?",
        response="Import, export, information. The third is the most profitable. People pay very well to know things — and to keep others from knowing them.",
        affinity_change=6, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="petyr_2",
        text="What do you know about the hunters searching for me?",
        response="Their leader's name, their payment source, and the fact that someone inside your castle is feeding them information. That last one costs extra.",
        affinity_change=8, blood_reward=15, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="petyr_3",
        text="I want your information network watching Morgana's contacts.",
        response="Monitoring a sorceress is expensive. But doable. I'll need access to the castle for my contacts to pass through. Agreed?",
        requires=["petyr_1"], min_affinity=20,
        affinity_change=10, suspicion_change=-15,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_agnes():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Sister Agnes",
        role=NPCRole.PRIEST,
        description="A woman in novice robes that look recently mended, with ink-stained fingers and eyes that hold more calm than fear. She smells of candle smoke and something older.",
        secret="She has been secretly feeding the poor with food taken from Morgana's stores. She knows the castle's sacred architecture — every ward, every blessed threshold — and where each one has a gap.",
        greeting="I prayed you would return. Not to this god specifically, but... I prayed.",
        likes=["protecting the innocent", "truth", "the old ways", "sanctuary", "helping others"],
        dislikes=["Morgana", "the current church", "false piety", "cruelty", "exploitation"],
        charm_resistance=3, intimidate_resistance=4,
        enthrall_resistance=6, enthrall_blood_cost=22,
        charm_success_line="I choose to trust you. That is still a choice.",
        charm_fail_line="You cannot charm someone who has already decided. I'll need more than that.",
        intimidate_success_line="I am not afraid of pain. But I'll help. For the others.",
        intimidate_fail_line="Threatening a woman of faith. Morgana would be proud.",
        enthrall_success_line="Your will and mine align, master. As they perhaps always did.",
        enthrall_fail_line="My soul is not yours to take. GO BACK TO THE DARK.",
        thought_read_line="Deep, still faith in something much older than Christianity. She knows every gap in the castle's holy defences and has been quietly widening them for years.",
    )
    npc.add_dialogue(DialogNode(
        id="agnes_1",
        text="You prayed for my return. Why?",
        response="Because what replaced you was worse. Morgana uses people. You... at least you're honest about what you are.",
        affinity_change=8, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="agnes_2",
        text="You know the castle's defences?",
        response="Every ward. Every threshold. Who placed them and who forgot to renew them. The east wing hasn't been properly consecrated in forty years.",
        affinity_change=10, suspicion_change=-5, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="agnes_3",
        text="Help me bring down Morgana's power in the castle.",
        response="I can dismantle her wards from the inside. But I'll need access to each room and some privacy. Give me time.",
        requires=["agnes_2"], min_affinity=25,
        affinity_change=12, suspicion_change=-20,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


def _make_caius():
    from npc import NPC, NPCRole, DialogNode, DialogueOption
    npc = NPC(
        name="Sir Caius the Knight",
        role=NPCRole.GUARD,
        description="A tall man in dented but well-maintained armour, carrying himself with the rigid dignity of someone who has lost everything except their principles.",
        secret="He was stripped of his rank and title not for cowardice, but for refusing to massacre a village suspected of sheltering a vampire. He does not regret it.",
        greeting="I have no lord. My oath is broken. If you have work that requires a conscience as well as a sword, I am listening.",
        likes=["honour", "protecting the innocent", "keeping oaths", "honest enemies", "duty done right"],
        dislikes=["cowardice", "unnecessary cruelty", "Morgana's methods", "betrayal", "senseless killing"],
        charm_resistance=5, intimidate_resistance=7,
        enthrall_resistance=6, enthrall_blood_cost=28,
        charm_success_line="Your cause has merit. I'll swear to it.",
        charm_fail_line="I've served charming lords before. It ended badly. Prove yourself.",
        intimidate_success_line="You won't break me with threats. But I'll work with you for now.",
        intimidate_fail_line="I faced down a mob of forty with no sword. Try harder.",
        enthrall_success_line="My sword is yours, master. I will not dishonour the blade.",
        enthrall_fail_line="MY WILL IS NOT YOURS. Draw steel and I will show you why.",
        thought_read_line="Titanium honour. He refused the order to kill the village and was court-martialled for it. He still believes the right thing is possible. It makes him extraordinarily dangerous to Morgana.",
    )
    npc.add_dialogue(DialogNode(
        id="caius_1",
        text="Why were you stripped of your rank?",
        response="I refused an order. The order was wrong. I would refuse it again. That is the whole of it.",
        affinity_change=8, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="caius_2",
        text="I need someone I can trust to guard what matters.",
        response="I don't guard for coin or fear. I guard for cause. Tell me what you're trying to build here.",
        affinity_change=6, option_type=DialogueOption.NEUTRAL,
    ))
    npc.add_dialogue(DialogNode(
        id="caius_3",
        text="I want to free this castle from Morgana's tyranny.",
        response="That I can swear to. I've watched what she does to this place and the people in it. Consider me sworn.",
        requires=["caius_1"], min_affinity=30,
        affinity_change=15, suspicion_change=-10,
        option_type=DialogueOption.NEUTRAL,
    ))
    return npc


# Public factory lookup
ENCOUNTER_NPC_FACTORIES: dict[str, callable] = {
    "celestine": _make_celestine,
    "gregori": _make_gregori,
    "esme":    _make_esme,
    "roland":  _make_roland,
    "petyr":   _make_petyr,
    "agnes":   _make_agnes,
    "caius":   _make_caius,
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENCOUNTER SELECTION
# ═══════════════════════════════════════════════════════════════════════════════

def random_encounter(
        castle_npc_names: set | None = None,
        unlocked_room_ids: set | None = None,
        completed_encounter_ids: set | None = None,
) -> Encounter:
    """
    Return a randomly chosen eligible encounter.

    - Unique encounters (NPC recruit, room unlock) filtered out once completed
    - All encounters filtered out once experienced (no repeats)
    - If all encounters completed, return a random one anyway (endless pool fallback)
    """
    if completed_encounter_ids is None:
        completed_encounter_ids = set()

    available: list[Encounter] = []
    for enc in ENCOUNTERS:
        # Skip if encounter already done
        if enc.id in completed_encounter_ids:
            continue

        # Skip if NPC already recruited
        if enc.recruitable_npc_id:
            name = ENCOUNTER_NPC_NAMES.get(enc.recruitable_npc_id, "")
            if castle_npc_names and name in castle_npc_names:
                continue   # NPC already in castle

        # Skip if room already unlocked
        if enc.unlocks_room >= 0:
            if unlocked_room_ids and enc.unlocks_room in unlocked_room_ids:
                continue   # Room already unlocked

        available.append(enc)

    return random.choice(available) if available else random.choice(ENCOUNTERS)
