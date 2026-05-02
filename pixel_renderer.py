"""
pixel_renderer.py — Pixel art drawing system.

Draws everything in a 16-bit RPG style using only pygame primitives —
no image files required. All sprites are built from pixel grids.
"""

import pygame
import math

# ── Pixel sprite definitions (16x16 grids, 0=transparent) ────────────────────

VAMPIRE_SPRITE = [
    "....BBBB....",
    "...BBBBBB...",
    "...B1111B...",
    "...B1BB1B...",
    "...BBBBBB...",
    "....BBBB....",
    "..PPBBBBPP..",
    "..PPBBBBPP..",
    "..PP.BB.PP..",
    "...P.BB.P...",
    "...P....P...",
    "...P....P...",
]

# Generic role-based sprites
NPC_SPRITES = {
    "guard": [
        "....SSSS....",
        "...SSSSSS...",
        "...S1111S...",
        "...S1SS1S...",
        "...SSSSSS...",
        "....SSSS....",
        "..GGSSSSGG..",
        "..GGSSSSGG..",
        "..GG.SS.GG..",
        "...G.SS.G...",
        "...G....G...",
        "...G....G...",
    ],
    "servant": [
        "....WWWW....",
        "...WWWWWW...",
        "...W1111W...",
        "...W1WW1W...",
        "...WWWWWW...",
        "....WWWW....",
        "..AAWWWWAA..",
        "..AAWWWWAA..",
        "..AA.WW.AA..",
        "...A.WW.A...",
        "...A....A...",
        "...A....A...",
    ],
    "priest": [
        "....RRRR....",
        "...RRRRRR...",
        "...R1111R...",
        "...R1RR1R...",
        "...RRRRRR...",
        "....RRRR....",
        "..WWRRRRRR..",
        "..WWRRRRRR..",
        "..WW.RR.WW..",
        "...W.RR.W...",
        "...W....W...",
        "...W....W...",
    ],
    "noble": [
        "....VVVV....",
        "...VVVVVV...",
        "...V1111V...",
        "...V1VV1V...",
        "...VVVVVV...",
        "....VVVV....",
        "..PPVVVVPP..",
        "..PPVVVVPP..",
        "..PP.VV.PP..",
        "...P.VV.P...",
        "...P....P...",
        "...P....P...",
    ],
    "hunter": [
        "....BBBB....",
        "...BBBBBB...",
        "...B1111B...",
        "...B1BB1B...",
        "...BBBBBB...",
        "....BBBB....",
        "..RRBBBBGG..",
        "..RRBBBBGG..",
        "..RR.BB.GG..",
        "...R.BB.G...",
        "...R....G...",
        "...R....G...",
    ],
    "alchemist": [
        "....GGGG....",
        "...GGGGGG...",
        "...G1111G...",
        "...G1GG1G...",
        "...GGGGGG...",
        "....GGGG....",
        "..PPGGGGPP..",
        "..PPGGGGPP..",
        "..PP.GG.PP..",
        "...P.GG.P...",
        "...P....P...",
        "...P....P...",
    ],
    "celestine": [        # hooded spy — slim dark cloak, hood up, gold trim
        "...CCCCCC...",   # hood top
        "..CCCCCCCC..",   # hood brim
        "..CC1CC1CC..",   # face in hood shadow
        "..CC1CCC1C..",
        "..CCCCCCCI.",    # I = gold eye glint
        "...CCCCCC...",   # chin
        "..NNCCCCNN..",   # N = night-black cloak shoulders
        "..NNCCCCNN..",
        "..NN.CC.NN..",
        "...N.CC.N...",
        "...N....N...",
        "...N....N...",
    ],
}

