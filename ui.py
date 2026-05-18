"""Reusable lightweight UI widgets for the Pygame scenes."""

import pygame

from constants import (
    ACCENT,
    BTN_ACTIVE,
    BTN_BG,
    BTN_HOVER,
    PANEL_BORDER,
    PANEL_COLOR,
    SHADOW,
    TEXT_COLOR,
    WHITE,
)
from utils import draw_text, draw_text_shadow, fit_text, lerp_color


class Button:
    """Animated click button with hover/press state and safe text fitting."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        font,
        bg_color=BTN_BG,
        text_color=TEXT_COLOR,
        hover_color=BTN_HOVER,
        accent=ACCENT,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.hover_color = hover_color
        self.accent = accent
        self.is_hovered = False
        self.is_pressed = False
        self._armed = False
        self._hover_t = 0.0
        self._press_t = 0.0

    def update(self, dt):
        """Smooth hover/press animation values toward current input state."""
        try:
            self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        except pygame.error:
            pass
        target_hover = 1.0 if self.is_hovered else 0.0
        target_press = 1.0 if self.is_pressed else 0.0
        speed = min(1.0, dt * 14.0)
        self._hover_t += (target_hover - self._hover_t) * speed
        self._press_t += (target_press - self._press_t) * speed

    def draw(self, surface):
        """Draw the button background, border, shadow, and fitted label."""
        hover = self._hover_t
        press = self._press_t
        base = lerp_color(self.bg_color, self.hover_color, hover)
        if press > 0.01:
            base = lerp_color(base, BTN_ACTIVE, press * 0.6)

        shadow_rect = self.rect.move(0, 3)
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, SHADOW, shadow_surf.get_rect(), border_radius=8)
        surface.blit(shadow_surf, shadow_rect.topleft)

        pygame.draw.rect(surface, base, self.rect, border_radius=8)
        border_c = lerp_color(PANEL_BORDER, self.accent, hover * 0.85)
        pygame.draw.rect(surface, border_c, self.rect, width=2, border_radius=8)

        ty = self.rect.centery + int(press * 2)
        label = fit_text(self.font, self.text, self.rect.width - 20)
        draw_text_shadow(
            surface,
            label,
            self.font,
            self.text_color,
            self.rect.centerx,
            ty,
            center=True,
            offset=(0, 1),
            shadow_alpha=80,
        )

    def handle_event(self, event):
        """Hover on motion; activate once on full click (down inside, up inside)."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self._armed = True
                    self.is_pressed = True
                    self.is_hovered = True
                else:
                    self._armed = False
                    self.is_pressed = False
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                activate = self._armed and self.rect.collidepoint(event.pos)
                self._armed = False
                self.is_pressed = False
                return activate
        return False


class Panel:
    """Cached side-panel background used by the game HUD."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self._cache = None

    def set_geometry(self, x, y, width, height):
        """Move/resize the panel and invalidate its cached surface if needed."""
        new_rect = pygame.Rect(x, y, width, height)
        if new_rect != self.rect:
            self.rect = new_rect
            self.invalidate()

    def invalidate(self):
        """Force the next draw to rebuild the panel surface."""
        self._cache = None

    def draw(self, surface):
        """Draw cached gradient panel background."""
        if self._cache is None:
            self._cache = pygame.Surface((self.rect.w, self.rect.h))
            self._cache.fill(PANEL_COLOR)
            for i in range(self.rect.h):
                t = i / max(1, self.rect.h - 1)
                shade = int(6 * (1 - t))
                color = (
                    min(255, PANEL_COLOR[0] + shade),
                    min(255, PANEL_COLOR[1] + shade),
                    min(255, PANEL_COLOR[2] + shade),
                )
                pygame.draw.line(self._cache, color, (0, i), (self.rect.w, i))
            pygame.draw.line(self._cache, PANEL_BORDER, (0, 0), (0, self.rect.h), 2)
        surface.blit(self._cache, self.rect.topleft)
