"""
npc.py — NPC data model.

Each NPC has:
  - Personality traits that determine resistance to each power
  - A hidden 'secret' you learn by reading their thoughts
  - A loyalty/fear/suspicion state that changes based on interactions
  - A role that unlocks gameplay benefits if they join your court
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class DialogueOption(Enum):
    """Tags for dialogue to categorize choices."""
    NEUTRAL = auto()
    FLIRTY = auto()
    THREATENING = auto()
    HELP_SEEKING = auto()
    REVEALING_HINT = auto()  # hints at vampire nature but disguised


@dataclass
class DialogNode:
    """A single dialogue choice with prerequisites and rewards."""
    id: str                          # unique identifier
    text: str                        # what player says
    response: str                    # what NPC says
    requires: list[str] = field(default_factory=list)  # IDs that must be seen first
    min_affinity: int = 0            # 0-100 affinity threshold
    affinity_change: int = 0         # how much affinity changes after
    blood_reward: int = 0            # blood given (positive) or cost (negative)
    suspicion_change: int = 0        # castle suspicion change
    option_type: DialogueOption = DialogueOption.NEUTRAL
    shows_vampire_hint: bool = False # if true, NPC becomes SUSPICIOUS if this leads to guess

    def is_available(self, affinity: int, dialogue_seen: set[str]) -> bool:
        """Check if this option can be selected."""
        if affinity < self.min_affinity:
            return False
        for req_id in self.requires:
            if req_id not in dialogue_seen:
                return False
        return True

    def lock_reason(self, affinity: int, dialogue_seen: set[str]) -> str:
        """Return why this option is locked."""
        if affinity < self.min_affinity:
            return f"Need closer relationship ({affinity}/{self.min_affinity})"
        for req_id in self.requires:
            if req_id not in dialogue_seen:
                return f"Requires earlier conversation"
        return ""


class NPCState(Enum):
    NEUTRAL    = auto()   # hasn't met you yet
    SUSPICIOUS = auto()   # wary, heard rumours
    LOYAL      = auto()   # charmed — willingly serves you
    THRALL     = auto()   # enthralled — compelled to obey
    TERRIFIED  = auto()   # broken by intimidation — obeys but unstable
    HOSTILE    = auto()   # will attack or raise alarm
    FLED       = auto()   # ran away, warned others


class NPCRole(Enum):
    GUARD    = "guard"      # patrols nearby rooms, warns you of intruders
    SERVANT  = "servant"    # unlocks rest/feed actions in their room
    SPY      = "spy"        # reveals hidden NPCs in adjacent rooms
    NOBLE    = "noble"      # grants access to locked noble quarters
    HUNTER   = "hunter"     # dangerous — if turned, becomes powerful ally
    PRIEST   = "priest"     # high resistance; turning grants holy weakness info


@dataclass
class NPC:
    name: str
    role: NPCRole
    description: str          # what you see when you enter the room
    secret: str               # revealed only after reading thoughts
    greeting: str             # what they say when you first speak

    # Preferences: what increases/decreases affinity
    likes: list[str] = field(default_factory=list)         # things they approve of
    dislikes: list[str] = field(default_factory=list)      # things they disapprove of

    # Resistance stats (0–10). Higher = harder to affect with that power.
    charm_resistance: int = 3
    intimidate_resistance: int = 3
    enthrall_resistance: int = 5

    # Blood cost multiplier for enthrall (some NPCs cost more)
    enthrall_blood_cost: int = 20

    # If True, ALL vampire powers fail immediately with a special message
    immune_to_powers: bool = False

    # Current state
    state: NPCState = NPCState.NEUTRAL
    thoughts_read: bool = False
    suspicion: int = 0        # 0–100; high suspicion raises castle-wide alert

    # Relationship/Affinity system (0-100)
    affinity: int = 0
    dialogue_seen: set[str] = field(default_factory=set)  # IDs of dialogue nodes seen
    suspects_vampire: bool = False  # does this NPC suspect the player is a vampire?

    # Lines of dialogue per power outcome
    charm_success_line: str     = "I... I feel drawn to you, my lord. I am yours."
    charm_fail_line: str        = "Something feels wrong. Stay away from me!"
    intimidate_success_line: str = "P-please, I'll do whatever you ask. Just don't hurt me."
    intimidate_fail_line: str   = "HELP! There's something in the castle!"
    enthrall_success_line: str  = "Master... I exist only to serve."
    enthrall_fail_line: str     = "GET OUT OF MY HEAD! Guards! GUARDS!"
    thought_read_line: str      = ""   # shown after reading; reveals secret

    # Dialogue tree: dict of dialogue node IDs -> DialogNode
    dialogue_tree: dict[str, DialogNode] = field(default_factory=dict)

    # Legacy support: simple dialogue options (deprecated, use dialogue_tree instead)
    dialogue_options: list = field(default_factory=list)

    def is_controllable(self) -> bool:
        return self.state in (NPCState.LOYAL, NPCState.THRALL, NPCState.TERRIFIED)

    def is_hostile(self) -> bool:
        return self.state in (NPCState.HOSTILE, NPCState.FLED)

    def status_label(self) -> str:
        labels = {
            NPCState.NEUTRAL:    "Neutral",
            NPCState.SUSPICIOUS: "Suspicious",
            NPCState.LOYAL:      "Loyal",
            NPCState.THRALL:     "Thrall",
            NPCState.TERRIFIED:  "Terrified",
            NPCState.HOSTILE:    "Hostile",
            NPCState.FLED:       "Fled",
        }
        return labels[self.state]

    def status_color(self) -> tuple:
        """Returns an RGB colour for the status badge."""
        colors = {
            NPCState.NEUTRAL:    (160, 160, 160),
            NPCState.SUSPICIOUS: (220, 180, 60),
            NPCState.LOYAL:      (100, 180, 255),
            NPCState.THRALL:     (160, 80, 220),
            NPCState.TERRIFIED:  (230, 130, 50),
            NPCState.HOSTILE:    (220, 60, 60),
            NPCState.FLED:       (120, 80, 80),
        }
        return colors[self.state]

    def get_available_dialogue(self) -> list[DialogNode]:
        """Return list of dialogue nodes that are currently available."""
        available = []
        for node in self.dialogue_tree.values():
            if node.is_available(self.affinity, self.dialogue_seen):
                available.append(node)
        return available

    def add_dialogue(self, node: DialogNode) -> None:
        """Register a dialogue node for this NPC."""
        self.dialogue_tree[node.id] = node

    def check_preference(self, action: str) -> tuple[bool, int]:
        """Check if NPC likes/dislikes an action. Returns (matches_preference, affinity_change)."""
        action_lower = action.lower()

        # Check if any liked words appear in the action text
        for like in self.likes:
            if like.lower() in action_lower:
                return (True, 8)   # Strongly liked: +8 affinity

        # Check if any disliked words appear in the action text
        for dislike in self.dislikes:
            if dislike.lower() in action_lower:
                return (False, -12) # Strongly disliked: -12 affinity

        # Otherwise neutral
        return (True, 2)   # Neutral: small positive (they appreciate conversation)


# ── NPC Factory Functions ────────────────────────────────────────────────────

def _create_aldric() -> NPC:
    """Create Aldric with dialogue tree that leads to debt relief alliance."""
    aldric = NPC(
        name="Aldric the Guard",
        role=NPCRole.GUARD,
        description="A grizzled soldier in rusted armour. He grips his spear tightly, eyes darting.",
        secret="He is deeply in debt to a moneylender. His family will be taken if he doesn't pay.",
        greeting="Halt! The castle is under the authority of Count Morgana now. State your business.",
        likes=["honor", "helping with his debt", "the old ways", "protection", "fairness"],
        dislikes=["Morgana", "slavery", "exploitation", "cruelty to innocents", "dishonesty"],
        charm_resistance=4,
        intimidate_resistance=2,
        enthrall_resistance=4,
        enthrall_blood_cost=15,
        charm_success_line="I... don't know why, but I trust you, my lord. The old ways feel right.",
        charm_fail_line="What are you doing to my head?! Back off before I run you through!",
        intimidate_success_line="By the saints... what ARE you? I'll do whatever you say, just stay back!",
        intimidate_fail_line="AN INTRUDER! TO ARMS! INTRUDER IN THE EAST WING!",
        enthrall_success_line="Master... I am your sword and your shadow.",
        enthrall_fail_line="SORCERY! It burns — GUARDS, THE DEVIL IS HERE!",
        thought_read_line="His mind is a mess of fear and debt. The name 'Morgana' brings a cold fury beneath the fear.",
    )

    # Build dialogue tree
    aldric.add_dialogue(DialogNode(
        id="aldric_1",
        text="Why do you serve Count Morgana?",
        response="I serve whoever pays. That's soldiering. Don't make it complicated.",
        affinity_change=2,
        option_type=DialogueOption.NEUTRAL,
    ))

    aldric.add_dialogue(DialogNode(
        id="aldric_2",
        text="You look troubled. What weighs on you?",
        response="Nothing that concerns you. ...Debts. The kind that follow a man home.",
        affinity_change=5,
        option_type=DialogueOption.HELP_SEEKING,
    ))

    aldric.add_dialogue(DialogNode(
        id="aldric_3",
        text="Do you remember the castle's old lord?",
        response="Before my time. They say he was worse than Morgana. I'm starting to doubt that.",
        affinity_change=3,
        option_type=DialogueOption.NEUTRAL,
    ))

    # Debt relief - requires showing you care (aldric_2) and building rapport
    aldric.add_dialogue(DialogNode(
        id="aldric_4",
        text="I could help you with those debts.",
        response="Help me? With what coin? Unless you're offering something dark in trade... No. I won't ask.",
        requires=["aldric_2"],
        min_affinity=15,
        affinity_change=10,
        blood_reward=20,  # costs player blood to help
        suspicion_change=-5,  # helping is less suspicious than using powers
        option_type=DialogueOption.HELP_SEEKING,
    ))

    # Advanced offer - can only be made after debt help
    aldric.add_dialogue(DialogNode(
        id="aldric_5",
        text="I'm not what you think I am. But I can protect your family better than any moneylender.",
        response="...Are you saying what I think? No. No, I don't want to know. But if you can keep them safe—that's all that matters.",
        requires=["aldric_4"],
        min_affinity=30,
        affinity_change=15,
        shows_vampire_hint=True,  # This reveals the secret
        option_type=DialogueOption.REVEALING_HINT,
    ))

    # Trust fallback option
    aldric.add_dialogue(DialogNode(
        id="aldric_6",
        text="Stand aside. I will not ask twice.",
        response="Ha. That line works on recruits. Try again.",
        affinity_change=-10,
        option_type=DialogueOption.THREATENING,
    ))

    return aldric


def _create_mira() -> NPC:
    """Create Mira with dialogue tree focused on kinship and castle secrets."""
    mira = NPC(
        name="Mira the Servant",
        role=NPCRole.SERVANT,
        description="A young woman dusting the old portraits. She freezes when she sees you.",
        secret="She is the granddaughter of your old steward. She knows the castle's hidden passages.",
        greeting="Oh! I'm sorry, I didn't hear you come in. Are you one of Count Morgana's guests?",
        likes=["family", "the old ways", "kindness", "the past", "respect for tradition"],
        dislikes=["Morgana", "cruelty", "dismissing the past", "harm to innocents", "dishonoring her grandfather"],
        charm_resistance=1,
        intimidate_resistance=5,
        enthrall_resistance=3,
        enthrall_blood_cost=10,
        charm_success_line="You remind me of the paintings in the old gallery. I feel like I've known you forever.",
        charm_fail_line="Why are you looking at me like that? I'm going to fetch the housekeeper!",
        intimidate_success_line="Please... I have a little brother. I'll do anything, just please don't hurt us.",
        intimidate_fail_line="SOMEONE HELP ME! PLEASE!",
        enthrall_success_line="I remember the hidden doors, master. I will show you everything.",
        enthrall_fail_line="What are you — get away — HELLLP!",
        thought_read_line="Flashes of a childhood here. She misses her grandfather. She knows a door behind the fireplace.",
    )

    mira.add_dialogue(DialogNode(
        id="mira_1",
        text="How long have you worked here?",
        response="Three years. Since my grandfather passed. He served here before me — and his father before him.",
        affinity_change=3,
        option_type=DialogueOption.NEUTRAL,
    ))

    mira.add_dialogue(DialogNode(
        id="mira_2",
        text="What did your grandfather say of the old lord?",
        response="That he was cold but fair. That the castle had rules. It felt like a real home, once.",
        affinity_change=8,
        option_type=DialogueOption.NEUTRAL,
    ))

    mira.add_dialogue(DialogNode(
        id="mira_3",
        text="You remind me of someone I once knew.",
        response="Really? Who? ...I'm sorry, that was forward of me.",
        affinity_change=12,
        option_type=DialogueOption.FLIRTY,
    ))

    # Passage unlock - requires showing you knew the old lord
    mira.add_dialogue(DialogNode(
        id="mira_4",
        text="I knew your grandfather. He was... loyal and wise.",
        response="You... knew grandfather? How is that possible? You look no older than I am... Unless...",
        requires=["mira_2"],
        min_affinity=20,
        affinity_change=20,
        suspicion_change=-10,
        shows_vampire_hint=True,
        option_type=DialogueOption.REVEALING_HINT,
    ))

    mira.add_dialogue(DialogNode(
        id="mira_5",
        text="You seem frightened. Are you safe here?",
        response="I'm fine. Count Morgana pays on time and doesn't ask questions. That's enough.",
        affinity_change=2,
        option_type=DialogueOption.HELP_SEEKING,
    ))

    return mira


def _create_father_dorin() -> NPC:
    """Create Father Dorin with dialogue about faith and ancient knowledge."""
    dorin = NPC(
        name="Father Dorin",
        role=NPCRole.PRIEST,
        description="An old priest clutching a silver cross, lips moving in silent prayer.",
        secret="He knows you exist. He has been waiting. He has a vial of your blood from 1000 years ago.",
        greeting="I know what you are, creature. This castle will not fall to darkness again.",
        likes=["protecting innocents", "redemption", "faith", "sacrifice", "truth"],
        dislikes=["corruption", "darkness", "harm to the faithful", "lies about your nature", "innocent suffering"],
        charm_resistance=9,
        intimidate_resistance=6,
        enthrall_resistance=10,
        enthrall_blood_cost=40,
        charm_success_line="God forgive me... your voice is like music. I... I don't want to resist.",
        charm_fail_line="Your honeyed words have no purchase on a faithful soul. Begone!",
        intimidate_success_line="I am old. My life matters less than others. Do what you will — but leave the innocent.",
        intimidate_fail_line="You will not break me! The light protects this house! SERVANTS OF GOD, TO ME!",
        enthrall_success_line="...The prayers feel hollow now. What have you done to me, master?",
        enthrall_fail_line="YOUR KIND HAS NO DOMINION HERE — BACK TO THE ABYSS!",
        thought_read_line="He holds something tightly. A memory — a ritual, a locked reliquary. Your name, spoken in terror for centuries.",
    )

    # Father Dorin already knows you're a vampire - no point hiding it
    dorin.suspects_vampire = True

    dorin.add_dialogue(DialogNode(
        id="dorin_1",
        text="I mean you no harm, Father.",
        response="The road to damnation is paved with exactly such assurances. I know what you are.",
        affinity_change=-5,
        suspicion_change=10,
    ))

    dorin.add_dialogue(DialogNode(
        id="dorin_2",
        text="What do you know about my return?",
        response="I know you slept beneath this castle for a thousand years. I have been preparing for this day.",
        affinity_change=5,
        option_type=DialogueOption.NEUTRAL,
    ))

    dorin.add_dialogue(DialogNode(
        id="dorin_3",
        text="Has your faith truly protected you?",
        response="It has kept me standing in your presence, hasn't it? That is protection enough.",
        affinity_change=3,
        option_type=DialogueOption.NEUTRAL,
    ))

    # Reliquary offer
    dorin.add_dialogue(DialogNode(
        id="dorin_4",
        text="What is inside the reliquary?",
        response="Something that belongs to the old world. Something that should never have survived. Neither should you.",
        requires=["dorin_2"],
        min_affinity=-20,  # Only available if player hasn't built rapport
        affinity_change=-10,
        option_type=DialogueOption.NEUTRAL,
    ))

    dorin.add_dialogue(DialogNode(
        id="dorin_5",
        text="We do not have to be enemies.",
        response="A wolf and a lamb cannot be friends. One of us must yield, creature.",
        affinity_change=2,
        option_type=DialogueOption.NEUTRAL,
    ))

    return dorin


def _create_lady_seraphine() -> NPC:
    """Create Lady Seraphine with dialogue leading to alliance against her father."""
    seraphine = NPC(
        name="Lady Seraphine",
        role=NPCRole.NOBLE,
        description="A striking noblewoman in black, reading by candlelight. She doesn't look up.",
        secret="She is Morgana's rival — and she wants power. She has been scheming to overthrow her for months.",
        greeting="Another one of the court? Or something more interesting, I wonder.",
        likes=["power", "intellect", "ambition", "independence", "turning the tables"],
        dislikes=["weakness", "servitude", "predictable people", "forced obedience", "being controlled"],
        charm_resistance=5,
        intimidate_resistance=7,
        enthrall_resistance=6,
        enthrall_blood_cost=25,
        charm_success_line="Oh. Oh, you are extraordinary. Morgana always kept the best things locked away.",
        charm_fail_line="Flattery from a shadow? I think not. Guards are one scream away.",
        intimidate_success_line="You're the first thing in this castle that's actually frightened me. Impressive. Fine.",
        intimidate_fail_line="You think I'm afraid of monsters? I LIVE with one. HELP! HELP ME!",
        enthrall_success_line="I hated her. Now I only think of you. Is that what you wanted, master?",
        enthrall_fail_line="GET OUT OF MY MIND — Morgana! MORGANA! SOMETHING IS IN THE CASTLE!",
        thought_read_line="She despises Morgana with a burning clarity. Poison. A silver key around her neck. Plans. Ambition.",
    )

    seraphine.add_dialogue(DialogNode(
        id="seraphine_1",
        text="What are you reading?",
        response="The poetry of a dead man. Far better company than the living men in this castle.",
        affinity_change=4,
        option_type=DialogueOption.NEUTRAL,
    ))

    seraphine.add_dialogue(DialogNode(
        id="seraphine_2",
        text="Tell me about your father.",
        response="Which version? The public one — powerful, gracious — or the truth about what he is?",
        affinity_change=8,
        option_type=DialogueOption.HELP_SEEKING,
    ))

    seraphine.add_dialogue(DialogNode(
        id="seraphine_3",
        text="I know about the poison.",
        response="Then you know I am thorough. Patient. And I have had three failed attempts already.",
        requires=["seraphine_2"],
        min_affinity=15,
        affinity_change=15,
        option_type=DialogueOption.NEUTRAL,
    ))

    seraphine.add_dialogue(DialogNode(
        id="seraphine_4",
        text="You could use someone like me.",
        response="The thought had occurred to me. Whether I can trust a creature that drinks blood — that is the question.",
        requires=["seraphine_3"],
        min_affinity=25,
        affinity_change=20,
        suspicion_change=-15,
        blood_reward=10,
        shows_vampire_hint=True,
        option_type=DialogueOption.REVEALING_HINT,
    ))

    seraphine.add_dialogue(DialogNode(
        id="seraphine_5",
        text="What does Morgana keep in the east tower?",
        response="Papers. Correspondence. Evidence of things he'd rather not see in daylight. I haven't reached it.",
        requires=["seraphine_2"],
        min_affinity=10,
        affinity_change=5,
        option_type=DialogueOption.NEUTRAL,
    ))

    seraphine.add_dialogue(DialogNode(
        id="seraphine_marry",
        text="I want to free this castle from tyranny. Stand with me. Marry me.",
        response="Free it? Or rule it together? ...Yes. Yes, I will stand with you. Against Morgana, against everything. Marry me, and together we will burn the chains.",
        requires=["seraphine_2"],
        min_affinity=50,
        affinity_change=20,
        blood_reward=10,
        suspicion_change=-10,
        option_type=DialogueOption.FLIRTY,
    ))

    return seraphine


# ── Predefined NPCs ──────────────────────────────────────────────────────────

def make_castle_npcs() -> list[NPC]:
    return [
        _create_aldric(),
        _create_mira(),
        _create_father_dorin(),
        _create_lady_seraphine(),
    ]
