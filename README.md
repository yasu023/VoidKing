<p align="center">
  <img src="assets/screenshots/ChatGPT Image May 25, 2026, 09_29_46 PM.png" alt="VoidKing Chess AI Banner" width="100%">
</p>

<p align="center">
  Professional Chess Game with Minimax AI • Python • Pygame
</p>

<p align="center">
  <a href="https://github.com/yasu023/VoidKing/releases">
    <img src="https://img.shields.io/badge/Download-Windows%20EXE-blue?style=for-the-badge">
  </a>
</p>

<br>

# VoidKing Chess AI

A professional desktop chess game built with Python and Pygame featuring Minimax AI with Alpha-Beta pruning, advanced chess rules, responsive UI, smooth animations, and multiple gameplay modes.

---

## ✨ Features

* Full official chess rules

  * Castling
  * En passant
  * Promotion
  * Check / Checkmate
  * Draw detection
* Human vs Human
* Human vs AI
* Multiple AI difficulty levels
* Minimax AI with Alpha-Beta pruning
* Smooth piece animations
* Modern responsive UI
* Move highlighting
* Move history panel
* Captured pieces panel
* Board themes
* Sound effects
* Stable FPS and optimized rendering
* Threaded AI processing (no freezing)

---

## 🧠 AI System

The AI is implemented using:

* Minimax Algorithm
* Negamax Search
* Alpha-Beta Pruning
* Move Ordering
* Quiescence Search
* Piece-Square Tables (PST)
* Positional Evaluation Heuristics

The engine evaluates:

* Material balance
* Center control
* Piece activity
* King safety
* Tactical exchanges

---

## 🛠️ Requirements

* Python 3.10+
* Pygame CE

Recommended:

* Official Python installation from python.org
* Avoid MSYS2 / MinGW Python for pygame

---

## 📦 Installation

```bash
git clone https://github.com/yasu023/VoidKing.git
cd VoidKing

pip install -r requirements.txt
```

Windows recommended:

```bash
py -3.12 -m pip install -r requirements.txt
```

---

## ▶️ Run The Game

```bash
python main.py
```

---

## 🎮 Controls

| Key / Action  | Effect                |
| ------------- | --------------------- |
| Esc           | Pause menu            |
| Resume        | Continue game         |
| Restart       | Restart match         |
| Main Menu     | Return to menu        |
| Enter / Space | Start game            |
| Resize Window | Responsive UI scaling |

---

## ⚙️ Menu Options

* Player vs Player
* Player vs AI
* AI Difficulty Selection
* White / Black Side Selection
* Classic / Dark Board Themes

---

## 🧪 Tests

```bash
python tests/test_chess.py
```

---

## 🧱 Project Structure

| File           | Purpose                         |
| -------------- | ------------------------------- |
| `main.py`      | Entry point and main loop       |
| `menu.py`      | Main menu system                |
| `game.py`      | Gameplay controller             |
| `board.py`     | Chess rules and move validation |
| `ai.py`        | Minimax AI engine               |
| `move.py`      | Move representation             |
| `ui.py`        | UI components and buttons       |
| `layout.py`    | Responsive layout system        |
| `utils.py`     | Asset loading and helpers       |
| `constants.py` | Colors, themes, AI constants    |

---

## 🚀 Release

Download the latest Windows executable from:

👉 https://github.com/yasu023/VoidKing/releases

---

## 👨‍💻 Developed By

Yassin Khaled
