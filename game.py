"""
game.py — Main game controller: scene management, rendering, and input.

Scenes:
  "explore"     — top-down movement through the castle
  "interact"    — face-to-face with an NPC, choose a power
  "result"      — show the outcome of a power use
  "court"       — view your current court and their roles
  "game_over"   — hunters arrived or you ran out of blood
"""

import pygame
import textwrap
import math
import time
from player import Player
from castle import build_castle
from powers import (
    use_read_thoughts, use_charm,
    use_intimidate, use_enthrall,
    PowerResult,
)
from npc import NPCState, NPCRole
from map_renderer import MapRenderer
from pixel_renderer import (
    draw_room_background, draw_vampire_player,
    draw_npc_sprite, draw_gothic_border, draw_pixel_text,
    draw_npc_portrait,
)
from sound import SoundSystem
from abilities import AbilitySystem, ABILITY_BY_ID
from quests import QuestSystem, QuestStatus
from encounters import random_encounter, VENTURE_COOLDOWN


# ── Colours ──────────────────────────────────────────────────────────────────
BG          = (12,  8, 20)
PANEL_BG    = (22, 15, 35)
BORDER      = (80, 50, 110)
WHITE       = (230, 225, 240)
MUTED       = (140, 130, 160)
BLOOD_RED   = (180, 30, 40)
BLOOD_LIGHT = (220, 80, 90)
GOLD        = (200, 170, 80)
GREEN       = (80, 180, 100)
PURPLE      = (130, 80, 200)

# ── Layout constants ──────────────────────────────────────────────────────────
W, H = 1024, 768
SIDEBAR_W = 260
MAP_W = W - SIDEBAR_W

# ── NPC portrait key mapping ───────────────────────────────────────────────
NPC_PORTRAIT_KEYS = {
    "Aldric the Guard": "aldric",
    "Mira the Servant": "mira",
    "Father Dorin": "dorin",
    "Lady Seraphine": "seraphine",
    "Viktor the Torturer": "viktor",
    "Erasmus the Alchemist": "erasmus",
    "Isolde the Vampire Hunter": "isolde",
}


