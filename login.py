"""
login.py — Login/Register screen for Vampire Castle.

Stores user credentials in users.json (hashed passwords).
Displays before the game starts.
"""

import pygame
import json
import hashlib
import os

# Path to user data file, stored next to this script
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# Colours matching the game palette
BG         = (8,  4, 16)
PANEL_BG   = (22, 14, 35)
BORDER     = (90, 55, 120)
BORDER_ACT = (160, 100, 220)   # active field border
WHITE      = (230, 225, 240)
MUTED      = (130, 120, 155)
GOLD       = (200, 170, 80)
BLOOD_RED  = (180, 30, 40)
GREEN      = (80, 200, 100)
ERROR_COL  = (220, 80, 80)


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class LoginScreen:
    """
    Handles the pre-game login/register screen.
    Call handle_events() + draw() in a loop until .done is True,
    then read .logged_in_user for the player name.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.W, self.H = screen.get_size()

        # Fonts
        self.font_title = pygame.font.SysFont("Georgia", 52, bold=True)
        self.font_sub    = pygame.font.SysFont("Georgia", 22)
        self.font_label  = pygame.font.SysFont("Georgia", 18, bold=True)
        self.font_input  = pygame.font.SysFont("Courier New", 20)
        self.font_btn    = pygame.font.SysFont("Arial",   18, bold=True)
        self.font_small  = pygame.font.SysFont("Georgia", 14)

        # Input state
        self.username = ""
        self.password = ""
        self.active   = "username"   # which field is focused

        # Message shown below the buttons
        self.message      = ""
        self.message_ok   = False    # True = green, False = red

        # Result
        self.done            = False
        self.logged_in_user  = ""

        # Cursor blink
        self.cursor_tick = 0

        # Decorative particles (simple floating dots)
        import random
        self.particles = [
            {"x": random.randint(0, self.W),
             "y": random.randint(0, self.H),
             "vy": random.uniform(-0.3, -0.8),
             "alpha": random.randint(40, 140)}
            for _ in range(60)
        ]

    # ── Public interface ─────────────────────────────────────────────────────

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                self._handle_key(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos)

    def draw(self) -> None:
        self.cursor_tick += 1
        self._update_particles()

        # Background
        self.screen.fill(BG)
        self._draw_particles()

        # Centre panel
        pw, ph = 480, 460
        px = self.W // 2 - pw // 2
        py = self.H // 2 - ph // 2

        pygame.draw.rect(self.screen, PANEL_BG, (px, py, pw, ph), border_radius=10)
        pygame.draw.rect(self.screen, BORDER,   (px, py, pw, ph), 2, border_radius=10)

        # Title
        title = self.font_title.render("VAMPIRE CASTLE", True, GOLD)
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, py + 24))

        sub = self.font_sub.render("Reclaim your throne", True, MUTED)
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, py + 84))

        # Divider
        pygame.draw.line(self.screen, BORDER,
                         (px + 30, py + 116), (px + pw - 30, py + 116), 1)

        # Username field
        uy = py + 140
        self._draw_field("Username", self.username, px + 40, uy, pw - 80,
                         self.active == "username")

        # Password field (show dots)
        passy = py + 226
        self._draw_field("Password", "*" * len(self.password), px + 40, passy, pw - 80,
                         self.active == "password")

        # Buttons
        btn_y = py + 316
        self._draw_button("LOGIN",    px + 40,          btn_y, 180, 48, GOLD)
        self._draw_button("REGISTER", px + pw - 220,    btn_y, 180, 48, (130, 80, 200))

        # Message
        if self.message:
            col = GREEN if self.message_ok else ERROR_COL
            msg_surf = self.font_label.render(self.message, True, col)
            self.screen.blit(msg_surf, (self.W // 2 - msg_surf.get_width() // 2, btn_y + 62))

        # Hint
        hint = self.font_small.render("TAB to switch fields   ENTER to login", True, MUTED)
        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, py + ph - 28))

    # ── Input handling ───────────────────────────────────────────────────────

    def _handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_TAB:
            self.active = "password" if self.active == "username" else "username"

        elif event.key == pygame.K_RETURN:
            self._try_login()

        elif event.key == pygame.K_BACKSPACE:
            if self.active == "username":
                self.username = self.username[:-1]
            else:
                self.password = self.password[:-1]

        elif event.unicode and event.unicode.isprintable():
            if self.active == "username" and len(self.username) < 24:
                self.username += event.unicode
            elif self.active == "password" and len(self.password) < 32:
                self.password += event.unicode

    def _handle_click(self, pos: tuple) -> None:
        pw, ph = 480, 460
        px = self.W // 2 - pw // 2
        py = self.H // 2 - ph // 2

        # Field click detection
        if px + 40 <= pos[0] <= px + pw - 40:
            if py + 155 <= pos[1] <= py + 203:
                self.active = "username"
            elif py + 241 <= pos[1] <= py + 289:
                self.active = "password"

        # Button click detection
        btn_y = py + 316
        if px + 40 <= pos[0] <= px + 220 and btn_y <= pos[1] <= btn_y + 48:
            self._try_login()
        elif px + pw - 220 <= pos[0] <= px + pw - 40 and btn_y <= pos[1] <= btn_y + 48:
            self._try_register()

    # ── Auth logic ───────────────────────────────────────────────────────────

    def _try_login(self) -> None:
        username = self.username.strip()
        password = self.password

        if not username or not password:
            self._set_message("Please fill in both fields.", ok=False)
            return

        users = _load_users()

        if username not in users:
            self._set_message("No account found. Click REGISTER to create one.", ok=False)
            return

        if users[username] != _hash(password):
            self._set_message("Incorrect password.", ok=False)
            return

        # Success!
        self.logged_in_user = username
        self.done = True
        self._set_message(f"Welcome back, {username}!", ok=True)

    def _try_register(self) -> None:
        username = self.username.strip()
        password = self.password

        if not username:
            self._set_message("Enter a username.", ok=False)
            return

        if len(username) < 3:
            self._set_message("Username must be at least 3 characters.", ok=False)
            return

        if not password or len(password) < 4:
            self._set_message("Password must be at least 4 characters.", ok=False)
            return

        users = _load_users()

        if username in users:
            self._set_message("That username is already taken.", ok=False)
            return

        # Create account
        users[username] = _hash(password)
        _save_users(users)

        self.logged_in_user = username
        self.done = True
        self._set_message(f"Account created! Welcome, {username}!", ok=True)

    def _set_message(self, text: str, ok: bool) -> None:
        self.message    = text
        self.message_ok = ok

    # ── Drawing helpers ──────────────────────────────────────────────────────

    def _draw_field(self, label: str, value: str, x: int, y: int,
                    width: int, active: bool) -> None:
        border_col = BORDER_ACT if active else BORDER

        lbl = self.font_label.render(label, True, GOLD if active else MUTED)
        self.screen.blit(lbl, (x, y))

        # Box
        box_y = y + 22
        pygame.draw.rect(self.screen, (14, 9, 25), (x, box_y, width, 36), border_radius=5)
        pygame.draw.rect(self.screen, border_col, (x, box_y, width, 36), 2, border_radius=5)

        # Text + cursor
        cursor_visible = active and (self.cursor_tick // 30) % 2 == 0
        display = value + ("|" if cursor_visible else "")
        txt = self.font_input.render(display, True, WHITE)
        # Clip long text from the right
        clip_rect = pygame.Rect(x + 8, box_y + 4, width - 16, 28)
        self.screen.set_clip(clip_rect)
        self.screen.blit(txt, (x + 8, box_y + 8))
        self.screen.set_clip(None)

    def _draw_button(self, label: str, x: int, y: int,
                     w: int, h: int, color: tuple) -> None:
        mouse = pygame.mouse.get_pos()
        hovered = x <= mouse[0] <= x + w and y <= mouse[1] <= y + h
        fill = tuple(min(255, c + 30) for c in color) if hovered else (22, 14, 35)

        pygame.draw.rect(self.screen, fill, (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, color, (x, y, w, h), 2, border_radius=6)

        lbl = self.font_btn.render(label, True, color)
        self.screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2,
                                y + h // 2 - lbl.get_height() // 2))

    # ── Particles ────────────────────────────────────────────────────────────

    def _update_particles(self) -> None:
        for p in self.particles:
            p["y"] += p["vy"]
            if p["y"] < -5:
                import random
                p["y"] = self.H + 5
                p["x"] = random.randint(0, self.W)

    def _draw_particles(self) -> None:
        for p in self.particles:
            surf = pygame.Surface((3, 3), pygame.SRCALPHA)
            surf.fill((200, 170, 80, p["alpha"]))
            self.screen.blit(surf, (int(p["x"]), int(p["y"])))
