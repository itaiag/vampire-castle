
"""
castle.py — Castle map with expanded rooms (19 total) and more NPCs.
"""

from dataclasses import dataclass, field
from typing import Optional
from npc import NPC, NPCRole, NPCState, make_castle_npcs


@dataclass
class Room:
    name: str
    description: str
    atmosphere: str
    exits: dict
    npc_indices: list
    feed_available: bool = False
    secret_passage: Optional[int] = None
    candle_positions: list = field(default_factory=list)
    room_number: int = 0
    interactive_elements: list = field(default_factory=list)  # list of dicts: {"name": "...", "description": "..."}
    locked: bool = False          # if True, player cannot enter until unlocked by a quest
    outside_access: bool = False  # if True, player can venture outside from this room


@dataclass
class Castle:
    rooms: list
    npcs: list

    def get_room(self, index: int):
        return self.rooms[index]

    def get_npcs_in_room(self, room_index: int) -> list:
        room = self.rooms[room_index]
        return [self.npcs[i] for i in room.npc_indices]

    def add_npc_to_room(self, npc, room_index: int) -> None:
        """Append a newly recruited NPC to the castle and place them in a room."""
        npc_idx = len(self.npcs)
        self.npcs.append(npc)
        self.rooms[room_index].npc_indices.append(npc_idx)

    def unlock_room(self, room_index: int) -> None:
        """Remove the lock from a locked room."""
        self.rooms[room_index].locked = False


