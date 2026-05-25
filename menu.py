"""Start menu scene for choosing mode, difficulty, color, and theme."""

import math

import pygame

from constants import (
    ACCENT,
    BG_COLOR,
    BOARD_THEME_ORDER,
    BOARD_THEMES,
    PANEL_BORDER,
    TEXT_COLOR,
    TEXT_DIM,
    TEXT_MUTED,
)
from layout import AppLayout
from ui import Button
from utils import clear_font_cache, draw_text, draw_text_shadow, get_font


class Menu:
    """Collects game settings before GameScene is created."""

    def __init__(self, layout):
        self.layout = layout
        self.mode_pvp = True
        self.human_color = "w"
        self.diffs = [(2, "Easy (2)"), (3, "Normal (3)"), (4, "Hard (4)"), (5, "Expert (5)")]
        self.diff_idx = 1
        self.board_theme = "classic"
        self.start_game = False
        self._time = 0.0
        self._bg_cache = None
        self._bg_size = None

        self.btn_start = Button(0, 0, 10, 10, "Start Game", get_font(18))
        self.btn_mode = Button(0, 0, 10, 10, "Mode: Player vs Player", get_font(18))
        self.btn_color = Button(0, 0, 10, 10, "You play: White", get_font(18))
        self.btn_diff = Button(0, 0, 10, 10, "Difficulty: Normal (3)", get_font(18))
        self.btn_theme = Button(0, 0, 10, 10, "Board: Classic", get_font(18))
        self._rebuild_fonts_and_layout()

    def on_resize(self, layout):
        """Recalculate fonts/layout and drop cached background after resize."""
        self.layout = layout
        self._bg_cache = None
        self._bg_size = None
        clear_font_cache()
        self._rebuild_fonts_and_layout()

    def _rebuild_fonts_and_layout(self):
        """Refresh button labels and rectangles from current settings."""
        L = self.layout
        self.font_title = get_font(L.font_title, bold=True)
        self.font_sub = get_font(L.font_sub)
        self.font_btn = get_font(L.font_btn)
        self.font_credit_label = get_font(max(11, int(12 * L.scale)))
        self.font_credit_name = get_font(max(13, int(14 * L.scale)), bold=True)

        for btn in (
            self.btn_start,
            self.btn_mode,
            self.btn_color,
            self.btn_diff,
            self.btn_theme,
        ):
            btn.font = self.font_btn

        self.btn_mode.text = "Mode: Player vs Player" if self.mode_pvp else "Mode: Player vs AI"
        self.btn_color.text = "You play: White" if self.human_color == "w" else "You play: Black"
        self.btn_diff.text = f"Difficulty: {self.diffs[self.diff_idx][1]}"
        self.btn_theme.text = f"Board: {BOARD_THEMES[self.board_theme]['label']}"

        self._layout_buttons()

    def get_settings(self):
        """Return the settings dictionary consumed by GameScene."""
        return {
            "pvp": self.mode_pvp,
            "ai_depth": self.diffs[self.diff_idx][0],
            "human_color": self.human_color,
            "board_theme": self.board_theme,
        }

    def _button_list(self):
        """Return visible buttons; AI-only choices are hidden in PvP mode."""
        buttons = [self.btn_start, self.btn_mode]
        if not self.mode_pvp:
            buttons.extend([self.btn_color, self.btn_diff])
        buttons.append(self.btn_theme)
        return buttons

    def _layout_buttons(self):
        """Stack visible buttons in the available menu area."""
        L = self.layout
        bw = L.menu_button_width()
        num = len(self._button_list())
        total_h, bh, gap = L.menu_button_area_height(num)
        cx = L.width // 2

        y0 = L.menu_content_top() + int(90 * L.scale)
        max_bottom = L.height - L.pad
        if y0 + total_h > max_bottom:
            y0 = max(L.pad + int(100 * L.scale), max_bottom - total_h)

        y = y0
        for btn in self._button_list():
            btn.rect = pygame.Rect(cx - bw // 2, y, bw, bh)
            y += bh + gap

    def _draw_developer_credit(self, surface):
        """Draw a subtle footer credit that stays clear of menu controls."""
        L = self.layout
        label = "Developed By"
        name = "Yassin Khaled"
        label_surf = self.font_credit_label.render(label, True, TEXT_DIM)
        name_surf = self.font_credit_name.render(name, True, TEXT_MUTED)

        gap = max(3, int(4 * L.scale))
        credit_h = label_surf.get_height() + gap + name_surf.get_height()
        buttons = self._button_list()
        buttons_bottom = max((btn.rect.bottom for btn in buttons), default=0)
        bottom_pad = max(L.pad, int(24 * L.scale))
        min_top = buttons_bottom + max(22, int(28 * L.scale))
        y = max(min_top, L.height - bottom_pad - credit_h)
        y = min(y, L.height - L.pad - credit_h)

        credit = pygame.Surface((L.width, credit_h), pygame.SRCALPHA)
        label_rect = label_surf.get_rect(center=(L.width // 2, label_surf.get_height() // 2))
        name_rect = name_surf.get_rect(
            center=(L.width // 2, label_surf.get_height() + gap + name_surf.get_height() // 2)
        )
        credit.blit(label_surf, label_rect)
        credit.blit(name_surf, name_rect)
        credit.set_alpha(int(170 * min(1.0, self._time / 1.4)))
        surface.blit(credit, (0, y))

    def update(self, dt):
        """Advance menu animation time and button hover/press states."""
        self._time += dt
        for btn in self._button_list():
            btn.update(dt)

    def handle_events(self, events):
        """Translate keyboard/mouse events into setting changes or start_game."""
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_game = True
                continue
            if self.btn_start.handle_event(e):
                self.start_game = True
            if self.btn_mode.handle_event(e):
                self.mode_pvp = not self.mode_pvp
                self._rebuild_fonts_and_layout()
            if self.btn_theme.handle_event(e):
                idx = BOARD_THEME_ORDER.index(self.board_theme)
                self.board_theme = BOARD_THEME_ORDER[(idx + 1) % len(BOARD_THEME_ORDER)]
                self.btn_theme.text = f"Board: {BOARD_THEMES[self.board_theme]['label']}"
                self._layout_buttons()
            if not self.mode_pvp:
                if self.btn_color.handle_event(e):
                    self.human_color = "b" if self.human_color == "w" else "w"
                    self.btn_color.text = (
                        "You play: White" if self.human_color == "w" else "You play: Black"
                    )
                    self._layout_buttons()
                if self.btn_diff.handle_event(e):
                    self.diff_idx = (self.diff_idx + 1) % len(self.diffs)
                    self.btn_diff.text = f"Difficulty: {self.diffs[self.diff_idx][1]}"
                    self._layout_buttons()

    def _draw_background(self, surface):
        """Render a cached subtle background sized to the current window."""
        size = (self.layout.width, self.layout.height)
        if self._bg_cache is None or self._bg_size != size:
            self._bg_cache = pygame.Surface(size)
            w, h = size
            self._bg_cache.fill(BG_COLOR)
            for i in range(h):
                t = i / max(1, h - 1)
                shade = int(14 * (1 - t))
                color = (BG_COLOR[0] + shade, BG_COLOR[1] + shade, BG_COLOR[2] + shade + 4)
                pygame.draw.line(self._bg_cache, color, (0, i), (w, i))
            glow = pygame.Surface((w, 200), pygame.SRCALPHA)
            accent_y = h // 4
            for i in range(200):
                a = int(28 * (1 - abs(i - 100) / 100))
                pygame.draw.line(glow, (*ACCENT[:3], a), (0, i), (w, i))
            self._bg_cache.blit(glow, (0, accent_y - 100))
            self._bg_size = size
        surface.blit(self._bg_cache, (0, 0))

    def draw(self, surface):
        """Draw menu title, instructions, and current setting buttons."""
        L = self.layout
        self._draw_background(surface)

        title_y = int(L.height * 0.14) + math.sin(self._time * 1.2) * 2
        draw_text_shadow(
            surface, "PyChess", self.font_title, TEXT_COLOR, L.width // 2, title_y, center=True
        )
        draw_text(surface, "Professional", self.font_sub, ACCENT, L.width // 2, title_y + 48, center=True)
        draw_text(
            surface,
            "Enter / Space to start  |  Esc in-game: pause",
            self.font_sub,
            TEXT_MUTED,
            L.width // 2,
            title_y + 78,
            center=True,
        )

        sep_y = L.menu_content_top() + int(72 * L.scale)
        pygame.draw.line(surface, PANEL_BORDER, (L.width // 2 - 140, sep_y), (L.width // 2 + 140, sep_y), 1)

        for btn in self._button_list():
            btn.draw(surface)

        self._draw_developer_credit(surface)