# Unique NPC character portraits - COMPLETELY DIFFERENT from each other
NPC_PORTRAITS = {
    "aldric": [  # BIG BULKY GUARD - Wide, powerful stance, heavily armored
        "...........",
        ".SSSSSSSSS.",
        ".S.1...1.S.",
        ".S.XXXXX.S.",
        ".SSSXXXSSS.",
        ".SSSSSSSS..",
        "..GGGGGGG..",
        "..GGG.GGG..",
        "..GG...GG..",
        "..GG...GG..",
        ".GGG...GGG.",
        ".GGG...GGG.",
    ],
    "mira": [  # TINY DELICATE GIRL - Very small, thin, fragile looking
        "....WW....",
        "...WWWW...",
        "...W11W...",
        "...W1EW...",
        "....WW....",
        "...AAA....",
        "..AAA.AA..",
        "..AA...AA.",
        "...A...A..",
        "...A...A..",
        "..A.....A.",
        ".A.......A",
    ],
    "dorin": [  # OLD PRIEST - Bent over, frail, holding cross up high
        "......+...",
        ".....+++..",
        "...RRRR+..",
        "...R11R+..",
        "...RXXXR..",
        "..RRXXXR..",
        "..WRRRW...",
        ".WWW.W.W..",
        ".WW..W..W.",
        ".WW..W..W.",
        ".W...W...W",
        "......W...",
    ],
    "seraphine": [  # TALL ELEGANT NOBLE - Slender, long, graceful, standing tall
        ".....V....",
        "....VVV...",
        "...VVV1V..",
        "...V.1.V..",
        "....V1V...",
        "....VVV...",
        "...PPVVPP.",
        "..PPP.PPP.",
        "..PPP.PPP.",
        "...P...P..",
        "...P...P..",
        "...P...P..",
    ],
    "viktor": [  # MASSIVE MUSCULAR TORTURER - HUGE wide body, imposing
        ".....S....",
        "...SSSSSSS",
        "...S.X.XS.",
        "..SSS1X1S.",
        "..SS1XXX1S",
        "..SSX1X1XS",
        ".KKKGSGSKK",
        "KKKKKSGSKK",
        ".KKKK.S.KK",
        ".KK..GSG.K",
        ".KK..GSG.K",
        "..K..G.G..",
    ],
    "erasmus": [  # SHORT SCRAWNY ALCHEMIST - Tiny, thin, pointy hat, crooked
        "...HHHH...",
        "..HHHHHH..",
        "..HHGGGGG.",
        "..HG1G1G..",
        "..HG.G.G..",
        "....GGGGG.",
        "..PPG...G.",
        ".PPG..G...",
        ".PPG..G...",
        "..PG..G...",
        "....G.....",
        "....G.....",
    ],
    "isolde": [  # COMBAT READY HUNTER - Asymmetrical, armed, scarred, tense
        "...BBB....",
        "..BBBBB...",
        "..B.X.XB..",
        ".BBX1X1BB.",
        ".BB1XXX1B.",
        "..BXBXBX..",
        ".RRRB>BBG.",
        "RRRRB>B>G.",
        ".RRR.B..G.",
        ".RRR.B..G.",
        "..RR.B.GG.",
        "....B.GG..",
    ],
    "celestine": [  # SPY / SHADOW LADY — hooded, slim, gold-eyed, mysterious
        "...CCCCCC.",
        "..CCCCCCCC",
        "..CC.11.CC",
        "..CC1I11CC",    # I = gold eye glint
        "...CCIICC.",
        "....CCCC..",
        "..NNCCCCN.",
        ".NNNCCCCNN",
        ".NNN.CC.NN",
        "..NN.CC.N.",
        "..NN....N.",
        "...N....N.",
    ],
}

SPRITE_COLORS = {
    "B": (40, 20, 60),   # dark purple (vampire body)
    "P": (80, 40, 110),  # purple (vampire cape)
    "1": (220, 190, 160),  # skin
    "S": (100, 100, 110),  # steel (guard armour)
    "G": (120, 100, 60),  # gold/brown (guard legs / hunter)
    "W": (220, 210, 200),  # white (servant / priest robe)
    "A": (180, 160, 130),  # apron
    "R": (60, 40, 80),  # robe (priest)
    "V": (100, 60, 140),  # violet (noble)
    "X": (80, 60, 100),  # scars/battle marks
    "K": (60, 40, 80),  # dark leather/blood
    "+": (200, 200, 100),  # cross/gold
    ">": (180, 180, 180),  # crossbow/silver
    "<": (180, 180, 180),  # crossbow/silver
}

TILE_SIZE = 32  # each floor/wall tile is 32x32 pixels


# ── Tile drawing ──────────────────────────────────────────────────────────────