def make_extra_npcs() -> list:
    npcs = [
        NPC(
            name="Viktor the Torturer",
            role=NPCRole.GUARD,
            description="A mountain of a man in a blood-stained leather apron. He sharpens a blade without looking up.",
            secret="He secretly weeps for every person he has harmed. He wants to escape Morgana as badly as anyone.",
            greeting="This wing is off-limits. Turn back or I'll make you regret it.",
            likes=["mercy", "freedom", "escape", "ending suffering", "redemption"],
            dislikes=["cruelty", "torture", "slavery", "following Morgana blindly", "more killing"],
            charm_resistance=6,
            intimidate_resistance=3,
            enthrall_resistance=5,
            enthrall_blood_cost=20,
            charm_success_line="You... you're different from Morgana. There's something ancient about you. I'll listen.",
            charm_fail_line="Save your honeyed words for someone weaker. Go.",
            intimidate_success_line="Fine. FINE. I was done with this work anyway. What do you need?",
            intimidate_fail_line="YOU THINK YOU SCARE ME? I'VE SEEN WORSE! MORGANA! MORGANA, COME HERE!",
            enthrall_success_line="The guilt is... gone. Only your will remains, master.",
            enthrall_fail_line="MY MIND IS MY OWN! INTRUDER! EVERYONE TO THE DUNGEON WING!",
            thought_read_line="Guilt so thick it's almost a physical presence. He wants out. He's kept a key to the dungeon cells.",
            dialogue_options=[
                ("Put down the blade. I am not your enemy.",     "Everyone who walks in here says that. They're usually wrong."),
                ("You don't seem like a man who enjoys this.",   "...What makes you say that? This is just work. It pays. That's all."),
                ("What does Morgana make you do in this wing?",    "Questions like that get people hurt. I'd stop asking if I were you."),
                ("I sense you want to stop. The guilt shows.",  "Shut up. You don't know me. You don't know anything about me."),
                ("Join me. Leave Morgana and this place behind.",   "Even if I believed you... a man like me doesn't get second chances."),
            ],
        ),
        NPC(
            name="Erasmus the Alchemist",
            role=NPCRole.SPY,
            description="A wiry old man surrounded by bubbling vials and crumbling manuscripts. He peers at you with bright, curious eyes.",
            secret="He has been secretly synthesising a poison that would kill a vampire. He is not sure if it works.",
            greeting="Extraordinary! The bone structure, the pallor, the eyes... you're not human, are you? Fascinating!",
            likes=["knowledge", "ancient secrets", "intellectual discussion", "honesty", "research"],
            dislikes=["ignorance", "book burning", "censorship", "superstition", "lies"],
            charm_resistance=2,
            intimidate_resistance=6,
            enthrall_resistance=4,
            enthrall_blood_cost=18,
            charm_success_line="A vampire! A REAL vampire! Do you know how long I've studied your kind? I'll help you — just let me take notes!",
            charm_fail_line="I may be old but I'm not stupid. Back away slowly and nobody gets poisoned.",
            intimidate_success_line="Alright, alright! No need for theatrics. I have what you need. Just don't damage the equipment.",
            intimidate_fail_line="POISON GAS IN THREE SECONDS IF YOU DON'T LEAVE! I'M NOT BLUFFING!",
            enthrall_success_line="My research... was for nothing. You were always going to win, weren't you, master?",
            enthrall_fail_line="Interesting! Your enthrall has a psychic frequency I can actually MEASURE — oh wait, HELP! HELP!",
            thought_read_line="A brilliant, chaotic mind. Formulas, theories, sketches of your kind. And a vial, locked in a drawer, labelled 'V-poison — DO NOT TEST ON SELF'.",
            dialogue_options=[
                ("You don't seem afraid of me at all.",           "Afraid? I'm DELIGHTED! Do you know how rare a living vampire specimen is? Hold still!"),
                ("What are you working on over there?",          "A compound of silver, garlic extract, and something unnameable. Nothing relevant to you. Ha."),
                ("You know what I am, yet you stay?",            "Knowledge is worth dying for. How OLD are you exactly? The castle records go back eight centuries."),
                ("What do your records say about my past?",      "Your name appears in the foundation documents. Fascinating legal implications, actually — you may still own this place."),
                ("That vial you're hiding — hand it over.",      "I don't know what you're — fine. FINE! I'm keeping my notes. The science must survive even if I don't."),
            ],
        ),
        NPC(
            name="Isolde the Vampire Hunter",
            role=NPCRole.HUNTER,
            description="A lean woman in travelling leathers, silver crossbow slung across her back. She doesn't flinch when she sees you.",
            secret="She has been hunting you specifically for twenty years. She is exhausted. She wants it to be over.",
            greeting="I've been waiting for you. I tracked you from the eastern provinces. I know what you are.",
            likes=["peace", "ending the hunt", "protecting innocents", "truth", "rest"],
            dislikes=["lies", "innocents harmed", "endless hunting", "senseless killing", "monsters who prey"],
            charm_resistance=8,
            intimidate_resistance=7,
            enthrall_resistance=9,
            enthrall_blood_cost=45,
            charm_success_line="I... I don't understand. I should be driving a stake through your heart. Why can't I move?",
            charm_fail_line="Silver crossbow, blessed bolts, and twenty years of training. Try that again and I'll end you.",
            intimidate_success_line="I'm not afraid to die. But there are people who need me. Stand down and I'll consider a truce.",
            intimidate_fail_line="EXACTLY what I expected from a monster! *loads crossbow* WHO ELSE IS IN THIS CASTLE?",
            enthrall_success_line="Twenty years. All that training. And here I am, kneeling. ...I hate you.",
            enthrall_fail_line="YOUR KIND CANNOT HOLD ME! *fires crossbow* EVERYONE RUN, THE VAMPIRE IS FREE!",
            thought_read_line="Iron discipline and bone-deep exhaustion. She has a journal — every rumour, every clue, twenty years of hunting you.",
            dialogue_options=[
                ("Twenty years. That is a long time to hunt.",   "You have no idea. I've crossed three countries, buried two partners, and given up everything for this."),
                ("Why do you want me dead?",                     "You're a predator. I protect people. It's not complicated."),
                ("This does not need to end in violence.",       "Every vampire I've faced has said that. Right before the killing started. Why are you different?"),
                ("What would it take for you to walk away?",     "...I don't know anymore. Twenty years ago I'd have said 'your head'. Now I'm less certain."),
                ("Why hunt me specifically for so long?",        "The village of Karev. 1003 AD. Someone has to answer for what happened there. Was that not you?"),
            ],
        ),
        NPC(
            name="Morgana the Sorceress",
            role=NPCRole.NOBLE,
            description="A striking woman in crimson silk and dark jewels, her eyes glowing with unnatural power. She sits upon an obsidian throne, regarding you with cold amusement.",
            secret="She is a powerful sorceress who seized your castle while you slept. She wants to be like you — immortal and unchained.",
            greeting="So. You finally wake. I have been waiting for the legendary vampire to return. How... disappointing.",
            likes=["power", "immortality", "respect", "ambitious minds", "magical discussion"],
            dislikes=["weakness", "servitude", "the old ways", "mercy", "sharing power"],
            charm_resistance=7,
            intimidate_resistance=8,
            enthrall_resistance=8,
            enthrall_blood_cost=50,
            charm_success_line="Your power is intoxicating. Perhaps we are not so different after all...",
            charm_fail_line="Do not waste your ancient tricks on me, creature. I have magic you cannot comprehend.",
            intimidate_success_line="Impressive. But this castle is MINE now. You will have to take it from me.",
            intimidate_fail_line="GUARDS! KILL THE INTRUDER! This is MY castle now!",
            enthrall_success_line="No... what have you done? I can feel your will crushing mine...",
            enthrall_fail_line="You dare?! My magic will BURN YOU FROM WITHIN! SOLDIERS, TO ME!",
            thought_read_line="A brilliant, ambitious mind. She seized the throne with dark magic. But underneath: fear. Fear that you'll return. And desire — she wants immortality.",
            dialogue_options=[
                ("This is my castle. You are the usurper.",    "WAS your castle. You've been gone a THOUSAND years. Possession is nine-tenths of the law, vampire."),
                ("Why did you take my throne?",                "Because it was empty. Because I am stronger than the fools who ruled before. Because I WANTED it."),
                ("You will kneel to me.",                       "Never. I'd sooner burn this castle to ash than serve an undead relic."),
                ("We are not so different. Together we could be unstoppable.",  "...Immortal. Unstoppable. Ruling side by side. You intrigue me, vampire. Perhaps we could come to an... arrangement."),
                ("Marry me. Rule beside me as my eternal consort.",  "Marry YOU? *laughs* Bold. I like that. Very well. Let us remake this castle together."),
                ("Your reign ends now. I challenge you to final combat.",  "Finally! The old vampire shows his teeth. Come then. Let us see who is truly the stronger one. This ends tonight."),
            ],
        ),
        NPC(
            name="Clara the Maid",
            role=NPCRole.SERVANT,
            description="A tired-looking woman in a faded servant's uniform, carrying fresh linens. She avoids eye contact nervously.",
            secret="She was born in the castle during your absence. She has never known freedom, only servitude to Morgana.",
            greeting="Oh! Forgive me, I... I didn't hear you. Are you... are you a guest of the Sorceress?",
            likes=["kindness", "freedom", "hope", "gentleness", "being protected"],
            dislikes=["cruelty", "slavery", "Morgana", "fear", "servitude"],
            charm_resistance=2,
            intimidate_resistance=4,
            enthrall_resistance=3,
            enthrall_blood_cost=12,
            charm_success_line="You... you seem kind. That's rare here. I think I can trust you.",
            charm_fail_line="Please don't hurt me! I'm just a servant, I don't know anything!",
            intimidate_success_line="Yes! Yes, I'll help you! Anything! Just please don't hurt the others!",
            intimidate_fail_line="HELP! GUARDS! There's a monster in the halls!",
            enthrall_success_line="Your will... it feels like freedom. I'll do anything you ask, master.",
            enthrall_fail_line="What's happening to me? HELP ME! SOMEONE HELP!",
            thought_read_line="Simple, kind thoughts. Fear and exhaustion. She dreams of leaving the castle. She knows where Morgana keeps her spell book.",
            dialogue_options=[
                ("How long have you lived in this castle?", "All my life. I was born here, during... well, I don't really know when. Morgana doesn't talk about it."),
                ("Do you know what happened to the old ruler?", "There was someone before... very long ago. The old stories say they were powerful. But Morgana erased all that history."),
                ("Would you help me against Morgana?", "I... I want to. But I'm so afraid. She has power over everything, everyone. Can you really protect me?"),
                ("What does Morgana keep locked away?", "Her spellbooks... in the Inner Sanctum. And there's something else. A crystal that glows at night. She keeps it very close."),
                ("You deserve freedom, Clara.", "Sometimes I dream about leaving. Just walking out those doors and never coming back. Do you think that's possible for me?"),
            ],
        ),
        NPC(
            name="Theron the Guard Captain",
            role=NPCRole.GUARD,
            description="A stern man in polished armor, commanding a squad of soldiers. His eyes scan the room constantly, ever watchful.",
            secret="He serves Morgana out of duty, not loyalty. He remembers the old castle and wonders if it was truly better then.",
            greeting="Halt! State your business. This wing is restricted to authorized personnel only.",
            likes=["duty done right", "protecting people", "honor", "respect", "ending Morgana's reign"],
            dislikes=["cowardice", "Morgana's tyranny", "betrayal", "senseless death", "evil masters"],
            charm_resistance=5,
            intimidate_resistance=4,
            enthrall_resistance=5,
            enthrall_blood_cost=22,
            charm_success_line="You have... presence. Perhaps we could come to an understanding.",
            charm_fail_line="Your tricks won't work on me, stranger. Stand down or face my sword.",
            intimidate_success_line="Fine. I've grown tired of serving Morgana anyway. What do you need?",
            intimidate_fail_line="INTRUDER ALERT! All guards to the east corridor! NOW!",
            enthrall_success_line="Your command is my will. I am yours to command, master.",
            enthrall_fail_line="You will not control me! GUARDS, DEFEND MORGANA!",
            thought_read_line="Duty-bound, professional, but beneath: doubt. He questions Morgana's rule. He remembers your name from old stories.",
            dialogue_options=[
                ("How many guards serve under you?", "Twenty men. Loyal soldiers, or at least... they obey orders. Morgana keeps us well-supplied and paid. That's enough."),
                ("Do you remember the old castle?", "I've heard stories from the veterans. They say the old lord was just as ruthless, but more... present. Morgana rules through fear and magic."),
                ("Would your men follow you if you rebelled?", "Some would. But Morgana has made examples. There are ways to crush rebellion that don't involve swords. That's what frightens me most."),
                ("The soldiers seem well-trained.", "They are. I take pride in my work, even if it's for someone I... don't entirely trust. A good soldier follows orders. But even soldiers can wonder about the orders."),
                ("I could use tactical support against Morgana.", "If you can convince me she's not the stronger power here, I'll consider it. But I need more than words. I need to see victory as possible."),
            ],
        ),
        NPC(
            name="Lydia the Librarian",
            role=NPCRole.SPY,
            description="An elderly woman surrounded by towering shelves of ancient books, carefully cataloging forbidden knowledge. She looks up from her work with interest.",
            secret="She is preserving the castle's true history, hidden from Morgana. She knows every secret in these walls.",
            greeting="Ah, a visitor to the library. How delightful. Few come here anymore. Most are afraid of what they might learn.",
            likes=["history", "truth", "preservation of knowledge", "honoring the past", "understanding"],
            dislikes=["ignorance", "book burning", "censorship", "forgetting history", "lies about the past"],
            charm_resistance=3,
            intimidate_resistance=6,
            enthrall_resistance=4,
            enthrall_blood_cost=16,
            charm_success_line="You have an old soul. I can see it. Let me help you understand what was lost.",
            charm_fail_line="I think you should leave. Some books are best left unread by the likes of you.",
            intimidate_success_line="Yes, yes, take what you need. Knowledge should be free, not locked away.",
            intimidate_fail_line="You wouldn't dare! This library is sacred! GUARDS!",
            enthrall_success_line="Your will... is like reading the true ending of a story. I am bound to you.",
            enthrall_fail_line="Impossible! This library is warded against dark magic! HELP!",
            thought_read_line="A keeper of secrets, a guardian of history. She has books that detail your reign, your power, your weaknesses. She has been waiting for your return.",
            dialogue_options=[
                ("What secrets does this library hold?", "Centuries of history. Records of every lord, every war, every dark deed. Morgana tried to burn some. But paper hides in stone, and memory lives in ink."),
                ("Do you have books about the old lord?", "Every ledger, every decree, every private letter. He was fierce, brilliant, and terribly lonely. I think you should read his journals."),
                ("Why has Morgana allowed you to survive?", "Because I am old, and she thinks I am harmless. She does not know that I have preserved everything she tried to erase. Knowledge survives tyrants."),
                ("Can you help me against Morgana?", "I can offer you truth. The books will tell you her weaknesses, her origins, her fears. With knowledge, perhaps you need not fight her — you can outmaneuver her."),
                ("There is a prophecy in these walls, isn't there?", "There are several. One predicts your return. Another speaks of a reckoning. And a third... well, I've kept that one hidden, even from myself. But it concerns you deeply."),
            ],
        ),
        NPC(
            name="Zote the Mighty",
            role=NPCRole.NOBLE,
            description="A short, pompous man in battered armour stands in the centre of the dusty chamber, gripping a nail sword with excessive pride. He radiates an unshakeable confidence that defies all reason.",
            secret="He is not mighty. He has never won a single fight. He has been wandering the castle for three weeks, completely lost, telling himself it is a heroic quest.",
            greeting="HALT! You stand before ZOTE THE MIGHTY — hero, wanderer, and living legend! State your business, and do so with appropriate reverence!",
            likes=["hearing about his greatness", "his precepts", "being called mighty", "his sword Life Ender"],
            dislikes=["being called lost", "doubting his strength", "other heroes", "admitting weakness"],
            immune_to_powers=True,
            charm_resistance=10,
            intimidate_resistance=10,
            enthrall_resistance=10,
            enthrall_blood_cost=999,
            charm_success_line="This should never appear.",
            charm_fail_line="HAH! Your tricks bounce off the armour of my spirit!",
            intimidate_success_line="This should never appear.",
            intimidate_fail_line="FRIGHTEN me? I once stared down a DRAGON! It blinked first!",
            enthrall_success_line="This should never appear.",
            enthrall_fail_line="My mind is an IMPENETRABLE FORTRESS, guarded by fifty-seven Precepts!",
            thought_read_line="His thoughts are... astonishingly loud. 'I AM ZOTE THE MIGHTY' echoes endlessly. Underneath: mild hunger and a vague worry about which way is north.",
        ),
    ]

    # Add proper dialogue trees to the new NPCs BEFORE returning
    from npc import DialogNode, DialogueOption

    clara = npcs[4]  # Clara the Maid
    clara.add_dialogue(DialogNode(
        id="clara_1",
        text="How long have you worked in this castle?",
        response="All my life, I think. I was born here. I don't remember anywhere else. Just... work.",
        affinity_change=3,
        option_type=DialogueOption.NEUTRAL,
    ))
    clara.add_dialogue(DialogNode(
        id="clara_2",
        text="You deserve better than this life.",
        response="Better? I... I don't know what that means. Morgana has given us food and shelter. That's more than some have.",
        affinity_change=8,
        option_type=DialogueOption.HELP_SEEKING,
    ))
    clara.add_dialogue(DialogNode(
        id="clara_3",
        text="What would you do if you could leave?",
        response="Leave? Where would I go? I have nothing. I'm nobody. But sometimes I dream of gardens... of a place where the sun is warm.",
        affinity_change=5,
        option_type=DialogueOption.NEUTRAL,
    ))
    clara.add_dialogue(DialogNode(
        id="clara_4",
        text="I will free you from this castle. Come with me.",
        response="Free me? You... you really mean that? I'm afraid. But maybe... maybe that fear means I'm alive. Yes. Yes, I'll come with you.",
        requires=["clara_2"],
        min_affinity=25,
        affinity_change=15,
        blood_reward=5,
        suspicion_change=-5,
        option_type=DialogueOption.HELP_SEEKING,
    ))

    theron = npcs[5]  # Theron the Guard Captain
    theron.add_dialogue(DialogNode(
        id="theron_1",
        text="How many soldiers serve under you?",
        response="Twenty good men. Trained, disciplined. They follow orders without question. That's what Morgana demands.",
        affinity_change=2,
        option_type=DialogueOption.NEUTRAL,
    ))
    theron.add_dialogue(DialogNode(
        id="theron_2",
        text="Do your men trust Morgana?",
        response="Trust? No. They obey because they're paid and because the alternative is death. There's a difference.",
        affinity_change=6,
        option_type=DialogueOption.NEUTRAL,
    ))
    theron.add_dialogue(DialogNode(
        id="theron_3",
        text="What would it take for your soldiers to turn against her?",
        response="A leader they believe in. A promise they trust. And proof that rebellion is possible. Right now, Morgana seems... eternal.",
        affinity_change=8,
        option_type=DialogueOption.NEUTRAL,
    ))
    theron.add_dialogue(DialogNode(
        id="theron_4",
        text="I can give them all of that. Join me.",
        response="You're serious. I can see it in your eyes. If you're truly what you claim to be... my men will follow. We're ready.",
        requires=["theron_2"],
        min_affinity=30,
        affinity_change=12,
        blood_reward=8,
        suspicion_change=-10,
        option_type=DialogueOption.NEUTRAL,
    ))

    lydia = npcs[6]  # Lydia the Librarian
    lydia.add_dialogue(DialogNode(
        id="lydia_1",
        text="What is your role in this castle?",
        response="I am the keeper of history. Every book, every record, every secret knowledge—it all passes through my hands. Morgana thinks I'm just an old librarian.",
        affinity_change=4,
        option_type=DialogueOption.NEUTRAL,
    ))
    lydia.add_dialogue(DialogNode(
        id="lydia_2",
        text="Do you have records about my reign?",
        response="Extensive ones. Foundation documents, legal deeds, personal journals. You were a complex lord—neither entirely cruel nor entirely fair.",
        affinity_change=10,
        option_type=DialogueOption.NEUTRAL,
    ))
    lydia.add_dialogue(DialogNode(
        id="lydia_3",
        text="What does Morgana fear most?",
        response="Irrelevance. Replacement. She seized power through force, but she knows it's fragile. One stronger mind could topple her.",
        affinity_change=7,
        option_type=DialogueOption.NEUTRAL,
    ))
    lydia.add_dialogue(DialogNode(
        id="lydia_4",
        text="Teach me what the books reveal about defeating her.",
        response="The books show her weaknesses. But knowledge is only power if you act on it. If you can prove yourself, I will share everything.",
        requires=["lydia_2"],
        min_affinity=35,
        affinity_change=15,
        blood_reward=10,
        suspicion_change=-8,
        option_type=DialogueOption.NEUTRAL,
    ))

    zote = npcs[7]  # Zote the Mighty
    zote.add_dialogue(DialogNode(
        id="zote_1",
        text="Who are you and how did you find this room?",
        response="WHO AM I? I am ZOTE THE MIGHTY! Hero, wanderer, and master of fifty-seven Precepts of Strength! This room found ME. I allow it.",
        affinity_change=2,
        option_type=DialogueOption.NEUTRAL,
    ))
    zote.add_dialogue(DialogNode(
        id="zote_2",
        text="What are these fifty-seven Precepts of Strength?",
        response="Precept the First: Never retreat! Precept the Second: Also never retreat! Precept the Third... it too involves not retreating. The rest are similar. I wrote them myself.",
        affinity_change=4,
        option_type=DialogueOption.NEUTRAL,
    ))
    zote.add_dialogue(DialogNode(
        id="zote_3",
        text="You seem lost.",
        response="LOST? I am STRATEGICALLY POSITIONED. There is a difference. A Mighty hero is never lost — he is simply exploring a previously undiscovered corridor. For the fourth time.",
        affinity_change=3,
        option_type=DialogueOption.NEUTRAL,
    ))
    zote.add_dialogue(DialogNode(
        id="zote_4",
        text="Your sword looks... very light.",
        response="LIFE ENDER is the mightiest blade ever forged! It is crafted from the finest... nail. Yes, a nail. But the INTENTION behind it is fearsome. Do not underestimate intention.",
        affinity_change=5,
        option_type=DialogueOption.NEUTRAL,
    ))
    zote.add_dialogue(DialogNode(
        id="zote_5",
        text="Have you fought anything in this castle?",
        response="I defeated seventeen guards, a sorceress, and what I believe was a very aggressive curtain. The guards fled in terror. The curtain required three attempts. I won ultimately.",
        requires=["zote_1"],
        affinity_change=6,
        option_type=DialogueOption.NEUTRAL,
    ))
    zote.add_dialogue(DialogNode(
        id="zote_6",
        text="I am an ancient vampire lord. Fear me.",
        response="Mm. Yes, I can see the pallor. Impressive. I once encountered a vampire in the eastern provinces. I gave him such a stern look that he turned into a bat immediately and left. Draw your own conclusions.",
        requires=["zote_1"],
        affinity_change=8,
        option_type=DialogueOption.NEUTRAL,
    ))

    morgana = npcs[3]  # Morgana the Sorceress
    morgana.add_dialogue(DialogNode(
        id="morgana_1",
        text="This is my castle. You are the usurper.",
        response="WAS your castle. You've been gone a THOUSAND years. Possession is nine-tenths of the law, vampire.",
        affinity_change=2,
        option_type=DialogueOption.NEUTRAL,
    ))
    morgana.add_dialogue(DialogNode(
        id="morgana_2",
        text="Why did you take my throne?",
        response="Because it was empty. Because I am stronger than the fools who ruled before. Because I WANTED it.",
        affinity_change=4,
        option_type=DialogueOption.NEUTRAL,
    ))
    morgana.add_dialogue(DialogNode(
        id="morgana_3",
        text="We are not so different. Together we could be unstoppable.",
        response="...Immortal. Unstoppable. Ruling side by side. You intrigue me, vampire. Perhaps we could come to an... arrangement.",
        affinity_change=12,
        option_type=DialogueOption.FLIRTY,
    ))
    morgana.add_dialogue(DialogNode(
        id="morgana_marry",
        text="Marry me. Rule beside me as my eternal consort.",
        response="Marry YOU? *laughs* Bold. I like that. Very well. Let us remake this castle together.",
        requires=["morgana_3"],
        min_affinity=50,
        affinity_change=20,
        blood_reward=10,
        suspicion_change=-10,
        option_type=DialogueOption.FLIRTY,
    ))
    morgana.add_dialogue(DialogNode(
        id="morgana_challenge",
        text="Your reign ends now. I challenge you to final combat.",
        response="Finally! The old vampire shows his teeth. Come then. Let us see who is truly the stronger one. This ends tonight.",
        affinity_change=0,
        option_type=DialogueOption.THREATENING,
    ))

    return npcs


