
"""
Vampire Castle — main entry point.
Run:  python main.py
Requires: pip install pygame
"""

import pygame
from game import Game
from login import LoginScreen

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Vampire Castle")
    clock = pygame.time.Clock()

    # ── Login screen ──────────────────────────────────────────────────────────
    login = LoginScreen(screen)
    while not login.done:
        login.handle_events()
        login.draw()
        pygame.display.flip()
        clock.tick(60)

    # ── Game ─────────────────────────────────────────────────────────────────
    game = Game(screen, player_name=login.logged_in_user)

    while True:
        dt = clock.tick(60) / 1000.0
        game.handle_events()
        game.update(dt)
        game.draw()
        pygame.display.flip()

if __name__ == "__main__":
    main()