class Game:
    def __init__(self, screen: pygame.Surface, player_name: str = "Vampire"):
        self.screen = screen
        self.player_name = player_name
        self.player = Player()
        self.castle = build_castle()
        self.scene = "explore"
        self.show_map = False

        # Track which rooms the player has visited
        self.visited_rooms = {0}   # start in room 0

        # Map renderer
        self.map_renderer = MapRenderer(screen)

        # Sound system
        self.sound = SoundSystem()
        self.sound.init()
        self.sound.play_ambient("ambient_explore")

        # Ability / leveling system
        self.abilities = AbilitySystem()
        self.levelup_scene_pending = False

        # Quest system
        self.quests = QuestSystem()
        self.quest_notification = ""
        self.quest_notification_timer = 0.0
        self.journal_scroll = 0       # pixels scrolled down in journal
        self.journal_cursor = 0       # index of selected quest in visible list

        # Animation tick
        self.tick = 0

        # Interaction state
        self.active_npc = None
        self.last_result = None      # ActionResult from last power use
        self.event_log = []          # list of strings shown in sidebar
        self.dialogue_text = ""      # NPC's current response

        # Choice-based dialogue system
        self.convo_history = []      # list of (speaker_label, text, color)

        # Walking/movement state
        self.is_walking = False      # whether player is currently walking to exit
        self.walk_direction = None   # direction being walked (north/south/east/west)
        self.walk_target_room = None # room index to transition to
        self.walk_progress = 0.0     # 0.0 to 1.0 (0 = at room center, 1.0 = reached exit)

        # Interactive room elements
        self.examined_element = None  # currently examined element (dict with name/description)
        self.current_element_idx = 0  # index for cycling through elements

        # Victory/defeat conditions
        self.morgana_defeated = False  # whether Morgana has been defeated in combat
        self.victory_type = None  # "married_morgana", "married_seraphine", or None

        # Outside venture system
        self.last_venture_time = 0.0   # epoch seconds; 0 = never ventured (available immediately)
        self.active_encounter = None   # current Encounter object while in "encounter" scene
        self.encounter_recruited_npc_ids: set = set()   # recruitable_npc_id values already added
        self.encounter_unlocked_room_ids: set = set()   # room indices already unlocked via encounters
        self.completed_encounter_ids: set = set()       # encounter IDs already experienced (no repeats)

        # Simple top-down player position (pixels within map area)
        self.px = MAP_W // 2
        self.py = H // 2
        self.move_speed = 180        # pixels per second

        # Fonts
        self.font_title  = pygame.font.SysFont("Georgia", 28, bold=True)
        self.font_body   = pygame.font.SysFont("Georgia", 17)
        self.font_small  = pygame.font.SysFont("Georgia", 14)
        self.font_ui     = pygame.font.SysFont("Arial",   15)
        self.font_ui_b   = pygame.font.SysFont("Arial",   15, bold=True)

        self._log("You awaken after a thousand years of darkness.")
        self._log("Your castle breathes without you. Reclaim it.")

    # ── Event log ─────────────────────────────────────────────────────────────

    def _log(self, message: str) -> None:
        # Wrap long lines for the sidebar
        wrapped = textwrap.wrap(message, width=30)
        self.event_log.extend(wrapped)
        # Keep only the last 18 lines
        if len(self.event_log) > 18:
            self.event_log = self.event_log[-18:]

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)

    def _handle_key(self, key: int) -> None:
        # M toggles the map from any scene except game over
        if key == pygame.K_m and self.scene != "game_over":
            self.show_map = not self.show_map
            return

        # Q toggles quest journal (from explore when not examining; or from journal)
        if key == pygame.K_q and self.scene == "journal":
            self.scene = "explore"
            return
        if key == pygame.K_q and self.scene == "explore" and not self.examined_element:
            self.journal_scroll = 0
            self.journal_cursor = 0
            self.scene = "journal"
            return

        # I toggles inventory
        if key == pygame.K_i and self.scene == "inventory":
            self.scene = "explore"
            return
        if key == pygame.K_i and self.scene == "explore":
            self.scene = "inventory"
            return

        if self.show_map:
            return

        if self.scene == "levelup":
            self._levelup_key(key)
        elif self.scene == "explore":
            self._explore_key(key)
        elif self.scene == "interact":
            self._interact_key(key)
        elif self.scene == "dialogue":
            self._dialogue_key(key)
        elif self.scene == "result":
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                # Check if a level up is waiting
                if self.abilities.pending_levelup:
                    self.scene = "levelup"
                else:
                    self.scene = "interact"
        elif self.scene == "court":
            if key == pygame.K_ESCAPE:
                self.scene = "explore"
        elif self.scene == "inventory":
            if key in (pygame.K_ESCAPE, pygame.K_i):
                self.scene = "explore"
        elif self.scene == "encounter":
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.active_encounter = None
                self.scene = "explore"
        elif self.scene == "journal":
            self._journal_key(key)
        elif self.scene == "game_over":
            pass

    def _levelup_key(self, key: int) -> None:
        offers = self.abilities.pending_offers
        mapping = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if key in mapping:
            idx = mapping[key]
            if idx < len(offers):
                chosen = offers[idx]
                self.abilities.unlock(chosen)
                ab = ABILITY_BY_ID[chosen]
                self._log(f"✦ Unlocked: {ab.name}")
                self.sound.play_sfx("level_up")
                self.scene = "interact"

    def _explore_key(self, key: int) -> None:
        # E — interact with nearest NPC in room
        if key == pygame.K_e:
            npcs = self.castle.get_npcs_in_room(self.player.current_room)
            visible = [n for n in npcs if not n.is_hostile() and n.state != NPCState.FLED]
            if visible:
                self.active_npc = visible[0]
                self.dialogue_text = self.active_npc.greeting
                self.convo_history = []
                self.scene = "interact"
            else:
                self._log("There is no one here to approach.")

        # X — examine interactive room elements (toggle)
        elif key == pygame.K_x:
            room = self.castle.get_room(self.player.current_room)
            if self.examined_element:
                # Clear examined element
                self.examined_element = None
                self._log("You stop examining the area.")
            elif room.interactive_elements:
                self.current_element_idx = 0
                self.examined_element = room.interactive_elements[0]
                self._log(f"Examining: {self.examined_element['name']}")
                self._try_pickup_item(self.examined_element)
            else:
                self._log("There is nothing of interest here.")

        # Q/Z — cycle through room elements
        elif key == pygame.K_q or key == pygame.K_z:
            room = self.castle.get_room(self.player.current_room)
            if room.interactive_elements and self.examined_element:
                if key == pygame.K_q:
                    self.current_element_idx = (self.current_element_idx - 1) % len(room.interactive_elements)
                else:  # pygame.K_z
                    self.current_element_idx = (self.current_element_idx + 1) % len(room.interactive_elements)
                self.examined_element = room.interactive_elements[self.current_element_idx]
                self._log(f"Examining: {self.examined_element['name']}")
                self._try_pickup_item(self.examined_element)

        # F — feed (if room allows)
        elif key == pygame.K_f:
            room = self.castle.get_room(self.player.current_room)
            if room.feed_available:
                msg = self.player.feed(25)
                self._log(msg)
            else:
                self._log("There is nothing to feed on here.")

        # V — venture outside (Castle Gate only)
        elif key == pygame.K_v:
            room = self.castle.get_room(self.player.current_room)
            if room.outside_access:
                self._start_venture()
            else:
                self._log("There is nowhere to venture from here.")

        # Tab — view your court
        elif key == pygame.K_TAB:
            self.scene = "court"

        # Arrow keys / WASD — move between rooms
        elif key in (pygame.K_UP, pygame.K_w):
            self._move("north")
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._move("south")
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._move("west")
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._move("east")

    def _move(self, direction: str) -> None:
        room = self.castle.get_room(self.player.current_room)
        if direction in room.exits:
            target_idx = room.exits[direction]
            target_room = self.castle.get_room(target_idx)
            if target_room.locked:
                self._log("A sealed door blocks the way. Something must be done to open it.")
                self._log("Check your Quest Journal — a quest may unlock this passage.")
                return
            # Clear examined element when moving
            self.examined_element = None
            # Start walking to the exit instead of teleporting
            self.is_walking = True
            self.walk_direction = direction
            self.walk_target_room = target_idx
            self.walk_progress = 0.0
        else:
            self._log("There is no path that way.")

    def _interact_key(self, key: int) -> None:
        """Number keys 1–4 choose a power. T to open dialogue. ESC to step back."""
        if key == pygame.K_1:
            self._use_power("read")
        elif key == pygame.K_2:
            self._use_power("charm")
        elif key == pygame.K_3:
            self._use_power("intimidate")
        elif key == pygame.K_4:
            self._use_power("enthrall")
        elif key == pygame.K_t:
            self.scene = "dialogue"
        elif key == pygame.K_5 or key == pygame.K_ESCAPE:
            self.scene = "explore"
            self.active_npc = None

    def _dialogue_key(self, key: int) -> None:
        """Handle number keys to pick a dialogue option; ESC to return to interact."""
        if key == pygame.K_ESCAPE:
            self.scene = "interact"
            return
        num_map = {
            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
            pygame.K_4: 3, pygame.K_5: 4,
        }
        if key in num_map:
            idx = num_map[key]
            npc = self.active_npc
            available = npc.get_available_dialogue()
            if idx < len(available):
                node = available[idx]
                player_line = node.text
                npc_response = node.response

                # Record that this dialogue has been seen
                npc.dialogue_seen.add(node.id)

                # Apply affinity change from dialogue node
                affinity_delta = node.affinity_change

                # BONUS: Check if dialogue aligns with NPC preferences
                matches_pref, pref_bonus = npc.check_preference(node.text)
                if matches_pref and pref_bonus > 0:
                    affinity_delta += pref_bonus
                    self._log(f"♥ {npc.name.split()[0]} appreciates that approach!")
                elif not matches_pref and pref_bonus < 0:
                    affinity_delta += pref_bonus  # Reduce affinity
                    self._log(f"✦ {npc.name.split()[0]} seems displeased by that choice.")

                npc.affinity = min(100, max(0, npc.affinity + affinity_delta))

                # Apply rewards
                if node.blood_reward != 0:
                    self.player.blood = min(self.player.max_blood, max(0, self.player.blood + node.blood_reward))
                    if node.blood_reward > 0:
                        self._log(f"★ +{node.blood_reward} blood from conversation")
                    else:
                        self._log(f"✦ {node.blood_reward} blood spent helping")

                if node.suspicion_change != 0:
                    self.player.raise_suspicion(max(0, node.suspicion_change)) if node.suspicion_change > 0 else self.player.lower_suspicion(max(0, -node.suspicion_change))

                # Track vampire secret
                if node.shows_vampire_hint:
                    npc.suspects_vampire = True

                # Check quest triggers after dialogue choice
                self._check_quests()

                # Add to conversation history
                self.convo_history.append(("You", player_line, GOLD))
                self.convo_history.append((npc.name.split()[0], npc_response, (210, 200, 230)))
                self.dialogue_text = npc_response
                if len(self.convo_history) > 20:
                    self.convo_history = self.convo_history[-20:]

                # MARRIAGE: Check if this dialogue leads to marriage
                if node.id == "morgana_marry":
                    self.player.married_to = npc.name
                    self._log(f"★ You are now married to Morgana! The castle is yours.")
                    self.sound.play_sfx("power_charm")  # celebratory sound
                    self._check_victory_conditions()
                elif node.id == "seraphine_marry":
                    self.player.married_to = npc.name
                    self._log(f"★ You are now married to Seraphine! Together you will overthrow the tyrant.")
                    self.sound.play_sfx("power_charm")
                    self._check_victory_conditions()

                # MORGANA DEFEAT: Check if player challenges Morgana to final combat
                if node.id == "morgana_challenge":
                    self._log("★ A final battle erupts in the Throne Room!")
                    self._log("★ After a fierce struggle, Morgana falls...")
                    self._log("★ The tyrant is defeated! The castle is free!")
                    self.morgana_defeated = True
                    self.sound.play_sfx("power_intimidate")  # victory sound
                    # Check for victory after defeating Morgana
                    self._check_victory_conditions()

    def _use_power(self, power: str) -> None:
        npc = self.active_npc
        p = self.player

        if npc.is_controllable():
            self._log(f"{npc.name} is already yours.")
            return

        if npc.immune_to_powers:
            lines = [
                "Your power slides off him like rain off stone.",
                "He doesn't even blink. Your will finds nothing to grip.",
                "An unnerving resilience. This one is beyond your reach.",
            ]
            import random
            self._log(random.choice(lines))
            return

        dispatch = {
            "read":       use_read_thoughts,
            "charm":      use_charm,
            "intimidate": use_intimidate,
            "enthrall":   use_enthrall,
        }

        # Play power sound
        sfx_map = {"read": "power_read", "charm": "power_charm",
                   "intimidate": "power_intimidate", "enthrall": "power_enthrall"}
        self.sound.play_sfx(sfx_map.get(power, "power_charm"))

        result = dispatch[power](p, npc)
        self.last_result = result

        # Apply suspicion delta (capped by iron_will passive)
        delta = result.suspicion_delta
        if delta > 0:
            delta = min(delta, self.abilities.max_suspicion_on_fail())
            p.raise_suspicion(delta)
            if delta >= 20:
                self.sound.transition_ambient("ambient_tense")
        elif delta < 0:
            p.lower_suspicion(-delta)

        # Play result sound
        sfx_result = {
            PowerResult.SUCCESS:       "success",
            PowerResult.PARTIAL:       "partial",
            PowerResult.FAIL:          "fail",
            PowerResult.CRITICAL_FAIL: "critical_fail",
        }
        self.sound.play_sfx(sfx_result[result.result])

        # Award XP
        xp_key = f"{power}_{result.result.name.lower()}"
        xp_map = {
            "read_success": "read_success",
            "charm_success": "charm_success", "charm_partial": "charm_partial",
            "intimidate_success": "intimidate_success", "intimidate_partial": "intimidate_partial",
            "enthrall_success": "enthrall_success", "enthrall_partial": "enthrall_partial",
        }
        self.abilities.award(xp_map.get(xp_key, ""))

        # Add NPC to court if controlled
        if npc.is_controllable():
            p.add_to_court(npc)
            self._log(f"★ {npc.name} joins your court as {npc.role.value}.")
            self.sound.play_sfx("court_join")
            self.abilities.award("court_joined")

        # Record secret if thought-read succeeded
        if power == "read" and result.result == PowerResult.SUCCESS:
            if npc.name not in p.secrets_known:
                p.secrets_known.append(npc.name)

        # Check quest triggers after power use
        self._check_quests()

        self._log(result.log_message)
        self.dialogue_text = result.dialogue
        self.scene = "result"

        # Check game over conditions
        if p.is_alert_triggered():
            self._log("THE HUNTERS HAVE ARRIVED. Your time is up.")
            self.sound.play_sfx("game_over")
            self.scene = "game_over"
        if p.blood <= 0:
            self._log("Your blood runs dry. You dissolve into the dark.")
            self.sound.play_sfx("game_over")
            self.scene = "game_over"

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.tick += 1

        # Countdown quest notification regardless of scene
        if self.quest_notification_timer > 0:
            self.quest_notification_timer -= dt

        if self.scene != "explore":
            return

        # Handle walking animation
        if self.is_walking:
            self.walk_progress += dt * 1.5  # Takes ~0.67 seconds to cross room

            # Calculate target exit position based on direction
            center_x, center_y = MAP_W // 2, H // 2
            exit_x, exit_y = center_x, center_y

            if self.walk_direction == "north":
                exit_y = 40
            elif self.walk_direction == "south":
                exit_y = H - 40
            elif self.walk_direction == "west":
                exit_x = 40
            elif self.walk_direction == "east":
                exit_x = MAP_W - 40

            # Interpolate position from center to exit
            self.px = center_x + (exit_x - center_x) * min(1.0, self.walk_progress)
            self.py = center_y + (exit_y - center_y) * min(1.0, self.walk_progress)

            # When walk completes, transition to new room
            if self.walk_progress >= 1.0:
                self.player.current_room = self.walk_target_room
                self.visited_rooms.add(self.player.current_room)
                new_room = self.castle.get_room(self.player.current_room)
                self._log(f"You enter: {new_room.name}")

                # Reset walking state and reposition player
                self.is_walking = False
                self.walk_direction = None
                self.walk_target_room = None
                self.walk_progress = 0.0
                self.px = MAP_W // 2
                self.py = H // 2

                # Check quest triggers after room transition
                self._check_quests()
            return

        # Normal exploration movement
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy = 1

        self.px = max(20, min(MAP_W - 20, self.px + dx * self.move_speed * dt))
        self.py = max(20, min(H - 20,     self.py + dy * self.move_speed * dt))

    # ── Draw exit portals ─────────────────────────────────────────────────────

    def _draw_exit_portal(self, direction: str, target_room_idx: int) -> None:
        """Draw a glowing portal/door indicating an exit. Locked rooms show a padlock style."""
        if direction == "north":
            x, y = MAP_W // 2 - 20, 20
        elif direction == "south":
            x, y = MAP_W // 2 - 20, H - 50
        elif direction == "west":
            x, y = 20, H // 2 - 20
        elif direction == "east":
            x, y = MAP_W - 60, H // 2 - 20
        else:
            return

        target_room = self.castle.get_room(target_room_idx)
        is_locked = target_room.locked

        portal_glow = pygame.Surface((50, 50), pygame.SRCALPHA)
        glow_alpha = int(100 + 60 * math.sin(self.tick * 0.08))

        if is_locked:
            # Dim red glow for locked portals
            pygame.draw.circle(portal_glow, (120, 30, 30, glow_alpha), (25, 25), 25)
            self.screen.blit(portal_glow, (x - 5, y - 5))
            pygame.draw.rect(self.screen, (100, 40, 40), (x, y, 50, 50), 3)
            pygame.draw.rect(self.screen, (70, 20, 20), (x + 3, y + 3, 44, 44), 1)
            # Lock icon (simple rectangle + arc approximation)
            lock_surf = self.font_ui_b.render("\u26bf", True, (180, 80, 80))
            self.screen.blit(lock_surf, (x + 25 - lock_surf.get_width() // 2,
                                         y + 25 - lock_surf.get_height() // 2))
        else:
            # Normal purple glow
            pygame.draw.circle(portal_glow, (100, 60, 150, glow_alpha), (25, 25), 25)
            self.screen.blit(portal_glow, (x - 5, y - 5))
            pygame.draw.rect(self.screen, (150, 100, 180), (x, y, 50, 50), 3)
            pygame.draw.rect(self.screen, (120, 60, 160), (x + 3, y + 3, 44, 44), 1)
            dir_text = direction[0].upper()
            dir_surf = self.font_ui_b.render(dir_text, True, GOLD)
            self.screen.blit(dir_surf, (x + 25 - dir_surf.get_width() // 2,
                                         y + 25 - dir_surf.get_height() // 2))

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self) -> None:
        self.screen.fill(BG)

        if self.scene == "explore":
            self._draw_explore()
        elif self.scene == "interact":
            self._draw_interact()
        elif self.scene == "dialogue":
            self._draw_dialogue()
        elif self.scene == "result":
            self._draw_result()
        elif self.scene == "levelup":
            self._draw_levelup()
        elif self.scene == "court":
            self._draw_court()
        elif self.scene == "inventory":
            self._draw_inventory()
        elif self.scene == "encounter":
            self._draw_encounter()
        elif self.scene == "journal":
            self._draw_journal()
        elif self.scene == "game_over":
            self._draw_game_over()

        self._draw_sidebar()

        if self.show_map:
            self.map_renderer.draw(self.castle, self.player, self.visited_rooms)

    # ── Explore scene ─────────────────────────────────────────────────────────

    def _draw_explore(self) -> None:
        room = self.castle.get_room(self.player.current_room)

        # Pixel art tiled room background
        draw_room_background(self.screen, MAP_W, H, self.tick,
                             getattr(room, 'candle_positions', []))

        # Atmosphere text
        atm = self.font_small.render(room.atmosphere, True, MUTED)
        self.screen.blit(atm, (20, 16))

        # Room name with shadow
        draw_pixel_text(self.screen, self.font_title, room.name, 20, 38, GOLD, shadow=True)

        # Room description (wrapped)
        desc_lines = textwrap.wrap(room.description, width=55)
        for i, line in enumerate(desc_lines):
            surf = self.font_body.render(line, True, WHITE)
            self.screen.blit(surf, (20, 80 + i * 22))

        # Draw NPC markers
        npcs = self.castle.get_npcs_in_room(self.player.current_room)
        for i, npc in enumerate(npcs):
            if npc.state == NPCState.FLED:
                continue
            nx = 120 + i * 140
            ny = H - 200
            color = npc.status_color()
            role_key = npc.role.value if npc.role.value in ["guard","servant","priest","noble","hunter","alchemist"] else "servant"
            draw_npc_sprite(self.screen, role_key, nx - 18, ny - 60, color, scale=3)
            name_surf = self.font_small.render(npc.name, True, color)
            self.screen.blit(name_surf, (nx - name_surf.get_width() // 2, ny + 6))
            state_surf = self.font_small.render(f"[{npc.status_label()}]", True, color)
            self.screen.blit(state_surf, (nx - state_surf.get_width() // 2, ny + 22))

        # Player pixel sprite
        draw_vampire_player(self.screen, int(self.px) - 18, int(self.py) - 36, self.tick, scale=3)

        # Draw exit portals/doors
        for direction, target_room_id in room.exits.items():
            self._draw_exit_portal(direction, target_room_id)

        # Examined element box (if examining something)
        if self.examined_element:
            pygame.draw.rect(self.screen, (30, 20, 45), (20, H - 180, MAP_W - 40, 130), border_radius=6)
            pygame.draw.rect(self.screen, BORDER, (20, H - 180, MAP_W - 40, 130), 1, border_radius=6)
            elem_name = self.font_ui_b.render(self.examined_element['name'], True, GOLD)
            self.screen.blit(elem_name, (30, H - 170))
            desc_lines = textwrap.wrap(self.examined_element['description'], width=58)
            for i, line in enumerate(desc_lines[:3]):
                desc_surf = self.font_small.render(line, True, (200, 190, 210))
                self.screen.blit(desc_surf, (30, H - 148 + i * 18))
            cycle_hint = self.font_small.render("[Q/Z] Cycle   [X] Clear", True, MUTED)
            self.screen.blit(cycle_hint, (30, H - 94))

        # Venture outside status banner (Castle Gate only)
        if room.outside_access:
            remaining = self._venture_cooldown_remaining()
            if remaining <= 0:
                v_text = "The night awaits.  [V] Venture Outside"
                v_color = GREEN
            else:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                v_text = f"You must rest before venturing again.  ({mins}:{secs:02d})"
                v_color = MUTED
            pygame.draw.rect(self.screen, (18, 25, 18),
                             (20, H - 215, MAP_W - 40, 30), border_radius=4)
            pygame.draw.rect(self.screen, v_color,
                             (20, H - 215, MAP_W - 40, 30), 1, border_radius=4)
            v_surf = self.font_ui_b.render(v_text, True, v_color)
            self.screen.blit(v_surf, (30, H - 208))

        # Exits text hint
        exits = room.exits
        hint_y = H - 48 if not self.examined_element else H - 48
        exits_text = "Exits: " + ", ".join(f"{d.upper()}" for d in exits)
        exits_surf = self.font_ui.render(exits_text, True, MUTED)
        self.screen.blit(exits_surf, (20, hint_y))

        # Controls hint
        venture_hint = "   [V] Venture Outside" if room.outside_access else ""
        hints = f"[WASD] Move   [E] Interact   [F] Feed   [X] Examine   [TAB] Court   [Q] Journal   [I] Items   [M] Map{venture_hint}"
        hint_surf = self.font_ui.render(hints, True, MUTED)
        self.screen.blit(hint_surf, (20, H - 26))

        # Quest completion notification (fades out over 3 seconds)
        if self.quest_notification_timer > 0:
            fade = min(1.0, self.quest_notification_timer)
            notif_color = (int(80 * fade), int(200 * fade), int(100 * fade))
            notif_surf = self.font_ui_b.render(self.quest_notification, True, notif_color)
            self.screen.blit(notif_surf, (20, H - 80))

    # ── Interact scene ────────────────────────────────────────────────────────

    def _draw_interact(self) -> None:
        npc = self.active_npc
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        pygame.draw.rect(self.screen, BORDER, (0, 0, MAP_W, H), 1)

        # NPC portrait on the left
        portrait_x = 20
        portrait_y = 30
        npc_key = NPC_PORTRAIT_KEYS.get(npc.name, "servant")
        draw_npc_portrait(self.screen, npc_key, portrait_x, portrait_y, npc.status_color(), scale=4)

        # NPC name and status (to the right of portrait)
        info_x = 160
        name_surf = self.font_title.render(npc.name, True, GOLD)
        self.screen.blit(name_surf, (info_x, 30))
        role_surf = self.font_ui.render(f"{npc.role.value.title()}  —  {npc.status_label()}", True, npc.status_color())
        self.screen.blit(role_surf, (info_x, 68))

        # Affinity meter
        aff_label = self.font_small.render(f"Relationship: {npc.affinity}/100", True, (150, 180, 240))
        self.screen.blit(aff_label, (info_x, 88))
        aff_bar_w = 120
        pygame.draw.rect(self.screen, (40, 30, 55), (info_x + 120, 88, aff_bar_w, 10), border_radius=2)
        if npc.affinity > 0:
            filled = int(npc.affinity / 100 * aff_bar_w)
            pygame.draw.rect(self.screen, (100, 180, 240), (info_x + 120, 88, filled, 10), border_radius=2)

        # NPC description (wrapped below)
        desc_lines = textwrap.wrap(npc.description, width=60)
        for i, line in enumerate(desc_lines[:3]):
            surf = self.font_body.render(line, True, WHITE)
            self.screen.blit(surf, (info_x, 110 + i * 20))

        # NPC dialogue box (last thing they said / greeting)
        pygame.draw.rect(self.screen, (30, 20, 45), (20, 240, MAP_W - 40, 80), border_radius=6)
        pygame.draw.rect(self.screen, BORDER, (20, 240, MAP_W - 40, 80), 1, border_radius=6)
        d_lines = textwrap.wrap(f'"{self.dialogue_text}"', width=58)
        for i, line in enumerate(d_lines[:3]):
            surf = self.font_body.render(line, True, (210, 200, 230))
            self.screen.blit(surf, (34, 250 + i * 20))

        # Thought reveal (if read)
        if npc.thoughts_read:
            pygame.draw.rect(self.screen, (20, 15, 40), (20, 330, MAP_W - 40, 50), border_radius=4)
            sec_label = self.font_ui_b.render("SECRET KNOWN:", True, (130, 80, 200))
            self.screen.blit(sec_label, (30, 336))
            sec_lines = textwrap.wrap(npc.secret, width=56)
            if sec_lines:
                sec_surf = self.font_small.render(sec_lines[0], True, (170, 140, 210))
                self.screen.blit(sec_surf, (30, 354))

        # Resistance bars
        self._draw_resistance_bars(npc, 390)

        # Power menu
        options = [
            ("[1] Read Thoughts", f"Cost: 5 blood"),
            ("[2] Charm / Seduce", f"Cost: 10 blood"),
            ("[3] Intimidate",     f"Cost: 8 blood"),
            ("[4] Enthrall",       f"Cost: {npc.enthrall_blood_cost} blood"),
            ("[T] Talk",           "Dialogue choices"),
            ("[5] Leave",          ""),
        ]
        pygame.draw.line(self.screen, BORDER, (20, 485), (MAP_W - 20, 485), 1)
        label = self.font_ui_b.render("Choose your approach:", True, MUTED)
        self.screen.blit(label, (30, 493))
        for i, (name, cost) in enumerate(options):
            col = GOLD if name.startswith("[T]") else (WHITE if i < 4 else MUTED)
            opt_surf = self.font_ui_b.render(name, True, col)
            self.screen.blit(opt_surf, (30, 515 + i * 32))
            if cost:
                cost_surf = self.font_small.render(cost, True, MUTED)
                self.screen.blit(cost_surf, (260, 519 + i * 32))

    def _draw_resistance_bars(self, npc, y: int) -> None:
        label = self.font_ui_b.render("NPC resistances", True, MUTED)
        self.screen.blit(label, (30, y))
        bars = [
            ("Charm",      npc.charm_resistance,      (100, 160, 220)),
            ("Intimidate", npc.intimidate_resistance,  (220, 120, 60)),
            ("Enthrall",   npc.enthrall_resistance,    (160, 80, 210)),
        ]
        for i, (name, val, color) in enumerate(bars):
            bx, by = 30, y + 24 + i * 26
            n_surf = self.font_small.render(f"{name}:", True, MUTED)
            self.screen.blit(n_surf, (bx, by))
            bar_x = bx + 90
            pygame.draw.rect(self.screen, (40, 30, 55), (bar_x, by + 2, 100, 14), border_radius=3)
            filled = int(val / 10 * 100)
            if filled > 0:
                pygame.draw.rect(self.screen, color, (bar_x, by + 2, filled, 14), border_radius=3)
            val_surf = self.font_small.render(str(val), True, color)
            self.screen.blit(val_surf, (bar_x + 108, by))

    # ── Dialogue scene ────────────────────────────────────────────────────────

    def _draw_dialogue(self) -> None:
        npc = self.active_npc
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        pygame.draw.rect(self.screen, BORDER, (0, 0, MAP_W, H), 1)

        # Large NPC portrait on the left side
        portrait_x = 20
        portrait_y = 20
        npc_key = NPC_PORTRAIT_KEYS.get(npc.name, "servant")
        draw_npc_portrait(self.screen, npc_key, portrait_x, portrait_y, npc.status_color(), scale=5)

        # NPC header with affinity meter on the right
        info_x = 200
        name_surf = self.font_title.render(npc.name, True, GOLD)
        self.screen.blit(name_surf, (info_x, 22))
        role_surf = self.font_ui.render(f"{npc.role.value.title()}  —  {npc.status_label()}", True, npc.status_color())
        self.screen.blit(role_surf, (info_x, 58))

        # Affinity meter
        aff_label = self.font_small.render(f"Relationship: {npc.affinity}/100", True, (150, 180, 240))
        self.screen.blit(aff_label, (info_x, 76))
        aff_bar_w = 120
        pygame.draw.rect(self.screen, (40, 30, 55), (info_x + 130, 76, aff_bar_w, 12), border_radius=2)
        if npc.affinity > 0:
            filled = int(npc.affinity / 100 * aff_bar_w)
            pygame.draw.rect(self.screen, (100, 180, 240), (info_x + 130, 76, filled, 12), border_radius=2)

        # Vampire secret indicator
        if npc.suspects_vampire:
            suspect_surf = self.font_small.render("⚠ Knows your secret", True, (200, 100, 100))
            self.screen.blit(suspect_surf, (info_x, 92))

        # Conversation history box - larger, show more lines
        pygame.draw.rect(self.screen, (25, 16, 40), (20, 104, MAP_W - 40, 220), border_radius=6)
        pygame.draw.rect(self.screen, BORDER, (20, 104, MAP_W - 40, 220), 1, border_radius=6)
        if self.convo_history:
            visible = self.convo_history[-10:]  # Show last 10 lines instead of 6
            for i, (speaker, msg, color) in enumerate(visible):
                is_player = speaker == "You"
                spk_surf = self.font_small.render(f"{speaker}:", True, GOLD if is_player else (180, 150, 220))
                self.screen.blit(spk_surf, (30, 112 + i * 20))
                # Word wrap long messages
                msg_lines = textwrap.wrap(msg, width=62)
                for j, msg_line in enumerate(msg_lines[:2]):
                    short = msg_line if len(msg_line) <= 56 else msg_line[:53] + "…"
                    msg_surf = self.font_small.render(short, True, color)
                    self.screen.blit(msg_surf, (30 + spk_surf.get_width() + 6, 112 + i * 20 + j * 14))
        else:
            greeting_lines = textwrap.wrap(f'"{npc.greeting}"', width=60)
            for i, line in enumerate(greeting_lines[:8]):
                surf = self.font_small.render(line, True, (210, 200, 230))
                self.screen.blit(surf, (30, 112 + i * 18))

        # Dialogue choices
        pygame.draw.line(self.screen, BORDER, (20, 336), (MAP_W - 20, 336), 1)
        choose_surf = self.font_ui_b.render("What do you say?", True, MUTED)
        self.screen.blit(choose_surf, (30, 344))

        available = npc.get_available_dialogue()
        for i, node in enumerate(available):
            oy = 372 + i * 48
            if oy + 40 > H - 50:  # Don't draw off-screen
                break

            num_col = GOLD
            num_surf = self.font_ui_b.render(f"[{i + 1}]", True, num_col)
            self.screen.blit(num_surf, (30, oy))

            lines = textwrap.wrap(node.text, width=55)
            for j, line in enumerate(lines[:2]):
                col = WHITE if j == 0 else MUTED
                line_surf = self.font_ui.render(line, True, col)
                self.screen.blit(line_surf, (68, oy + j * 18))

            # Show preference hint
            matches_pref, bonus = npc.check_preference(node.text)
            if matches_pref and bonus > 0:
                hint = self.font_small.render("♥ they like this", True, (100, 180, 100))
            elif not matches_pref and bonus < 0:
                hint = self.font_small.render("✦ they dislike this", True, (220, 100, 100))
            else:
                hint = self.font_small.render("○ neutral", True, MUTED)
            self.screen.blit(hint, (550, oy))

        # Show locked options too, but grayed out with reason
        locked = [n for n in npc.dialogue_tree.values() if not n.is_available(npc.affinity, npc.dialogue_seen)]
        for i, node in enumerate(locked[:2]):  # Show up to 2 locked options
            if available:
                oy = 372 + len(available) * 48 + i * 32
            else:
                oy = 372 + i * 32
            if oy + 30 > H - 50:
                break

            num_surf = self.font_ui.render(f"[{len(available) + i + 1}]", True, (100, 100, 120))
            self.screen.blit(num_surf, (30, oy))

            lock_reason = node.lock_reason(npc.affinity, npc.dialogue_seen)
            lock_surf = self.font_small.render(f"🔒 {lock_reason}", True, (120, 100, 140))
            self.screen.blit(lock_surf, (68, oy))

        esc_surf = self.font_ui.render("[ESC] Back", True, MUTED)
        self.screen.blit(esc_surf, (30, H - 34))

    # ── Result scene ──────────────────────────────────────────────────────────

    def _draw_result(self) -> None:
        npc = self.active_npc
        result = self.last_result
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        pygame.draw.rect(self.screen, BORDER, (0, 0, MAP_W, H), 1)

        # Result header
        result_colors = {
            PowerResult.SUCCESS:       (80, 200, 120),
            PowerResult.PARTIAL:       (200, 180, 60),
            PowerResult.FAIL:          (200, 100, 60),
            PowerResult.CRITICAL_FAIL: (220, 40, 40),
        }
        result_labels = {
            PowerResult.SUCCESS:       "SUCCESS",
            PowerResult.PARTIAL:       "PARTIAL SUCCESS",
            PowerResult.FAIL:          "FAILED",
            PowerResult.CRITICAL_FAIL: "CRITICAL FAILURE",
        }
        color = result_colors[result.result]
        label = self.font_title.render(result_labels[result.result], True, color)
        self.screen.blit(label, (30, 30))

        power_surf = self.font_ui.render(f"Power used: {result.power}", True, MUTED)
        self.screen.blit(power_surf, (30, 72))

        # NPC dialogue
        pygame.draw.rect(self.screen, (30, 20, 45), (20, 110, MAP_W - 40, 120), border_radius=6)
        pygame.draw.rect(self.screen, color, (20, 110, MAP_W - 40, 120), 1, border_radius=6)
        npc_label = self.font_ui_b.render(f"{npc.name} says:", True, GOLD)
        self.screen.blit(npc_label, (34, 120))
        d_lines = textwrap.wrap(f'"{self.dialogue_text}"', width=56)
        for i, line in enumerate(d_lines[:4]):
            surf = self.font_body.render(line, True, WHITE)
            self.screen.blit(surf, (34, 144 + i * 22))

        # Consequence summary
        pygame.draw.line(self.screen, BORDER, (20, 250), (MAP_W - 20, 250), 1)
        con_label = self.font_ui_b.render("Consequences:", True, MUTED)
        self.screen.blit(con_label, (30, 260))

        blood_text = f"Blood spent: {result.blood_cost}"
        blood_surf = self.font_body.render(blood_text, True, BLOOD_LIGHT)
        self.screen.blit(blood_surf, (30, 288))

        if result.suspicion_delta > 0:
            susp_text = f"Castle suspicion +{result.suspicion_delta}  (now {self.player.castle_suspicion}/100)"
            susp_color = (220, 100, 60)
        elif result.suspicion_delta < 0:
            susp_text = f"Castle suspicion {result.suspicion_delta}  (now {self.player.castle_suspicion}/100)"
            susp_color = GREEN
        else:
            susp_text = f"Castle suspicion unchanged  ({self.player.castle_suspicion}/100)"
            susp_color = MUTED
        susp_surf = self.font_body.render(susp_text, True, susp_color)
        self.screen.blit(susp_surf, (30, 316))

        state_text = f"{npc.name} is now: {npc.status_label()}"
        state_surf = self.font_body.render(state_text, True, npc.status_color())
        self.screen.blit(state_surf, (30, 344))

        # Continue prompt
        cont = self.font_ui.render("[ SPACE / ENTER ] Continue", True, MUTED)
        self.screen.blit(cont, (30, H - 40))

    # ── Level up scene ────────────────────────────────────────────────────────

    def _draw_levelup(self) -> None:
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        draw_gothic_border(self.screen, pygame.Rect(10, 10, MAP_W - 20, H - 20), (200, 170, 80), 2)

        draw_pixel_text(self.screen, self.font_title,
                        f"LEVEL UP — Level {self.abilities.level}", 30, 30, GOLD, shadow=True)

        sub = self.font_body.render("Choose an ability to unlock:", True, MUTED)
        self.screen.blit(sub, (30, 72))

        offers = self.abilities.pending_offers
        for i, ability_id in enumerate(offers):
            ab = ABILITY_BY_ID[ability_id]
            oy = 120 + i * 130
            kind_color = (100, 200, 140) if ab.kind.name == "PASSIVE" else (100, 160, 240)

            draw_gothic_border(self.screen, pygame.Rect(20, oy, MAP_W - 40, 110),
                               kind_color, 1)
            pygame.draw.rect(self.screen, (20, 14, 35), (21, oy + 1, MAP_W - 42, 108))

            key_surf = self.font_ui_b.render(f"[{i+1}]", True, GOLD)
            self.screen.blit(key_surf, (36, oy + 12))
            name_surf = self.font_ui_b.render(ab.name, True, WHITE)
            self.screen.blit(name_surf, (70, oy + 12))
            kind_surf = self.font_small.render(ab.kind.name.title(), True, kind_color)
            self.screen.blit(kind_surf, (70, oy + 34))
            desc_lines = textwrap.wrap(ab.description, width=58)
            for j, line in enumerate(desc_lines[:2]):
                d = self.font_small.render(line, True, MUTED)
                self.screen.blit(d, (36, oy + 56 + j * 18))
            if ab.active_cost > 0:
                cost = self.font_small.render(f"Cost: {ab.active_cost} blood", True, BLOOD_LIGHT)
                self.screen.blit(cost, (36, oy + 90))

    # ── Court scene ───────────────────────────────────────────────────────────

    def _draw_court(self) -> None:
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        pygame.draw.rect(self.screen, BORDER, (0, 0, MAP_W, H), 1)

        title = self.font_title.render("Your Court", True, GOLD)
        self.screen.blit(title, (30, 30))

        if not self.player.court:
            empty = self.font_body.render("Your court is empty. No one serves you yet.", True, MUTED)
            self.screen.blit(empty, (30, 100))
        else:
            for i, npc in enumerate(self.player.court):
                cy = 90 + i * 80
                pygame.draw.rect(self.screen, (30, 20, 48), (20, cy, MAP_W - 40, 70), border_radius=6)
                pygame.draw.rect(self.screen, npc.status_color(), (20, cy, MAP_W - 40, 70), 1, border_radius=6)
                name_surf = self.font_ui_b.render(f"{npc.name}  —  {npc.role.value.title()}", True, npc.status_color())
                self.screen.blit(name_surf, (34, cy + 10))
                state_surf = self.font_small.render(f"State: {npc.status_label()}", True, MUTED)
                self.screen.blit(state_surf, (34, cy + 32))
                if npc.thoughts_read:
                    sec_surf = self.font_small.render(f"Secret: {npc.secret[:60]}...", True, (150, 110, 200))
                    self.screen.blit(sec_surf, (34, cy + 50))

        esc_surf = self.font_ui.render("[ESC] Return", True, MUTED)
        self.screen.blit(esc_surf, (30, H - 40))

    # ── Game over ─────────────────────────────────────────────────────────────

    def _draw_game_over(self) -> None:
        self.screen.fill((5, 0, 10))

        # Check for victory conditions
        if self.victory_type == "married_morgana":
            msg = self.font_title.render("ETERNAL REIGN", True, GOLD)
            sub = self.font_body.render("You and Morgana are bound as equals now.", True, (200, 170, 100))
            detail1 = self.font_body.render("Together, you remake the castle in your image.", True, WHITE)
            detail2 = self.font_body.render("The old vampire and the sorceress rule as one.", True, WHITE)
            self.screen.blit(msg, (MAP_W // 2 - msg.get_width() // 2, H // 2 - 100))
            self.screen.blit(sub, (MAP_W // 2 - sub.get_width() // 2, H // 2 - 20))
            self.screen.blit(detail1, (MAP_W // 2 - detail1.get_width() // 2, H // 2 + 20))
            self.screen.blit(detail2, (MAP_W // 2 - detail2.get_width() // 2, H // 2 + 60))

        elif self.victory_type == "married_seraphine":
            msg = self.font_title.render("LIBERATION", True, GOLD)
            sub = self.font_body.render("With Seraphine at your side, you have slain the tyrant.", True, (200, 170, 100))
            detail1 = self.font_body.render("The castle is freed from Morgana's grip.", True, WHITE)
            detail2 = self.font_body.render("Together you rebuild with grace and wisdom.", True, WHITE)
            self.screen.blit(msg, (MAP_W // 2 - msg.get_width() // 2, H // 2 - 100))
            self.screen.blit(sub, (MAP_W // 2 - sub.get_width() // 2, H // 2 - 20))
            self.screen.blit(detail1, (MAP_W // 2 - detail1.get_width() // 2, H // 2 + 20))
            self.screen.blit(detail2, (MAP_W // 2 - detail2.get_width() // 2, H // 2 + 60))

        else:
            # Default loss condition
            msg = self.font_title.render("THE NIGHT ENDS", True, BLOOD_RED)
            sub = self.font_body.render("Your dominion crumbles. The hunters close in.", True, MUTED)
            court_count = len(self.player.court)
            stat = self.font_body.render(f"Court members claimed: {court_count}   Suspicion: {self.player.castle_suspicion}/100", True, MUTED)
            self.screen.blit(msg, (MAP_W // 2 - msg.get_width() // 2, H // 2 - 60))
            self.screen.blit(sub, (MAP_W // 2 - sub.get_width() // 2, H // 2))
            self.screen.blit(stat, (MAP_W // 2 - stat.get_width() // 2, H // 2 + 40))

    # ── Victory/Defeat Conditions ──────────────────────────────────────────────

    def _check_victory_conditions(self) -> None:
        """Check if player has met any win conditions."""
        # Victory 1: Married to Morgana (she becomes your ally, you rule together)
        if self.player.married_to == "Morgana the Sorceress":
            self.victory_type = "married_morgana"
            self.scene = "game_over"
            return

        # Victory 2: Married to Seraphine AND Morgana defeated
        if self.player.married_to == "Lady Seraphine" and self.morgana_defeated:
            self.victory_type = "married_seraphine"
            self.scene = "game_over"
            return

    # ── Quest helpers ─────────────────────────────────────────────────────────

    def _check_quests(self) -> None:
        """Run quest trigger check and display notifications for any completions."""
        completed = self.quests.check_triggers(self)
        for title in completed:
            self._log(f"✓ Quest complete: {title}")
            self.quest_notification = f"QUEST COMPLETE: {title}"
            self.quest_notification_timer = 3.5

    # ── Journal scene ─────────────────────────────────────────────────────────

    def _journal_key(self, key: int) -> None:
        if key in (pygame.K_ESCAPE, pygame.K_q):
            self.scene = "explore"
            return

        visible = self.quests.visible_quests()
        if not visible:
            return

        if key in (pygame.K_DOWN, pygame.K_s):
            self.journal_cursor = min(len(visible) - 1, self.journal_cursor + 1)
        elif key in (pygame.K_UP, pygame.K_w):
            self.journal_cursor = max(0, self.journal_cursor - 1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            # Claim reward for the selected quest
            quest = visible[self.journal_cursor]
            claimed = self.quests.claim_reward(self, quest.id)
            if claimed:
                rewards = quest.rewards
                parts = []
                if rewards.get("blood", 0):
                    parts.append(f"+{rewards['blood']} blood")
                if rewards.get("xp", 0):
                    parts.append(f"+{rewards['xp']} XP")
                if rewards.get("suspicion_reduction", 0):
                    parts.append(f"-{rewards['suspicion_reduction']} suspicion")
                reward_str = ", ".join(parts) if parts else "nothing"
                self._log(f"★ Claimed: {quest.title} ({reward_str})")

    def _draw_journal(self) -> None:
        HEADER_H = 60
        FOOTER_H = 40
        CONTENT_H = H - HEADER_H - FOOTER_H

        # ── Background + border ──
        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        draw_gothic_border(self.screen, pygame.Rect(0, 0, MAP_W, H), BORDER, 2)
        draw_pixel_text(self.screen, self.font_title, "Quest Journal", 30, 14, GOLD, shadow=True)

        # ── Build ordered visible quest list ──
        visible = self.quests.visible_quests()
        self.journal_cursor = max(0, min(self.journal_cursor, len(visible) - 1))

        # ── Render all content onto a tall offscreen surface ──
        content_surf = pygame.Surface((MAP_W, 3000), pygame.SRCALPHA)
        content_surf.fill((0, 0, 0, 0))

        y = 0
        quest_y_positions = []   # (quest_index, y_top, y_bottom) for auto-scroll

        # Separate main and side into sections with headers
        main_quests = [q for q in visible if q.quest_type == "main"]
        side_quests  = [q for q in visible if q.quest_type == "side"]
        quest_idx = 0

        # Main section
        main_label = self.font_ui_b.render("\u2500\u2500 MAIN QUESTS \u2500\u2500", True, GOLD)
        content_surf.blit(main_label, (30, y))
        y += 28
        if main_quests:
            for quest in main_quests:
                selected = (quest_idx == self.journal_cursor)
                y_top = y
                y = self._draw_quest_entry(quest, y, surf=content_surf, selected=selected)
                quest_y_positions.append((quest_idx, y_top, y))
                y += 6
                quest_idx += 1
        else:
            s = self.font_small.render("No main quests discovered yet.", True, MUTED)
            content_surf.blit(s, (34, y))
            y += 22

        y += 14

        # Side section
        side_label = self.font_ui_b.render("\u2500\u2500 SIDE QUESTS \u2500\u2500", True, PURPLE)
        content_surf.blit(side_label, (30, y))
        y += 28
        if side_quests:
            for quest in side_quests:
                selected = (quest_idx == self.journal_cursor)
                y_top = y
                y = self._draw_quest_entry(quest, y, surf=content_surf, selected=selected)
                quest_y_positions.append((quest_idx, y_top, y))
                y += 6
                quest_idx += 1
        else:
            s = self.font_small.render("Explore the castle to discover side quests.", True, MUTED)
            content_surf.blit(s, (34, y))
            y += 22

        total_content_h = y + 10

        # ── Auto-scroll to keep selected quest visible ──
        if quest_y_positions:
            for idx, y_top, y_bot in quest_y_positions:
                if idx == self.journal_cursor:
                    if y_top < self.journal_scroll:
                        self.journal_scroll = y_top
                    elif y_bot > self.journal_scroll + CONTENT_H:
                        self.journal_scroll = y_bot - CONTENT_H
                    break

        max_scroll = max(0, total_content_h - CONTENT_H)
        self.journal_scroll = max(0, min(self.journal_scroll, max_scroll))

        # ── Blit visible slice ──
        self.screen.blit(content_surf, (0, HEADER_H),
                         pygame.Rect(0, self.journal_scroll, MAP_W, CONTENT_H))

        # ── Scrollbar ──
        if max_scroll > 0:
            track_x = MAP_W - 10
            track_top = HEADER_H + 4
            track_h = CONTENT_H - 8
            pygame.draw.rect(self.screen, (40, 30, 60), (track_x, track_top, 6, track_h), border_radius=3)
            thumb_pct = self.journal_scroll / max_scroll
            thumb_h = max(20, int(track_h * CONTENT_H / total_content_h))
            thumb_y = track_top + int((track_h - thumb_h) * thumb_pct)
            pygame.draw.rect(self.screen, BORDER, (track_x, thumb_y, 6, thumb_h), border_radius=3)

        if self.journal_scroll < max_scroll:
            arrow = self.font_ui_b.render("\u25bc more", True, MUTED)
            self.screen.blit(arrow, (MAP_W // 2 - arrow.get_width() // 2, H - FOOTER_H - 2))

        # ── Footer ──
        pygame.draw.line(self.screen, BORDER, (10, H - FOOTER_H), (MAP_W - 10, H - FOOTER_H), 1)
        # Context-sensitive footer hint
        if visible and self.journal_cursor < len(visible):
            sel = visible[self.journal_cursor]
            if sel.status == QuestStatus.COMPLETED and not sel.reward_claimed:
                hint_text = "[ENTER / SPACE] Claim Reward    [↑↓] Navigate    [Q / ESC] Close"
                hint_color = GREEN
            else:
                hint_text = "[↑↓ / WS] Navigate    [Q / ESC] Close"
                hint_color = MUTED
        else:
            hint_text = "[↑↓ / WS] Navigate    [Q / ESC] Close"
            hint_color = MUTED
        hint = self.font_ui.render(hint_text, True, hint_color)
        self.screen.blit(hint, (MAP_W // 2 - hint.get_width() // 2, H - FOOTER_H + 12))

    def _draw_quest_entry(self, quest, y: int, surf=None, selected: bool = False) -> int:
        """Draw a single quest card onto surf (defaults to self.screen). Returns new y."""
        if surf is None:
            surf = self.screen

        status_colors = {
            QuestStatus.ACTIVE:       GOLD,
            QuestStatus.COMPLETED:    GREEN,
            QuestStatus.UNDISCOVERED: MUTED,
            QuestStatus.FAILED:       BLOOD_RED,
        }
        status_labels = {
            QuestStatus.ACTIVE:       "[ACTIVE]",
            QuestStatus.COMPLETED:    "[CLAIMED]" if quest.reward_claimed else "[DONE — CLAIM REWARD]",
            QuestStatus.UNDISCOVERED: "[?]",
            QuestStatus.FAILED:       "[FAILED]",
        }
        color = status_colors[quest.status]
        # Unclaimed completed quests pulse with green
        if quest.status == QuestStatus.COMPLETED and not quest.reward_claimed:
            color = GREEN

        # Build reward summary string
        rewards = quest.rewards
        reward_parts = []
        if rewards.get("blood", 0):
            reward_parts.append(f"+{rewards['blood']} Blood")
        if rewards.get("xp", 0):
            reward_parts.append(f"+{rewards['xp']} XP")
        if rewards.get("suspicion_reduction", 0):
            reward_parts.append(f"-{rewards['suspicion_reduction']} Suspicion")
        if getattr(quest, "unlocks_room", -1) >= 0:
            room = self.castle.get_room(quest.unlocks_room)
            reward_parts.append(f"Unlocks: {room.name}")
        reward_str = "  |  Reward: " + ", ".join(reward_parts) if reward_parts else ""

        # Calculate card height: objectives + optional reward row
        extra_h = max(0, len(quest.objectives) - 1) * 18
        has_reward_row = bool(reward_parts)
        card_h = 64 + extra_h + (20 if has_reward_row else 0)

        # Card background
        bg_color = (35, 28, 55) if selected else (25, 18, 42)
        pygame.draw.rect(surf, bg_color, (20, y, MAP_W - 40, card_h), border_radius=6)
        border_color = color if selected else (max(0, color[0] - 60), max(0, color[1] - 60), max(0, color[2] - 60))
        pygame.draw.rect(surf, border_color, (20, y, MAP_W - 40, card_h), 2 if selected else 1, border_radius=6)

        # Selection indicator
        if selected:
            pygame.draw.rect(surf, color, (20, y, 4, card_h), border_radius=2)

        # Status badge + title
        badge_text = f"{status_labels[quest.status]}  {quest.title}"
        badge = self.font_ui_b.render(badge_text, True, color)
        surf.blit(badge, (34, y + 8))

        # Objectives
        obj_y = y + 28
        for obj in quest.objectives:
            tick = "\u2713" if obj.completed else "\u25cb"
            obj_color = GREEN if obj.completed else WHITE
            obj_surf = self.font_small.render(f"  {tick} {obj.description}", True, obj_color)
            surf.blit(obj_surf, (34, obj_y))
            obj_y += 18

        # Reward row
        if has_reward_row:
            if quest.reward_claimed:
                rew_color = MUTED
                rew_text = f"  \u2713 Reward collected:{reward_str.replace('  |  Reward: ', ' ')}"
            else:
                rew_color = GREEN if quest.status == QuestStatus.COMPLETED else MUTED
                rew_text = f"  \u2605{reward_str}"
            rew_surf = self.font_small.render(rew_text, True, rew_color)
            surf.blit(rew_surf, (34, obj_y))

        return y + card_h

    # ── Outside venture ───────────────────────────────────────────────────────

    def _venture_cooldown_remaining(self) -> float:
        """Seconds until player can venture again. 0 means available now."""
        elapsed = time.time() - self.last_venture_time
        return max(0.0, VENTURE_COOLDOWN - elapsed)

    def _start_venture(self) -> None:
        """Attempt to venture outside. Blocked if cooldown is active."""
        remaining = self._venture_cooldown_remaining()
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            self._log(f"You must rest before venturing again. ({mins}:{secs:02d})")
            return

        # Pick encounter — filter out ones already completed
        castle_npc_names = {n.name for n in self.castle.npcs}
        encounter = random_encounter(
            castle_npc_names=castle_npc_names,
            unlocked_room_ids=self.encounter_unlocked_room_ids,
            completed_encounter_ids=self.completed_encounter_ids,
        )
        self.active_encounter = encounter
        self.last_venture_time = time.time()

        # Mark this encounter as completed
        self.completed_encounter_ids.add(encounter.id)

        # Blood
        if encounter.blood_reward > 0:
            self.player.blood = min(self.player.max_blood,
                                    self.player.blood + encounter.blood_reward)
        elif encounter.blood_reward < 0:
            self.player.blood = max(0, self.player.blood + encounter.blood_reward)

        # XP
        if encounter.xp_reward > 0:
            if self.abilities.add_xp(encounter.xp_reward):
                self.scene = "levelup"   # will be overridden below; levelup checked later

        # Suspicion
        if encounter.suspicion_change > 0:
            self.player.raise_suspicion(encounter.suspicion_change)
        elif encounter.suspicion_change < 0:
            self.player.lower_suspicion(-encounter.suspicion_change)

        # Item
        if encounter.item_id:
            from items import ITEMS
            item = ITEMS.get(encounter.item_id)
            if item:
                self.player.add_item(item)

        # NPC recruitment — create NPC and place in thematic room
        if encounter.recruitable_npc_id:
            from encounters import ENCOUNTER_NPC_FACTORIES, ENCOUNTER_NPC_NAMES
            factory = ENCOUNTER_NPC_FACTORIES.get(encounter.recruitable_npc_id)
            if factory and encounter.recruitable_npc_id not in self.encounter_recruited_npc_ids:
                npc = factory()
                # Place NPCs in thematic rooms based on their role/identity
                npc_room_placement = {
                    "celestine": 18, # Black Widow → Velvet Chamber (her private seduction room)
                    "gregori": 16,   # Gravedigger → Cemetery
                    "esme": 18,      # Hedge Witch → Catacombs (magical)
                    "roland": 17,    # Warrior → Forge
                    "petyr": 15,     # Merchant → Castle Gate (meeting place)
                    "agnes": 16,     # Nun → Cemetery (sacred spaces)
                    "caius": 17,     # Knight → Forge (armory)
                }
                room_idx = npc_room_placement.get(encounter.recruitable_npc_id, 15)
                self.castle.add_npc_to_room(npc, room_idx)
                self.encounter_recruited_npc_ids.add(encounter.recruitable_npc_id)
                npc_name = ENCOUNTER_NPC_NAMES.get(encounter.recruitable_npc_id, npc.name)
                room_name = self.castle.get_room(room_idx).name
                self._log(f"★ {npc_name} has arrived in {room_name}.")

        # Room unlock
        if encounter.unlocks_room >= 0 and encounter.unlocks_room not in self.encounter_unlocked_room_ids:
            self.castle.unlock_room(encounter.unlocks_room)
            self.encounter_unlocked_room_ids.add(encounter.unlocks_room)
            room_name = self.castle.get_room(encounter.unlocks_room).name
            self._log(f"★ {room_name} is now accessible.")

        self.sound.play_sfx("ambient_explore")
        self.scene = "encounter"

        # Check win/lose immediately
        if self.player.is_alert_triggered():
            self._log("THE HUNTERS HAVE ARRIVED. Your time is up.")
            self.sound.play_sfx("game_over")
            self.scene = "game_over"
        elif self.player.blood <= 0:
            self._log("Your blood runs dry. You dissolve into the dark.")
            self.sound.play_sfx("game_over")
            self.scene = "game_over"

    # ── Encounter scene ───────────────────────────────────────────────────────

    def _draw_encounter(self) -> None:
        enc = self.active_encounter
        if enc is None:
            self.scene = "explore"
            return

        from items import ITEMS
        RARITY_COLORS = {"common": (160, 155, 185), "rare": (80, 150, 230), "legendary": GOLD}

        self.screen.fill((5, 0, 12))
        draw_gothic_border(self.screen, pygame.Rect(10, 10, MAP_W - 20, H - 20), BORDER, 2)

        # Header
        header = self.font_small.render("OUTSIDE ENCOUNTER", True, MUTED)
        self.screen.blit(header, (30, 22))
        draw_pixel_text(self.screen, self.font_title, enc.title, 30, 44, GOLD, shadow=True)

        # Atmospheric description box
        pygame.draw.rect(self.screen, (20, 13, 35), (20, 96, MAP_W - 40, 130), border_radius=6)
        pygame.draw.rect(self.screen, BORDER, (20, 96, MAP_W - 40, 130), 1, border_radius=6)
        desc_lines = textwrap.wrap(enc.description, width=62)
        for i, line in enumerate(desc_lines[:5]):
            surf = self.font_body.render(line, True, WHITE)
            self.screen.blit(surf, (34, 104 + i * 22))

        # Outcome text
        pygame.draw.line(self.screen, BORDER, (20, 240), (MAP_W - 20, 240), 1)
        out_lines = textwrap.wrap(enc.outcome, width=62)
        for i, line in enumerate(out_lines[:3]):
            surf = self.font_body.render(line, True, (210, 200, 230))
            self.screen.blit(surf, (30, 250 + i * 22))

        # Rewards panel
        pygame.draw.rect(self.screen, (18, 12, 30), (20, 330, MAP_W - 40, 200), border_radius=6)
        pygame.draw.rect(self.screen, BORDER, (20, 330, MAP_W - 40, 200), 1, border_radius=6)
        rew_label = self.font_ui_b.render("What you found:", True, MUTED)
        self.screen.blit(rew_label, (34, 340))

        ry = 364
        if enc.blood_reward > 0:
            s = self.font_body.render(f"  + {enc.blood_reward} Blood", True, BLOOD_LIGHT)
            self.screen.blit(s, (34, ry)); ry += 26
        elif enc.blood_reward < 0:
            s = self.font_body.render(f"  - {abs(enc.blood_reward)} Blood", True, (220, 80, 80))
            self.screen.blit(s, (34, ry)); ry += 26

        if enc.xp_reward > 0:
            s = self.font_body.render(f"  + {enc.xp_reward} XP", True, PURPLE)
            self.screen.blit(s, (34, ry)); ry += 26

        if enc.suspicion_change > 0:
            s = self.font_body.render(f"  + {enc.suspicion_change} Suspicion", True, (220, 100, 60))
            self.screen.blit(s, (34, ry)); ry += 26
        elif enc.suspicion_change < 0:
            s = self.font_body.render(f"  - {abs(enc.suspicion_change)} Suspicion", True, GREEN)
            self.screen.blit(s, (34, ry)); ry += 26

        if enc.item_id:
            item = ITEMS.get(enc.item_id)
            if item:
                col = RARITY_COLORS.get(item.rarity, WHITE)
                s = self.font_body.render(f"  Item: [{item.rarity.upper()}] {item.name}", True, col)
                self.screen.blit(s, (34, ry)); ry += 26
                fl = self.font_small.render(f"  {item.description}", True, MUTED)
                self.screen.blit(fl, (34, ry)); ry += 20

        if enc.recruitable_npc_id:
            from encounters import ENCOUNTER_NPC_NAMES
            npc_name = ENCOUNTER_NPC_NAMES.get(enc.recruitable_npc_id, "A new ally")
            s = self.font_body.render(f"  New ally: {npc_name}", True, (100, 190, 240))
            self.screen.blit(s, (34, ry)); ry += 26
            fl = self.font_small.render("  They have traveled to the Castle Gate.", True, MUTED)
            self.screen.blit(fl, (34, ry)); ry += 20

        if enc.unlocks_room >= 0:
            room_name = self.castle.get_room(enc.unlocks_room).name
            s = self.font_body.render(f"  Unlocked: {room_name}", True, GREEN)
            self.screen.blit(s, (34, ry)); ry += 26
            fl = self.font_small.render("  A new area of the castle is now accessible.", True, MUTED)
            self.screen.blit(fl, (34, ry)); ry += 20

        if (enc.blood_reward == 0 and enc.xp_reward == 0 and enc.suspicion_change == 0
                and not enc.item_id and not enc.recruitable_npc_id and enc.unlocks_room < 0):
            s = self.font_body.render("  Nothing. The night gave nothing.", True, MUTED)
            self.screen.blit(s, (34, ry))

        # Next venture timer hint
        mins_left = int(VENTURE_COOLDOWN // 60)
        timer_hint = self.font_small.render(
            f"Next venture available in {mins_left} minutes.", True, MUTED)
        self.screen.blit(timer_hint, (30, H - 60))

        cont = self.font_ui.render("[ SPACE / ENTER ] Return to castle", True, MUTED)
        self.screen.blit(cont, (30, H - 36))

    # ── Item pickup ───────────────────────────────────────────────────────────

    def _try_pickup_item(self, element: dict) -> None:
        """If element has an uncollected item, add it to player inventory."""
        item_id = element.get("item_id")
        if not item_id or element.get("item_taken", False):
            return
        from items import ITEMS
        item = ITEMS.get(item_id)
        if item and item.id not in self.player.item_ids:
            msg = self.player.add_item(item)
            element["item_taken"] = True
            self._log(msg)
            self.sound.play_sfx("success")

    # ── Inventory scene ───────────────────────────────────────────────────────

    def _draw_inventory(self) -> None:
        RARITY_COLORS = {
            "common":    (160, 155, 185),
            "rare":      (80,  150, 230),
            "legendary": GOLD,
        }

        pygame.draw.rect(self.screen, PANEL_BG, (0, 0, MAP_W, H))
        draw_gothic_border(self.screen, pygame.Rect(0, 0, MAP_W, H), BORDER, 2)
        draw_pixel_text(self.screen, self.font_title, "Inventory", 30, 14, GOLD, shadow=True)

        count_surf = self.font_ui.render(
            f"{len(self.player.inventory)} relic{'s' if len(self.player.inventory) != 1 else ''} carried",
            True, MUTED)
        self.screen.blit(count_surf, (30, 50))

        if not self.player.inventory:
            empty = self.font_body.render(
                "Your inventory is empty. Examine rooms to uncover relics.", True, MUTED)
            self.screen.blit(empty, (30, 100))
        else:
            y = 72
            for item in self.player.inventory:
                color = RARITY_COLORS.get(item.rarity, WHITE)
                flavor_lines = textwrap.wrap(item.flavor, width=64)
                card_h = 68 + (18 if len(flavor_lines) > 1 else 0)

                pygame.draw.rect(self.screen, (25, 18, 40),
                                 (20, y, MAP_W - 40, card_h), border_radius=6)
                pygame.draw.rect(self.screen, color,
                                 (20, y, MAP_W - 40, card_h), 1, border_radius=6)

                # Rarity strip on left edge
                pygame.draw.rect(self.screen, color, (20, y, 4, card_h), border_radius=2)

                # Name + rarity badge
                badge = self.font_ui_b.render(
                    f"[{item.rarity.upper()}]  {item.name}", True, color)
                self.screen.blit(badge, (34, y + 8))

                # Effect description
                eff = self.font_small.render(item.description, True, WHITE)
                self.screen.blit(eff, (34, y + 30))

                # Flavor (up to 2 lines)
                for j, line in enumerate(flavor_lines[:2]):
                    flav = self.font_small.render(line, True, MUTED)
                    self.screen.blit(flav, (34, y + 48 + j * 16))

                y += card_h + 6
                if y > H - 50:
                    more = self.font_small.render("▼ more items below", True, MUTED)
                    self.screen.blit(more, (MAP_W // 2 - more.get_width() // 2, H - 48))
                    break

        pygame.draw.line(self.screen, BORDER, (10, H - 40), (MAP_W - 10, H - 40), 1)
        esc = self.font_ui.render("[I / ESC] Close", True, MUTED)
        self.screen.blit(esc, (MAP_W // 2 - esc.get_width() // 2, H - 26))

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _draw_sidebar(self) -> None:
        sx = MAP_W
        pygame.draw.rect(self.screen, (16, 10, 28), (sx, 0, SIDEBAR_W, H))
        pygame.draw.line(self.screen, BORDER, (sx, 0), (sx, H), 1)

        # Player name
        name_surf = self.font_ui_b.render(self.player_name, True, GOLD)
        self.screen.blit(name_surf, (sx + 14, 2))

        # Blood bar
        blood_label = self.font_ui_b.render("BLOOD", True, BLOOD_LIGHT)
        self.screen.blit(blood_label, (sx + 14, 16))
        pct = self.player.blood / self.player.max_blood
        pygame.draw.rect(self.screen, (40, 20, 28), (sx + 14, 38, SIDEBAR_W - 28, 18), border_radius=4)
        if pct > 0:
            pygame.draw.rect(self.screen, BLOOD_RED, (sx + 14, 38, int((SIDEBAR_W - 28) * pct), 18), border_radius=4)
        blood_num = self.font_small.render(f"{self.player.blood}/{self.player.max_blood}", True, WHITE)
        self.screen.blit(blood_num, (sx + 14, 60))

        # Suspicion bar
        susp_label = self.font_ui_b.render("SUSPICION", True, self.player.suspicion_color())
        self.screen.blit(susp_label, (sx + 14, 88))
        spct = self.player.castle_suspicion / 100
        pygame.draw.rect(self.screen, (40, 30, 20), (sx + 14, 110, SIDEBAR_W - 28, 18), border_radius=4)
        if spct > 0:
            pygame.draw.rect(self.screen, self.player.suspicion_color(),
                             (sx + 14, 110, int((SIDEBAR_W - 28) * spct), 18), border_radius=4)
        susp_num = self.font_small.render(f"{self.player.castle_suspicion}/100  —  {self.player.suspicion_label()}", True, self.player.suspicion_color())
        self.screen.blit(susp_num, (sx + 14, 132))

        # Court count + Level + XP bar
        court_label = self.font_ui_b.render(f"COURT: {len(self.player.court)}", True, GOLD)
        self.screen.blit(court_label, (sx + 14, 162))

        xp_label = self.font_ui_b.render(f"LEVEL {self.abilities.level}", True, PURPLE)
        self.screen.blit(xp_label, (sx + 14, 182))
        xp_pct = self.abilities.xp_progress()
        pygame.draw.rect(self.screen, (30, 20, 50), (sx + 14, 200, SIDEBAR_W - 28, 12), border_radius=3)
        if xp_pct > 0:
            pygame.draw.rect(self.screen, PURPLE, (sx + 14, 200, int((SIDEBAR_W - 28) * xp_pct), 12), border_radius=3)
        xp_num = self.font_small.render(f"XP to next: {self.abilities.xp_to_next()}", True, MUTED)
        self.screen.blit(xp_num, (sx + 14, 216))

        # Quest count hint
        active_q = self.quests.active_count()
        unclaimed_q = self.quests.unclaimed_count()
        if unclaimed_q > 0:
            q_label = f"[Q] Quests — {unclaimed_q} reward{'s' if unclaimed_q > 1 else ''}!"
            q_color = GREEN
        elif active_q > 0:
            q_label = f"[Q] Quests ({active_q} active)"
            q_color = GOLD
        else:
            q_label = "[Q] Quests"
            q_color = MUTED
        q_surf = self.font_small.render(q_label, True, q_color)
        self.screen.blit(q_surf, (sx + 14, 234))

        # Item count hint
        item_count = len(self.player.inventory)
        if item_count > 0:
            i_label = f"[I] Items ({item_count})"
            i_color = (160, 155, 200)
        else:
            i_label = "[I] Inventory"
            i_color = MUTED
        i_surf = self.font_small.render(i_label, True, i_color)
        self.screen.blit(i_surf, (sx + 14, 252))

        # Divider
        pygame.draw.line(self.screen, BORDER, (sx + 10, 186), (W - 10, 186), 1)

        # Event log
        log_label = self.font_ui_b.render("EVENT LOG", True, MUTED)
        self.screen.blit(log_label, (sx + 14, 194))
        for i, line in enumerate(self.event_log[-16:]):
            color = WHITE if i >= len(self.event_log[-16:]) - 2 else MUTED
            surf = self.font_small.render(line, True, color)
            self.screen.blit(surf, (sx + 14, 214 + i * 18))