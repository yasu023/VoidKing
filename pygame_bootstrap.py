"""Import pygame from pygame-ce or standard pygame with a clear install hint."""


def init_pygame():
  """Return the pygame module or stop with an actionable dependency message."""
  try:
    import pygame  # noqa: F401 — pygame-ce provides the pygame module name
  except ImportError as exc:
    raise SystemExit(
      "Pygame is not installed.\n\n"
      "Install with standard Python (python.org), then run:\n"
      "  pip install -r requirements.txt\n\n"
      "On Windows, prefer:  py -3.12 -m pip install -r requirements.txt\n"
      "Avoid MSYS2 Python for pygame wheels.\n"
    ) from exc
  import pygame

  if not pygame.version.ver.startswith("2"):
    print(f"Warning: unexpected pygame version {pygame.version.ver}")
  return pygame
