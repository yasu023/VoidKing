# PyChess Professional

A production-ready chess game built with Python and Pygame CE. Full rule enforcement, responsive UI, minimax AI, and polished menus.

## Requirements

- **Python 3.10+** from [python.org](https://www.python.org/downloads/) (recommended on Windows)
- Avoid **MSYS2/MinGW Python** for pygame — wheels are unreliable there

## Installation

```bash
cd chess_game
pip install -r requirements.txt
```

Windows (recommended):

```bash
py -3.12 -m pip install -r requirements.txt
```

Verify your environment:

```bash
python scripts/check_env.py
```

## Run

```bash
python main.py
```

### Controls

| Key / action | Effect |
|--------------|--------|
| **Esc** (in game) | Pause menu |
| **Resume** | Continue game |
| **Restart** | New game |
| **Main Menu** | Return to menu |
| **Enter / Space** (menu) | Start game |
| Drag window edge | Resize (min 880×600) |

### Menu options

- **Player vs Player** / **Player vs AI**
- **You play: White / Black** (vs AI)
- **Difficulty** (AI depth 2–5)
- **Board theme**: Classic / Dark

## Features

- Complete chess rules (pins, castling, en passant, draws, etc.)
- Threaded AI (no UI freeze)
- Resizable window with adaptive layout
- Procedural piece/sound fallbacks when assets are missing

## Tests

```bash
python tests/test_chess.py
```

## Project layout

| File | Role |
|------|------|
| `main.py` | Main loop, resize, scene routing |
| `layout.py` | Responsive layout metrics |
| `menu.py` | Main menu |
| `game.py` | Gameplay, pause, panels |
| `board.py` | Rules and move generation |
| `ai.py` | Minimax engine |
| `pygame_bootstrap.py` | Safe pygame import |
| `constants.py` | Colors, themes, AI tables |

Optional: `assets/pieces/*.png`, `assets/sounds/*.wav`
