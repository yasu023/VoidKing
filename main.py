"""Application entry point and high-level scene loop."""

import multiprocessing
import sys

from pygame_bootstrap import init_pygame

pygame = init_pygame()

from constants import FPS
from game import GameScene
from layout import AppLayout
from menu import Menu


def main():
    """Initialize Pygame, switch between menu/game scenes, and run frames."""
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        pass

    layout = AppLayout(AppLayout.DEFAULT_WIDTH, AppLayout.DEFAULT_HEIGHT)
    flags = pygame.RESIZABLE
    screen = pygame.display.set_mode((layout.width, layout.height), flags)
    pygame.display.set_caption("PyChess Professional")
    clock = pygame.time.Clock()

    menu = Menu(layout)
    game = None
    running = True

    def apply_resize(w, h):
        """Rebuild responsive layout and notify active scenes after resize."""
        nonlocal layout, screen
        layout = AppLayout(max(AppLayout.MIN_WIDTH, w), max(AppLayout.MIN_HEIGHT, h))
        screen = pygame.display.set_mode((layout.width, layout.height), flags)
        menu.on_resize(layout)
        if game is not None:
            game.on_resize(layout)
        return layout, screen

    while running:
        # Clamp very large frame deltas after pauses/window drags so animations
        # and AI polling resume smoothly instead of jumping forward.
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.05:
            dt = 1.0 / FPS

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.VIDEORESIZE:
                layout, screen = apply_resize(e.w, e.h)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not getattr(e, "repeat", False):
                if menu.start_game and game is None:
                    menu.start_game = False
                # In-game Esc is handled only in GameScene.handle_events to avoid double-toggle

        # Scene ownership is simple: Menu collects settings, GameScene owns the
        # live Board once play begins, and returning to menu discards that game.
        if not menu.start_game:
            menu.update(dt)
            menu.handle_events(events)
            menu.draw(screen)
        else:
            if game is None:
                game = GameScene(menu.get_settings(), layout)

            if game.request_main_menu:
                from ai import cancel_ai_search

                cancel_ai_search()
                menu.start_game = False
                game = None
            else:
                if game.settings.get("board_theme") != menu.board_theme:
                    game.settings["board_theme"] = menu.board_theme
                    game._invalidate_board_cache()
                game.update(dt)
                game.handle_events(events)
                game.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
