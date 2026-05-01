"""
quests.py — Quest system for Vampire Castle.

Defines quest data models, all quest content, and the QuestSystem class
that tracks progress and fires completion rewards.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from game import Game


class QuestStatus(Enum):
    UNDISCOVERED = auto()   # not yet visible to player
    ACTIVE       = auto()   # player has discovered / accepted quest
    COMPLETED    = auto()   # all objectives met, rewards given
    FAILED       = auto()   # failed condition (NPC fled before objective done)


@dataclass
class QuestObjective:
    description: str                  # shown in journal, e.g. "Visit the Throne Room"
    check: Callable[["Game"], bool]   # returns True when this objective is done
    completed: bool = False


@dataclass
class Quest:
    id: str
    title: str
    description: str
    quest_type: str                            # "main" or "side"
    npc_name: str = ""                         # NPC who grants side quest (empty = auto)
    objectives: list = field(default_factory=list)   # list[QuestObjective]
    rewards: dict = field(default_factory=dict)       # {"blood": int, "xp": int, "suspicion_reduction": int}
    status: QuestStatus = QuestStatus.UNDISCOVERED
    # which quest ID to unlock when this completes (for chaining main quests)
    unlocks_quest: str = ""
    # whether the player has collected the reward from the journal
    reward_claimed: bool = False
    # room index to unlock when reward is claimed (-1 = none)
    unlocks_room: int = -1


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_npc(game: "Game", name: str):
    """Find an NPC by name from the castle roster."""
    for npc in game.castle.npcs:
        if npc.name == name:
            return npc
    return None


# ── Quest Definitions ─────────────────────────────────────────────────────────

def _build_quests() -> list[Quest]:
    from npc import NPCState

    quests: list[Quest] = []

    # ── MAIN QUESTS ────────────────────────────────────────────────────────────

    quests.append(Quest(
        id="the_awakening",
        title="The Awakening",
        description=(
            "You have slept beneath this castle for a thousand years. "
            "Now you rise. Your throne awaits — but others occupy it. "
            "Find the Throne Room and take stock of what has become of your domain."
        ),
        quest_type="main",
        objectives=[
            QuestObjective(
                description="Visit the Throne Room",
                check=lambda g: 4 in g.visited_rooms,
            ),
        ],
        rewards={"blood": 10, "xp": 20, "suspicion_reduction": 0},
        status=QuestStatus.ACTIVE,   # auto-starts
        unlocks_quest="shadows_of_allegiance",
    ))

    quests.append(Quest(
        id="shadows_of_allegiance",
        title="Shadows of Allegiance",
        description=(
            "The castle is full of souls who might serve you — if you can bend them "
            "to your will. Charm, intimidate, or enthrall them. Build your court. "
            "A ruler without loyal subjects is just a ghost."
        ),
        quest_type="main",
        objectives=[
            QuestObjective(
                description="Recruit 2 NPCs to your court",
                check=lambda g: len(g.player.court) >= 2,
            ),
        ],
        rewards={"blood": 20, "xp": 30, "suspicion_reduction": 5},
        unlocks_quest="reclaim_the_throne",
    ))

    quests.append(Quest(
        id="secrets_of_the_dark",
        title="Secrets of the Dark",
        description=(
            "Every soul in this castle hides something. Reading their thoughts "
            "will reveal the truth — and give you power over them. "
            "Peer into the minds of those who dwell here."
        ),
        quest_type="main",
        objectives=[
            QuestObjective(
                description="Read the thoughts of 3 NPCs",
                check=lambda g: len(g.player.secrets_known) >= 3,
            ),
        ],
        rewards={"blood": 0, "xp": 25, "suspicion_reduction": 0, "item_id": "obsidian_eye"},
        status=QuestStatus.ACTIVE,   # also auto-starts
        unlocks_quest="",
    ))

    quests.append(Quest(
        id="reclaim_the_throne",
        title="Reclaim the Throne",
        description=(
            "With allies at your side, you are ready to truly reclaim your domain. "
            "Return to the Throne Room with a court worthy of an ancient vampire. "
            "Let this castle remember its true master."
        ),
        quest_type="main",
        objectives=[
            QuestObjective(
                description="Have 3 or more NPCs in your court",
                check=lambda g: len(g.player.court) >= 3,
            ),
            QuestObjective(
                description="Stand in the Throne Room",
                check=lambda g: g.player.current_room == 4,
            ),
        ],
        rewards={"blood": 30, "xp": 50, "suspicion_reduction": 10, "item_id": "ancient_signet"},
        unlocks_quest="",
    ))

    # ── SIDE QUESTS ────────────────────────────────────────────────────────────

    quests.append(Quest(
        id="aldrics_debt",
        title="An Old Debt",
        description=(
            "Aldric the Guard is drowning in debt to a moneylender. "
            "His fear makes him loyal to Morgana, but his pride makes him hate it. "
            "Help him — and he may help you in return."
        ),
        quest_type="side",
        npc_name="Aldric the Guard",
        objectives=[
            QuestObjective(
                description="Learn of Aldric's trouble",
                check=lambda g: "aldric_2" in _get_npc_dialogue_seen(g, "Aldric the Guard"),
            ),
            QuestObjective(
                description="Offer to help with the debt",
                check=lambda g: "aldric_4" in _get_npc_dialogue_seen(g, "Aldric the Guard"),
            ),
        ],
        rewards={"blood": 15, "xp": 20, "suspicion_reduction": 5},
    ))

    quests.append(Quest(
        id="miras_passage",
        title="The Hidden Path",
        description=(
            "Mira the Servant carries the memory of her grandfather — your old steward. "
            "She knows this castle's secrets: hidden passages, forgotten doors. "
            "Build her trust, and she will show you what time has buried."
        ),
        quest_type="side",
        npc_name="Mira the Servant",
        objectives=[
            QuestObjective(
                description="Learn Mira's family history",
                check=lambda g: "mira_2" in _get_npc_dialogue_seen(g, "Mira the Servant"),
            ),
            QuestObjective(
                description="Reveal your connection to her grandfather",
                check=lambda g: "mira_4" in _get_npc_dialogue_seen(g, "Mira the Servant"),
            ),
        ],
        rewards={"blood": 0, "xp": 20, "suspicion_reduction": 10, "item_id": "witches_brooch"},
    ))

    quests.append(Quest(
        id="dorins_test",
        title="The Priest's Test",
        description=(
            "Father Dorin already knows what you are. He has been waiting "
            "for your return for decades. He will not be easily swayed — "
            "but perhaps you can earn his grudging respect."
        ),
        quest_type="side",
        npc_name="Father Dorin",
        objectives=[
            QuestObjective(
                description="Speak with Father Dorin",
                check=lambda g: "dorin_2" in _get_npc_dialogue_seen(g, "Father Dorin"),
            ),
            QuestObjective(
                description="Reach affinity 20 with Father Dorin",
                check=lambda g: _get_npc_affinity(g, "Father Dorin") >= 20,
            ),
        ],
        rewards={"blood": 0, "xp": 25, "suspicion_reduction": 0},
    ))

    quests.append(Quest(
        id="seraphines_scheme",
        title="Noble Schemes",
        description=(
            "Lady Seraphine has secrets of her own — ambitions she's been nursing "
            "in the dark. She despises Morgana and has been planning something. "
            "An alliance with her could reshape the power structure of the castle."
        ),
        quest_type="side",
        npc_name="Lady Seraphine",
        objectives=[
            QuestObjective(
                description="Learn Seraphine's secret about Morgana",
                check=lambda g: "seraphine_2" in _get_npc_dialogue_seen(g, "Lady Seraphine"),
            ),
            QuestObjective(
                description="Gain Seraphine's loyalty",
                check=lambda g: _get_npc_state(g, "Lady Seraphine", NPCState),
            ),
        ],
        rewards={"blood": 20, "xp": 30, "suspicion_reduction": 10},
    ))

    quests.append(Quest(
        id="viktor_redemption",
        title="The Weight of Guilt",
        description=(
            "Viktor the Torturer is a man haunted by what he has done in this castle. "
            "He performs his duty with the hollow eyes of someone who has lost their soul. "
            "Read his thoughts and uncover the truth he carries."
        ),
        quest_type="side",
        npc_name="Viktor the Torturer",
        objectives=[
            QuestObjective(
                description="Encounter Viktor in the Dungeon Wing",
                check=lambda g: 5 in g.visited_rooms,
            ),
            QuestObjective(
                description="Read Viktor's thoughts",
                check=lambda g: "Viktor the Torturer" in g.player.secrets_known,
            ),
        ],
        rewards={"blood": 20, "xp": 20, "suspicion_reduction": 0},
    ))

    quests.append(Quest(
        id="erasmus_poison",
        title="Forbidden Knowledge",
        description=(
            "Erasmus the Alchemist dwells in his laboratory with bubbling experiments "
            "and a secret vial that could spell your doom. Visit him, and discover "
            "what dangerous knowledge he protects."
        ),
        quest_type="side",
        npc_name="Erasmus the Alchemist",
        objectives=[
            QuestObjective(
                description="Visit the Alchemist's Laboratory",
                check=lambda g: 6 in g.visited_rooms,
            ),
            QuestObjective(
                description="Read Erasmus's thoughts",
                check=lambda g: "Erasmus the Alchemist" in g.player.secrets_known,
            ),
        ],
        rewards={"blood": 10, "xp": 20, "suspicion_reduction": 0},
    ))

    quests.append(Quest(
        id="lost_chamber",
        title="The Lost Chamber",
        description=(
            "Something is sealed behind the Treasury — a door that does not appear "
            "on any map. Mira's grandfather spoke of hidden passages in the old days. "
            "Learn the castle's secrets, and find a way to open what has long been shut."
        ),
        quest_type="side",
        npc_name="",   # auto-discovered on visiting Treasury (room 12)
        objectives=[
            QuestObjective(
                description="Find the sealed vault door in the Treasury",
                check=lambda g: 12 in g.visited_rooms,
            ),
            QuestObjective(
                description="Read Mira's thoughts to learn of hidden passages",
                check=lambda g: "Mira the Servant" in g.player.secrets_known,
            ),
        ],
        rewards={"blood": 15, "xp": 25, "suspicion_reduction": 0},
        unlocks_room=14,   # unlocks The Forgotten Vault when reward is claimed
    ))

    return quests


def _get_npc_dialogue_seen(game: "Game", npc_name: str) -> set:
    """Return the set of dialogue node IDs seen for an NPC, or empty set."""
    npc = _get_npc(game, npc_name)
    if npc is None:
        return set()
    return npc.dialogue_seen


def _get_npc_affinity(game: "Game", npc_name: str) -> int:
    """Return affinity for an NPC, or 0 if not found."""
    npc = _get_npc(game, npc_name)
    if npc is None:
        return 0
    return npc.affinity


def _get_npc_state(game: "Game", npc_name: str, NPCState) -> bool:
    """Return True if Seraphine is LOYAL or THRALL."""
    npc = _get_npc(game, npc_name)
    if npc is None:
        return False
    return npc.state in (NPCState.LOYAL, NPCState.THRALL)


# ── Quest System ──────────────────────────────────────────────────────────────

class QuestSystem:
    def __init__(self):
        self.quests: dict[str, Quest] = {q.id: q for q in _build_quests()}

        # NPC name → quest ID for auto-discovery on first room visit
        self._npc_quest_map = {
            "Aldric the Guard":       "aldrics_debt",
            "Mira the Servant":       "miras_passage",
            "Father Dorin":           "dorins_test",
            "Lady Seraphine":         "seraphines_scheme",
            "Viktor the Torturer":    "viktor_redemption",
            "Erasmus the Alchemist":  "erasmus_poison",
        }
        # room index → quest ID for auto-discovery when entering a room
        self._room_quest_map = {
            12: "lost_chamber",   # Treasury → discovers The Lost Chamber
        }

    # ── Discovery ─────────────────────────────────────────────────────────────

    def discover(self, quest_id: str) -> bool:
        """Move a quest from UNDISCOVERED → ACTIVE. Returns True if newly activated."""
        quest = self.quests.get(quest_id)
        if quest and quest.status == QuestStatus.UNDISCOVERED:
            quest.status = QuestStatus.ACTIVE
            return True
        return False

    # ── Check triggers ────────────────────────────────────────────────────────

    def check_triggers(self, game: "Game") -> list[str]:
        """
        Evaluate all active quests and side-quest discovery conditions.
        Returns list of quest titles that were NEWLY completed this call.
        Also handles reward application.
        """
        newly_completed: list[str] = []

        # Auto-discover side quests when the player is in the room with the NPC
        npcs_here = game.castle.get_npcs_in_room(game.player.current_room)
        for npc in npcs_here:
            quest_id = self._npc_quest_map.get(npc.name)
            if quest_id:
                self.discover(quest_id)

        # Auto-discover room-triggered quests
        room_quest = self._room_quest_map.get(game.player.current_room)
        if room_quest:
            self.discover(room_quest)

        # Evaluate each active quest
        for quest in self.quests.values():
            if quest.status != QuestStatus.ACTIVE:
                continue

            # Check individual objectives
            all_done = True
            for obj in quest.objectives:
                if not obj.completed:
                    try:
                        if obj.check(game):
                            obj.completed = True
                    except Exception:
                        pass  # guard against NPC not found etc.
                if not obj.completed:
                    all_done = False

            # If all objectives completed, finish the quest
            if all_done and quest.objectives:
                quest.status = QuestStatus.COMPLETED
                newly_completed.append(quest.title)
                # Chain: unlock next main quest immediately (no reward yet — player must claim)
                if quest.unlocks_quest:
                    self.discover(quest.unlocks_quest)

        return newly_completed

    def claim_reward(self, game: "Game", quest_id: str) -> bool:
        """
        Claim the reward for a completed quest. Returns True if reward was given.
        Rewards are only given once — calling again does nothing.
        """
        quest = self.quests.get(quest_id)
        if quest is None or quest.status != QuestStatus.COMPLETED or quest.reward_claimed:
            return False

        quest.reward_claimed = True
        rewards = quest.rewards

        blood_gain = rewards.get("blood", 0)
        if blood_gain > 0:
            game.player.blood = min(game.player.max_blood, game.player.blood + blood_gain)

        xp_gain = rewards.get("xp", 0)
        if xp_gain > 0:
            game.abilities.add_xp(xp_gain)

        susp_red = rewards.get("suspicion_reduction", 0)
        if susp_red > 0:
            game.player.lower_suspicion(susp_red)

        # Unlock a room if this quest grants access
        if quest.unlocks_room >= 0:
            target = game.castle.get_room(quest.unlocks_room)
            target.locked = False

        # Give item reward if present
        item_id = rewards.get("item_id", "")
        if item_id:
            from items import ITEMS
            item = ITEMS.get(item_id)
            if item:
                game.player.add_item(item)

        return True

    # ── Accessors ─────────────────────────────────────────────────────────────

    def all_quests(self) -> list[Quest]:
        return list(self.quests.values())

    def get_active_main(self) -> list[Quest]:
        return [q for q in self.quests.values()
                if q.quest_type == "main" and q.status == QuestStatus.ACTIVE]

    def get_completed_main(self) -> list[Quest]:
        return [q for q in self.quests.values()
                if q.quest_type == "main" and q.status == QuestStatus.COMPLETED]

    def all_side_quests(self) -> list[Quest]:
        """Return all side quests that are ACTIVE or COMPLETED (not UNDISCOVERED)."""
        return [q for q in self.quests.values()
                if q.quest_type == "side" and q.status != QuestStatus.UNDISCOVERED]

    def active_count(self) -> int:
        return sum(1 for q in self.quests.values() if q.status == QuestStatus.ACTIVE)

    def unclaimed_count(self) -> int:
        return sum(1 for q in self.quests.values()
                   if q.status == QuestStatus.COMPLETED and not q.reward_claimed)

    def visible_quests(self) -> list:
        """Ordered list of all quests shown in the journal (main then side, non-undiscovered)."""
        main = [q for q in self.quests.values()
                if q.quest_type == "main" and q.status != QuestStatus.UNDISCOVERED]
        side = [q for q in self.quests.values()
                if q.quest_type == "side" and q.status != QuestStatus.UNDISCOVERED]
        return main + side
