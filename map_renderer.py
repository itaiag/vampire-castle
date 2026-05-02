"""
map_renderer.py — Castle map overlay (19 rooms total).

Draws all rooms as nodes, connections as lines,
colours rooms by status (unvisited / visited / claimed / hostile).
Press M to open/close.
"""

import pygame


# Room positions on the map canvas (x, y) — laid out to match the castle structure
# Reorganized by level: bottom (0-4), dungeon (5), mid (6-9), upper (10-15), top (16-17), special (18-19)
ROOM_POSITIONS = {
    0: (400, 600),   # Castle Gate       (bottom centre, outside entrance)
    1: (400, 480),   # Grand Entrance    (bottom centre)
    2: (560, 600),   # Moonlit Cemetery  (bottom right, outside)
    3: (240, 600),   # Old Forge         (bottom left, outside)
    4: (550, 180),   # Velvet Chamber    (near gallery, private room)
    5: (240, 480),   # Dungeon Wing      (bottom left, below kitchens)
    6: (240, 340),   # Old Kitchens      (middle left)
    7: (560, 340),   # Chapel            (middle right)
    8: (240, 380),   # Guard Barracks    (left mid-low)
    9: (120, 340),   # Servants' Quarters (far left)
    10: (400, 200),  # Upper Gallery     (centre hub)
    11: (240, 200),  # Great Library     (left upper)
    12: (560, 200),  # Alchemist's Lab   (right upper)
    13: (560, 60),   # East Tower        (top right)
    14: (500, 250),  # Winter Garden     (upper right of gallery)
    15: (80,  480),  # Ancient Catacombs (left, ancestral underground)
    16: (400, 60),   # Throne Room       (very top centre)
    17: (400, 100),  # Inner Sanctum     (very top, below throne)
    18: (680, 340),  # Treasury          (far right)
    19: (680, 220),  # Forgotten Vault   (secret, above Treasury)
}

CONNECTIONS = [
    (0, 1),   # Gate <-> Entrance
    (0, 2),   # Gate <-> Cemetery
    (0, 3),   # Gate <-> Forge
    (1, 6),   # Entrance <-> Kitchens
    (1, 7),   # Entrance <-> Chapel
    (1, 10),  # Entrance <-> Gallery
    (4, 14),  # Velvet <-> Garden
    (4, 16),  # Velvet <-> Throne
    (5, 8),   # Dungeon <-> Barracks
    (5, 13),  # Dungeon <-> Tower
    (5, 15),  # Dungeon <-> Catacombs
    (6, 8),   # Kitchens <-> Barracks
    (6, 9),   # Kitchens <-> Servants
    (6, 11),  # Kitchens <-> Library
    (7, 12),  # Chapel <-> Lab
    (7, 18),  # Chapel <-> Treasury
    (8, 11),  # Barracks <-> Library
    (9, 11),  # Servants <-> Library
    (10, 12), # Gallery <-> Lab
    (10, 14), # Gallery <-> Garden
    (10, 17), # Gallery <-> Sanctum
    (11, 17), # Library <-> Sanctum
    (12, 13), # Lab <-> Tower
    (12, 18), # Lab <-> Treasury
    (16, 17), # Throne <-> Sanctum
    (18, 19), # Treasury <-> Vault
]

# Secret passage (shown only if Mira is in court)
SECRET_CONNECTION = (6, 16)   # Kitchens <-> Throne Room hidden passage

NODE_RADIUS = 36
FONT_NAME   = "Georgia"


class MapRenderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_title = pygame.font.SysFont(FONT_NAME, 15, bold=True)
        self.font_small = pygame.font.SysFont(FONT_NAME, 12)

    def draw(self, castle, player, visited_rooms: set) -> None:
        W, H = self.screen.get_size()

        # Dark translucent overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((8, 4, 18, 220))
        self.screen.blit(overlay, (0, 0))

        # Title
        title_font = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        title = title_font.render("Castle Map", True, (200, 170, 80))
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 20))

        hint = self.font_small.render("[M] Close map", True, (100, 90, 120))
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, 56))

        # Offset so map is centred on screen
        ox = W // 2 - 400
        oy = H // 2 - 270

        # Check if secret passage is unlocked (Mira is in court)
        from npc import NPCRole
        secret_unlocked = any(n.role == NPCRole.SERVANT and n.is_controllable() for n in player.court)

        # Draw connections
        for a, b in CONNECTIONS:
            self._draw_connection(a, b, ox, oy, dashed=False)

        if secret_unlocked:
            self._draw_connection(*SECRET_CONNECTION, ox, oy, dashed=True)

        # Draw room nodes
        for room_idx, room in enumerate(castle.rooms):
            pos = ROOM_POSITIONS[room_idx]
            cx = pos[0] + ox
            cy = pos[1] + oy

            visited   = room_idx in visited_rooms
            is_current = room_idx == player.current_room

            npcs_here   = castle.get_npcs_in_room(room_idx)
            has_hostile = any(n.is_hostile() for n in npcs_here)
            has_claimed = any(n.is_controllable() for n in npcs_here)
            has_neutral = any(not n.is_controllable() and not n.is_hostile() for n in npcs_here)

            # Node fill colour
            if not visited and not is_current:
                fill   = (25, 18, 40)
                border = (60, 45, 80)
                label_color = (60, 50, 80)
            elif has_hostile:
                fill   = (60, 15, 15)
                border = (200, 50, 50)
                label_color = (220, 100, 80)
            elif has_claimed and not has_neutral and not has_hostile:
                fill   = (15, 40, 60)
                border = (60, 160, 220)
                label_color = (100, 190, 240)
            elif has_claimed:
                fill   = (30, 20, 55)
                border = (130, 80, 200)
                label_color = (170, 130, 220)
            else:
                fill   = (30, 22, 48)
                border = (110, 85, 150)
                label_color = (180, 165, 210)

            # Current room pulse ring
            if is_current:
                pygame.draw.circle(self.screen, (200, 170, 80), (cx, cy), NODE_RADIUS + 8, 2)

            # Node circle
            pygame.draw.circle(self.screen, fill,   (cx, cy), NODE_RADIUS)
            pygame.draw.circle(self.screen, border, (cx, cy), NODE_RADIUS, 2)

            # Room name
            name = castle.rooms[room_idx].name
            # Shorten long names to fit
            short_names = {
                "The Grand Entrance": "Entrance",
                "The Old Kitchens":   "Kitchens",
                "The Chapel":         "Chapel",
                "The Upper Gallery":  "Gallery",
                "The Throne Room":    "Throne Room",
                "The Dungeon Wing":   "Dungeon",
                "The Alchemist's Laboratory": "Lab",
                "The East Tower":     "Tower",
                "The Great Library":  "Library",
                "The Inner Sanctum":  "Sanctum",
                "The Guard Barracks": "Barracks",
                "The Servants' Quarters": "Servants",
                "The Treasury":       "Treasury",
                "The Winter Garden":  "Garden",
                "The Forgotten Vault": "Vault???",
                "The Moonlit Cemetery": "Cemetery",
                "The Old Forge":       "Forge",
                "The Ancient Catacombs": "Catacombs",
                "The Velvet Chamber":  "Chamber",
            }
            display_name = short_names.get(name, name)

            if visited or is_current:
                name_surf = self.font_title.render(display_name, True, label_color)
                self.screen.blit(name_surf, (cx - name_surf.get_width() // 2, cy - 10))

                # NPC status icons below name
                icon_x = cx - len(npcs_here) * 10
                for npc in npcs_here:
                    color = npc.status_color() if visited or is_current else (50, 40, 65)
                    pygame.draw.circle(self.screen, color, (icon_x, cy + 16), 6)
                    icon_x += 20
            else:
                # Unvisited — show "???"
                unk = self.font_title.render("???", True, (50, 40, 65))
                self.screen.blit(unk, (cx - unk.get_width() // 2, cy - 8))

            # "YOU ARE HERE" marker
            if is_current:
                you = self.font_small.render("YOU", True, (200, 170, 80))
                self.screen.blit(you, (cx - you.get_width() // 2, cy + 26))

        # Legend
        self._draw_legend(W, H)

    def _draw_connection(self, a: int, b: int, ox: int, oy: int, dashed: bool) -> None:
        ax = ROOM_POSITIONS[a][0] + ox
        ay = ROOM_POSITIONS[a][1] + oy
        bx = ROOM_POSITIONS[b][0] + ox
        by = ROOM_POSITIONS[b][1] + oy

        color = (80, 60, 120) if not dashed else (100, 60, 160)

        if dashed:
            # Draw dashed line
            import math
            dx, dy = bx - ax, by - ay
            dist = math.hypot(dx, dy)
            steps = int(dist / 14)
            for i in range(steps):
                t0 = i / steps
                t1 = (i + 0.5) / steps
                x0 = int(ax + dx * t0)
                y0 = int(ay + dy * t0)
                x1 = int(ax + dx * t1)
                y1 = int(ay + dy * t1)
                pygame.draw.line(self.screen, color, (x0, y0), (x1, y1), 1)
            # Label
            mx = (ax + bx) // 2
            my = (ay + by) // 2
            sec = self.font_small.render("secret", True, (100, 60, 160))
            self.screen.blit(sec, (mx - sec.get_width() // 2, my - 8))
        else:
            pygame.draw.line(self.screen, color, (ax, ay), (bx, by), 2)

    def _draw_legend(self, W: int, H: int) -> None:
        items = [
            ((60, 160, 220),  "Fully claimed"),
            ((130, 80, 200),  "Partially claimed"),
            ((110, 85, 150),  "Visited, neutral"),
            ((200, 50,  50),  "Hostile NPC"),
            ((60,  45,  80),  "Unvisited"),
            ((200, 170, 80),  "You are here"),
        ]
        lx = W - 200
        ly = H - 160
        bg = pygame.Surface((185, len(items) * 24 + 16), pygame.SRCALPHA)
        bg.fill((15, 10, 28, 200))
        self.screen.blit(bg, (lx - 8, ly - 8))

        for i, (color, label) in enumerate(items):
            pygame.draw.circle(self.screen, color, (lx + 8, ly + i * 24 + 8), 7)
            surf = self.font_small.render(label, True, (160, 150, 180))
            self.screen.blit(surf, (lx + 22, ly + i * 24))
