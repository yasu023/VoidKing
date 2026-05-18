"""Verify Python environment and pygame installation."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")

    try:
        from pygame_bootstrap import init_pygame

        pygame = init_pygame()
        pygame.init()
        print(f"pygame: {pygame.version.ver} ({pygame.get_sdl_version()})")
        if pygame.font.get_init() or True:
            pygame.font.init()
            f = pygame.font.SysFont("Arial", 14)
            print(f"font probe: {f is not None}")
        pygame.display.init()
        surf = pygame.display.set_mode((320, 200))
        pygame.display.flip()
        pygame.quit()
        print("OK: display smoke test passed")
        return 0
    except SystemExit as e:
        print(e)
        return 1
    except Exception as e:
        print(f"FAIL: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