def draw_floor_tile(surf: pygame.Surface, x: int, y: int, tick: int) -> None:
    """Draw a stone floor tile with subtle variation."""
    base = (28, 20, 42)
    grout = (20, 14, 30)
    pygame.draw.rect(surf, base, (x, y, TILE_SIZE, TILE_SIZE))
    # Grout lines
    pygame.draw.line(surf, grout, (x, y), (x + TILE_SIZE, y), 1)
    pygame.draw.line(surf, grout, (x, y), (x, y + TILE_SIZE), 1)
    # Subtle stone crack pattern based on position
    seed = (x // TILE_SIZE * 7 + y // TILE_SIZE * 13) % 4
    if seed == 0:
        pygame.draw.line(surf, grout, (x + 8, y + 10), (x + 14, y + 18), 1)
    elif seed == 1:
        pygame.draw.line(surf, grout, (x + 20, y + 6), (x + 26, y + 12), 1)


def draw_wall_tile(surf: pygame.Surface, x: int, y: int) -> None:
    """Draw a stone wall tile."""
    base = (35, 25, 50)
    dark = (22, 16, 34)
    light = (50, 36, 68)
    pygame.draw.rect(surf, base, (x, y, TILE_SIZE, TILE_SIZE))
    # Brick pattern
    row = (y // TILE_SIZE) % 2
    for bx in range(0, TILE_SIZE, 16):
        offset = 8 if row == 1 else 0
        bx2 = (bx + offset) % TILE_SIZE
        pygame.draw.rect(surf, dark, (x + bx2, y, 1, TILE_SIZE))
    pygame.draw.line(surf, dark, (x, y + TILE_SIZE // 2), (x + TILE_SIZE, y + TILE_SIZE // 2), 1)
    pygame.draw.line(surf, light, (x, y), (x + TILE_SIZE, y), 1)
    pygame.draw.line(surf, light, (x, y), (x, y + TILE_SIZE), 1)


def draw_candle(surf: pygame.Surface, x: int, y: int, tick: int) -> None:
    """Draw a flickering candle."""
    flicker = math.sin(tick * 0.08 + x) * 3
    # Candle body
    pygame.draw.rect(surf, (220, 200, 160), (x + 3, y + 8, 6, 12))
    # Flame
    flame_h = int(8 + flicker)
    flame_col = (255, int(180 + flicker * 5), 40)
    pygame.draw.ellipse(surf, flame_col, (x + 2, y + 8 - flame_h, 8, flame_h))
    # Glow
    glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
    alpha = int(30 + flicker * 4)
    pygame.draw.circle(glow_surf, (255, 200, 80, alpha), (20, 20), 18)
    surf.blit(glow_surf, (x - 14, y - 10))


def draw_room_background(surf: pygame.Surface, room_w: int, room_h: int, tick: int,
                         candle_positions: list) -> None:
    """Draw a full tiled room with walls and floor."""
    # Floor tiles
    for ty in range(2, (room_h // TILE_SIZE) - 1):
        for tx in range(2, (room_w // TILE_SIZE) - 1):
            draw_floor_tile(surf, tx * TILE_SIZE, ty * TILE_SIZE, tick)

    # Wall tiles (top and sides)
    for tx in range(room_w // TILE_SIZE):
        draw_wall_tile(surf, tx * TILE_SIZE, 0)
        draw_wall_tile(surf, tx * TILE_SIZE, TILE_SIZE)
    for ty in range(room_h // TILE_SIZE):
        draw_wall_tile(surf, 0, ty * TILE_SIZE)
        draw_wall_tile(surf, room_w - TILE_SIZE, ty * TILE_SIZE)
    # Bottom wall
    for tx in range(room_w // TILE_SIZE):
        draw_wall_tile(surf, tx * TILE_SIZE, room_h - TILE_SIZE)

    # Candles
    for cx, cy in candle_positions:
        draw_candle(surf, cx, cy, tick)


# ── Sprite drawing ────────────────────────────────────────────────────────────

def draw_sprite(surf: pygame.Surface, sprite_grid: list, x: int, y: int,
                scale: int = 3, tint: tuple = None) -> None:
    """Draw a pixel sprite at (x, y) scaled up."""
    for row_idx, row in enumerate(sprite_grid):
        for col_idx, ch in enumerate(row):
            if ch == "." or ch == " ":
                continue
            color = SPRITE_COLORS.get(ch, (200, 200, 200))
            if tint:
                # Blend with tint color
                color = tuple(min(255, int(c * 0.7 + t * 0.3)) for c, t in zip(color, tint))
            px = x + col_idx * scale
            py = y + row_idx * scale
            pygame.draw.rect(surf, color, (px, py, scale, scale))


def draw_vampire_player(surf: pygame.Surface, x: int, y: int, tick: int,
                        scale: int = 3) -> None:
    """Draw the player vampire with a subtle cape flutter."""
    flutter = int(math.sin(tick * 0.1) * scale)
    draw_sprite(surf, VAMPIRE_SPRITE, x, y + flutter, scale)
    # Shadow
    shadow = pygame.Surface((40, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, 40, 8))
    surf.blit(shadow, (x + 2, y + len(VAMPIRE_SPRITE) * scale - 4))


def draw_npc_sprite(surf: pygame.Surface, role_key: str, x: int, y: int,
                    state_color: tuple, scale: int = 3) -> None:
    """Draw an NPC sprite with a state-coloured aura."""
    grid = NPC_SPRITES.get(role_key, NPC_SPRITES["servant"])
    # State aura
    aura = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(aura, (*state_color, 40), (30, 30), 28)
    surf.blit(aura, (x - 10, y - 10))
    draw_sprite(surf, grid, x, y, scale)
    # Shadow
    shadow = pygame.Surface((40, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 50), (0, 0, 40, 8))
    surf.blit(shadow, (x + 2, y + len(grid) * scale - 4))


def draw_npc_portrait(surf: pygame.Surface, npc_key: str, x: int, y: int,
                      state_color: tuple = None, scale: int = 4) -> None:
    """Draw a detailed NPC portrait at conversation size."""
    grid = NPC_PORTRAITS.get(npc_key)
    if grid is None:
        return

    # Background panel
    portrait_w = len(grid[0]) * scale + 4
    portrait_h = len(grid) * scale + 4
    pygame.draw.rect(surf, (20, 10, 30), (x - 2, y - 2, portrait_w, portrait_h))
    pygame.draw.rect(surf, (80, 50, 110), (x - 2, y - 2, portrait_w, portrait_h), 2)

    # Optional aura/state color
    if state_color:
        aura = pygame.Surface((portrait_w + 20, portrait_h + 20), pygame.SRCALPHA)
        pygame.draw.circle(aura, (*state_color, 30), (portrait_w // 2 + 10, portrait_h // 2 + 10), portrait_w // 2 + 8)
        surf.blit(aura, (x - 12, y - 12))

    # Draw the portrait
    draw_sprite(surf, grid, x, y, scale)


# ── UI pixel elements ─────────────────────────────────────────────────────────

def draw_gothic_border(surf: pygame.Surface, rect: pygame.Rect,
                       color: tuple = (80, 50, 110), thickness: int = 2) -> None:
    """Draw a gothic-style border with corner ornaments."""
    x, y, w, h = rect
    pygame.draw.rect(surf, color, rect, thickness)
    # Corner diamonds
    corner_size = 6
    for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
        points = [
            (cx, cy - corner_size),
            (cx + corner_size, cy),
            (cx, cy + corner_size),
            (cx - corner_size, cy),
        ]
        pygame.draw.polygon(surf, color, points)


def draw_blood_drops(surf: pygame.Surface, x: int, y: int,
                     filled: int, total: int, color: tuple = (180, 30, 40)) -> None:
    """Draw blood as a series of drop icons instead of a flat bar."""
    drop_w = 14
    for i in range(total):
        dx = x + i * (drop_w + 3)
        c = color if i < filled else (50, 20, 28)
        # Drop shape: circle + triangle
        pygame.draw.circle(surf, c, (dx + 7, y + 9), 6)
        pygame.draw.polygon(surf, c, [(dx + 7, y), (dx + 2, y + 8), (dx + 12, y + 8)])


def draw_pixel_text(surf: pygame.Surface, font: pygame.font.Font, text: str,
                    x: int, y: int, color: tuple, shadow: bool = True) -> None:
    """Draw text with an optional pixel shadow."""
    if shadow:
        shadow_surf = font.render(text, False, (0, 0, 0))
        surf.blit(shadow_surf, (x + 1, y + 1))
    text_surf = font.render(text, False, color)
    surf.blit(text_surf, (x, y))