def build_castle() -> Castle:
    npcs = make_castle_npcs() + make_extra_npcs()

    rooms = [
Room(
        name="The Castle Gate",
        description=(
            "The great drawbridge hangs over a dry moat, its chains green with age. "
            "Beyond it, the road winds through dark pine forest toward distant villages. "
            "Cold air pours in, carrying the scent of earth, pine needles, and the wider world. "
            "From here you can venture out — but the night demands rest between excursions."
        ),
        atmosphere="The boundary between your world and theirs. The forest watches.",
        exits={"north": 1, "east": 2, "west": 3},
        npc_indices=[],
        feed_available=False,
        candle_positions=[(120, 100), (580, 100), (340, 380)],
        room_number=0,
        outside_access=True,
        interactive_elements=[
            {
                "name": "The drawbridge",
                "description": (
                    "Massive oak planks reinforced with iron. It can be raised or lowered "
                    "from inside. Right now it rests down, an invitation to the night."
                ),
            },
            {
                "name": "The gatehouse arch",
                "description": (
                    "Stone carved with gargoyles that face outward — watching for threats "
                    "approaching the castle, not leaving it. They answer to you."
                ),
            },
            {
                "name": "The road beyond",
                "description": (
                    "Moonlit cobblestones give way to dirt and then to forest. "
                    "Villages lie within an hour's travel. "
                    "Danger and opportunity in equal measure."
                ),
            },
        ],
        locked=False,
    ),
Room(name="The Grand Entrance", description="You drift through the great oak doors, sealed a thousand years ago. Dust motes hang in shafts of moonlight. Twin staircases curve upward into shadow. Beneath your feet, the ancient marble bears your sigil, still sharp despite the centuries. This is where it begins again.", atmosphere="Moonlight cuts through cracked stained glass. Somewhere, footsteps echo.", exits={"south": 0, "west": 6, "east": 7, "north": 10}, npc_indices=[0], feed_available=False, candle_positions=[(80, 60), (620, 60), (80, 350), (620, 350), (300, 250)], room_number=1, interactive_elements=[
            {"name": "Ancient tapestries", "description": "Faded royal banners hang from the walls, depicting hunts from centuries past. Your own hunts, you realize."},
            {"name": "Stone sigil", "description": "Your personal seal is carved into the marble floor. It has been preserved exactly as you remember it. Something glints in the carved grooves — an old iron disc bearing your mark.", "item_id": "iron_talisman"},
        ]),
Room(
        name="The Moonlit Cemetery",
        description=(
            "Rows of old graves stretch into the dark, each stone bearing your family's crest. "
            "Ivy has claimed most of them. The ground is soft, cold, and somehow welcoming. "
            "The dead here were loyal to you in life. They remember."
        ),
        atmosphere="Old names on stone. The night holds its breath.",
        exits={"west": 0},
        npc_indices=[],
        feed_available=False,
        candle_positions=[(100, 200), (600, 200), (350, 420)],
        room_number=2,
        locked=False,
        interactive_elements=[
            {
                "name": "Family graves",
                "description": "Generations of your servants, buried with honours you granted. Their names are still legible.",
            },
            {
                "name": "The old crypt",
                "description": "A stone crypt sealed with your own seal. The interior is dark and dry.",
                "item_id": "wraithskin_wrap",
            },
            {
                "name": "Fresh flowers",
                "description": "Someone has been tending these graves. The flowers are only days old.",
            },
        ],
    ),
Room(
        name="The Old Forge",
        description=(
            "The forge is cold but intact: great bellows, iron anvils, a wall of tongs and hammers. "
            "Your armourer's mark is stamped into the door and every major tool. "
            "Centuries of disuse have left a thick coat of rust, but the bones are sound."
        ),
        atmosphere="Cold iron. Waiting patience. The echo of hammers past.",
        exits={"east": 0},
        npc_indices=[],
        feed_available=False,
        candle_positions=[(150, 180), (550, 180), (350, 400)],
        room_number=3,
        locked=False,
        interactive_elements=[
            {
                "name": "The main anvil",
                "description": "A great iron slab, still true and level after all this time. Your armourer's mark is stamped in the corner.",
            },
            {
                "name": "Weapons rack",
                "description": "Half-finished blades from your era, waiting for completion. The steel is still good.",
                "item_id": "terror_cloak",
            },
            {
                "name": "The bellows",
                "description": "Enormous leather bellows, cracked with age. With repair they could breathe life into the forge again.",
            },
        ],
    ),
Room(
        name="The Velvet Chamber",
        description=(
            "A room of elegant shadows and dark luxury. Velvet drapes frame tall windows "
            "that overlook the castle grounds. A low sofa of deepest crimson sits before a fireplace "
            "where flames dance without heat. On every surface: jewels, stolen treasures, "
            "secrets collected like coins. A woman reclines in the shadows, watching you with gold eyes "
            "that miss nothing. This is where deals are made. Where wills are bent."
        ),
        atmosphere="The scent of perfume and candlewax. Predator and prey, blurred.",
        exits={"southwest": 14, "northwest": 16},
        npc_indices=[],
        feed_available=False,
        candle_positions=[(120, 150), (620, 150), (350, 380)],
        room_number=4,
        locked=False,
        interactive_elements=[
            {
                "name": "The velvet sofa",
                "description": "Luxurious crimson fabric, worn smooth by countless visitors. Some came for company. Some came seeking power. Few left unchanged.",
            },
            {
                "name": "Treasure scattered about",
                "description": "Jewels, coins, artifacts — the spoils of charm and manipulation. Each piece tells a story of seduction and theft.",
            },
            {
                "name": "Mirrors on the walls",
                "description": "Dozens of mirrors reflecting the room endlessly. She watches everything. She is always watching.",
            },
        ],
    ),
Room(name="The Dungeon Wing", description="Damp stone and the metallic smell of old blood. Cells line both walls, iron bars green with rust. Most are empty. Some are not. A massive figure works at a bench of cruel tools — sharpening, organizing, preparing. The leather of his apron is stained with decades of work.", atmosphere="Water drips in the dark. Each drop echoes like a scream.", exits={"north": 8, "west": 15, "northeast": 13}, npc_indices=[4], feed_available=True, candle_positions=[(80, 80), (560, 80), (300, 300)], room_number=5, interactive_elements=[
            {"name": "Iron cells", "description": "The bars are crusted with rust and worse things. Most cells are mercifully empty."},
            {"name": "Torture bench", "description": "Tools of pain arranged with meticulous care. Among them, a cold obsidian amulet — not a tool of torture, but of something older and darker.", "item_id": "shadow_amulet"},
            {"name": "Blood stains", "description": "The stone walls are dark with stains that no amount of scrubbing will remove."},
        ]),
Room(name="The Old Kitchens", description="The smell of tallow and stale bread lingers. Iron pots hang above a cold fireplace. Portraits of your stewards line the walls — generations of loyalty serving Morgana's court. A kitchen maid tends to meals in the background.", atmosphere="The hearth is dead. But the portraits remember.", exits={"east": 1, "west": 9, "south": 8, "north": 11}, npc_indices=[1], feed_available=True, secret_passage=16, candle_positions=[(100, 80), (500, 80), (300, 280)], room_number=6, interactive_elements=[
            {"name": "Portraits of stewards", "description": "Faces of your loyal servants stare down, generation after generation. Most are long dead. Their descendants still serve."},
            {"name": "Fireplace", "description": "The hearth is cold and dark. Ash from a thousand fires has settled into the grate."},
            {"name": "Secret passage", "description": "Behind the portrait of the head steward, you can feel a draft. A hidden passage, perhaps?"},
        ]),
Room(name="The Chapel", description="The pews are warped and split with age. Candlelight flickers across a crumbling altar where sacred objects once sat. Now there is only emptiness and prayer. A priest kneels before the carved stone, his silver cross held to his lips. He does not rise at your approach.", atmosphere="The air tastes of incense and old faith. Something holy recoils from you.", exits={"west": 1, "east": 18, "north": 12}, npc_indices=[2], feed_available=False, candle_positions=[(300, 60), (100, 200), (500, 200), (200, 400), (400, 400)], room_number=7, interactive_elements=[
            {"name": "Altar", "description": "The altar is cracked and bare. Once it held relics. Now it holds only shadows, memories — and a deep-red gemstone left as an offering.", "item_id": "blood_ruby"},
            {"name": "Old pews", "description": "The wooden benches are worn smooth by centuries of prayer. Some are splintered, rotting."},
            {"name": "Silver cross", "description": "Father Dorin clutches a gleaming cross. It catches the candlelight like a beacon against the dark."},
        ]),
Room(name="The Guard Barracks", description="A stark military chamber filled with armor stands, weapons racks, and sleeping platforms. A stern man in polished armor stands at attention, commanding an invisible squad. The discipline here is absolute.", atmosphere="Order. Duty. The sharp smell of steel and oil.", exits={"north": 6, "south": 5, "west": 11}, npc_indices=[9], feed_available=False, candle_positions=[(100, 150), (600, 150), (350, 350)], room_number=8, interactive_elements=[
            {"name": "Armor stands", "description": "Rows of gleaming armor, polished to perfection. Theron's discipline evident in every piece."},
            {"name": "Weapons racks", "description": "Swords, spears, and crossbows hang in perfect order. Ready for anything."},
            {"name": "Sleeping platforms", "description": "Simple but clean cots where soldiers rest between shifts. Their loyalty is bought with order and pay."},
        ]),
Room(name="The Servants' Quarters", description="A cramped, humble space where servants sleep and work. Simple cots line the walls, and a young maid tends to laundry. The room smells of soap and damp cloth. It's a world apart from the grandeur above.", atmosphere="Weary. Simple. The smell of hard work.", exits={"east": 6, "northeast": 11}, npc_indices=[8], feed_available=False, candle_positions=[(100, 200), (400, 200)], room_number=9, interactive_elements=[
            {"name": "Simple cots", "description": "Narrow beds with thin blankets. The servants make do with little."},
            {"name": "Laundry", "description": "Piles of clothes wait to be cleaned. Never-ending work."},
            {"name": "Personal items", "description": "Small tokens hidden under pillows. Memories of lives before the castle, perhaps?"},
        ]),
Room(name="The Upper Gallery", description="Long windows overlook the courtyard below, showing the world beyond your walls. Between tapestries depicting ancient hunts, your defaced portrait hangs — eyes scratched out by angry hands, yet still somehow watching. A woman in black silk sits reading by candlelight.", atmosphere="Your own face watches from the wall. She watches you watching it.", exits={"south": 1, "north": 17, "east": 12, "southeast": 14}, npc_indices=[3], feed_available=False, candle_positions=[(60, 60), (640, 60), (350, 200), (150, 320), (550, 320)], room_number=10, interactive_elements=[
            {"name": "Your portrait", "description": "Someone scratched out your eyes with fury. Yet somehow, they still seem to see you."},
            {"name": "Windows", "description": "Beyond the glass, you can see the world you once ruled. Villages. Forests. The vast world that moved on without you."},
            {"name": "Tapestries", "description": "Ancient hunts are depicted in fading thread. Your hunts, from a time when you ruled openly."},
        ]),
Room(name="The Great Library", description="Towering shelves stretch to the ceiling, packed with ancient tomes and forbidden knowledge. Candlelight flickers across leather spines. An elderly woman moves carefully between the stacks, cataloging secrets. The air smells of old paper and mystery.", atmosphere="Whispers of forgotten histories. The air is thick with knowledge.", exits={"south": 6, "southwest": 9, "east": 8, "northeast": 17}, npc_indices=[10], feed_available=False, candle_positions=[(100, 100), (900, 100), (500, 400)], room_number=11, interactive_elements=[
            {"name": "Ancient tomes", "description": "Books so old they crumble at a touch. Tucked between volumes on the rhetoric of persuasion: a small ring engraved with words that bend lesser wills.", "item_id": "silver_tongue"},
            {"name": "Forbidden knowledge", "description": "Lydia has hidden away secrets that would make lesser minds break. They wait here."},
            {"name": "Hidden sections", "description": "Some shelves seem deliberately obscured. Lydia's true archives, perhaps?"},
        ]),
Room(name="The Alchemist's Laboratory", description="Every surface writhes with activity — bubbling alembics, crystalline growths in jars, pages scrawled with formulae no living scholar could read. The air burns your throat. An ancient man spins at your entrance, eyes bright with recognition and hunger.", atmosphere="Chemical fire and strange energy. The air itself tastes wrong.", exits={"west": 10, "north": 13, "south": 7, "southeast": 18}, npc_indices=[5], feed_available=False, candle_positions=[(150, 60), (450, 60), (300, 250), (100, 350), (500, 350)], room_number=12, interactive_elements=[
            {"name": "Bubbling alembics", "description": "Liquids of impossible colors bubble and steam. Some glow faintly in the dim light."},
            {"name": "Crystalline growths", "description": "Jars line the shelves containing crystals that shouldn't exist. One amber crystal resonates with strange energy when your hand draws near.", "item_id": "philosophers_stone"},
            {"name": "Formulae", "description": "Pages covered in cramped handwriting and arcane symbols. Some might be about you."},
        ]),
Room(name="The East Tower", description="A circular room at the tower's peak. Arrow slits cut the walls, and through them, you can see the world outside — villages, forests, the distant sea. Wind howls, carrying the scent of silver and blessed herbs. At the room's centre stands a woman with a crossbow, her stance perfect, her eyes never wavering.", atmosphere="The wind carries silver and determination. This is not chance. This is purpose.", exits={"south": 12, "southwest": 5}, npc_indices=[6], feed_available=False, candle_positions=[(300, 100), (200, 200), (400, 200)], room_number=13, interactive_elements=[
            {"name": "Arrow slits", "description": "The narrow windows provide perfect sightlines. You could see for miles from here."},
            {"name": "Silver bolts", "description": "A quiver of blessed ammunition and, beneath it, a carved hunter's mask — worn to hide the face. It muffles the supernatural as well as the features.", "item_id": "hunters_mask"},
            {"name": "The distant view", "description": "Villages, forests, and the sea beyond. A world that has continued without you."},
        ]),
Room(name="The Winter Garden", description="A greenhouse filled with exotic plants that shouldn't exist in this climate. Moonlight filters through glass panes, illuminating flowers that bloom in darkness. Vines twist around marble columns like serpents.", atmosphere="Strange beauty. Unnatural growth. Something watches from the shadows.", exits={"northwest": 10, "northeast": 4}, npc_indices=[], feed_available=False, candle_positions=[(150, 150), (550, 150), (350, 350)], room_number=14, interactive_elements=[
            {"name": "Exotic plants", "description": "Flowers that should not bloom. Vines that move like they're breathing. All growing in eternal night."},
            {"name": "Glass panes", "description": "The greenhouse ceiling is made of enchanted glass. It never breaks, never fogs, never lets the cold through."},
            {"name": "Marble columns", "description": "Covered in dark vines. Halfway up one column, wrapped in a vine like placed there for safekeeping: the sigil of your old house, still radiating dominion.", "item_id": "court_medallion"},
        ]),
Room(
        name="The Ancient Catacombs",
        description=(
            "Stone steps descend into a passage that predates the castle itself. "
            "The air is perfectly still, perfectly cold. "
            "Alcoves line the walls, each holding remains wrapped in cloth that has somehow survived "
            "the centuries. These are not servants. These are your ancestors."
        ),
        atmosphere="Silence older than memory. The stone remembers everything.",
        exits={"east": 5},
        npc_indices=[],
        feed_available=False,
        candle_positions=[(80, 180), (620, 180), (350, 450)],
        room_number=15,
        locked=False,
        interactive_elements=[
            {
                "name": "The ancestor alcoves",
                "description": "Rows of wrapped remains, each with a carved name-plate in the old tongue. Your name appears on one.",
            },
            {
                "name": "The sealed vault",
                "description": "At the passage's end, a stone door carved with protective symbols. It opens at your touch, breathing out cold air and older power.",
                "item_id": "lords_chalice",
            },
            {
                "name": "Ancient inscriptions",
                "description": "The walls are covered in writing that predates your own era. History even you did not know.",
            },
        ],
    ),
Room(name="The Throne Room", description="Your throne dominates the chamber — draped in the red and gold of Morgana, symbols of her rule defacing the ancient cushions. The seat is empty now, waiting. A figure in crimson silk sits upon an obsidian throne instead, regarding you with cold amusement. Around it, sconces hold candles that burn despite no hand lighting them.", atmosphere="The throne pulses with unfinished business. It remembers you. And waits.", exits={"south": 17, "southeast": 4}, npc_indices=[7], feed_available=False, candle_positions=[(300, 80), (100, 300), (550, 300), (200, 450), (400, 450)], room_number=16, interactive_elements=[
            {"name": "Your throne", "description": "It has been desecrated with Morgana's symbols, but underneath, the ancient carved wood remembers your rule."},
            {"name": "Obsidian throne", "description": "Morgana's dark throne is beautiful and terrible. The stone seems to drink in the light."},
            {"name": "Self-lighting sconces", "description": "Magic holds these candles aflame without fuel. Morgana's power made manifest."},
        ]),
Room(name="The Inner Sanctum", description="Morgana's personal chambers. Rich furnishings and arcane symbols cover the walls. A crystalline orb pulses with dark magic in the center. Books of spellcraft line obsidian pedestals, protected by wards that crackle with energy.", atmosphere="Power thrums in the air. Magic presses against your skin.", exits={"south": 10, "north": 16, "southwest": 11}, npc_indices=[], feed_available=False, candle_positions=[(300, 150), (100, 350), (500, 350)], room_number=17, interactive_elements=[
            {"name": "Crystalline orb", "description": "Dark magic swirls inside. Beside it sits a shred of consecrated cloth that seems to mute the supernatural aura of anything it touches.", "item_id": "mist_veil"},
            {"name": "Arcane symbols", "description": "The walls are covered with glowing runes. The language of power."},
            {"name": "Spellcraft books", "description": "Morgana's magical research. Perhaps clues to her weaknesses lie here."},
        ]),
Room(name="The Treasury", description="Shelves glint with gold coins, jewels, and artifacts of immense value. But the wealth feels cold, joyless. This is power quantified and locked away. The air is thick with the scent of coins and magic that keeps it all secure.", atmosphere="Greed hangs in the air. Glittering darkness.", exits={"west": 7, "northwest": 12, "north": 19}, npc_indices=[], feed_available=False, candle_positions=[(200, 200), (600, 200), (400, 400)], room_number=18, interactive_elements=[
            {"name": "Gold coins", "description": "More wealth than a kingdom could spend. Yet it buys neither life nor love."},
            {"name": "Jewels and gems", "description": "Rubies, emeralds, sapphires. Artifacts from across the world, collected over centuries."},
            {"name": "Ancient artifacts", "description": "Objects of power from ages past. Among them, an ancient vessel — still humming with forgotten vitality, like it was made to hold something more than wine.", "item_id": "crimson_chalice"},
        ]),
Room(name="The Forgotten Vault", description="A dusty, forgotten chamber buried deep behind the Treasury. Cobwebs hang from the ceiling like curtains. In the centre stands a short man in dented armour, gripping a nail sword, radiating total confidence in all directions. He looks like he has been here a while.", atmosphere="Dust. Silence. The unmistakable aura of someone who is absolutely not lost.", exits={"south": 18}, npc_indices=[11], feed_available=False, candle_positions=[(200, 150), (500, 150), (350, 380)], room_number=19, locked=False, interactive_elements=[
            {"name": "Dusty trophy case", "description": "An empty glass case with Zote's note inside. But on top, partially hidden under centuries of dust: your crown from the first age. It has been waiting.", "item_id": "crown_of_old_night"},
            {"name": "A map on the wall", "description": "A hand-drawn map of the castle — almost completely wrong. Several rooms are labelled 'Here be something scary (avoided heroically)'."},
            {"name": "Pile of notes", "description": "Loose papers covered in cramped handwriting. 'Precept 33: If lost, stand still and declare yourself the centre of the world. The world will eventually come to you.'"},
        ]),
    ]

    return Castle(rooms=rooms, npcs=npcs)
