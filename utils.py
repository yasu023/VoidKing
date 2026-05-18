"""Rendering, asset, font, and animation helpers shared by scenes."""

import math
import os

import pygame

from constants import BLACK, FONT_UI, SQUARE_SIZE, WHITE

_UNICODE_PIECES = {
    "wp": "\u2659",
    "wn": "\u2658",
    "wb": "\u2657",
    "wr": "\u2656",
    "wq": "\u2655",
    "wk": "\u2654",
    "bp": "\u265F",
    "bn": "\u265E",
    "bb": "\u265D",
    "br": "\u265C",
    "bq": "\u265B",
    "bk": "\u265A",
}

_assets = {}
_warned_assets = set()
_font_cache = {}
_mixer_ready = False
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _asset_path(relative):
    """Resolve an asset path relative to the project directory."""
    return os.path.join(_BASE_DIR, relative)


def clear_font_cache():
    """Clear cached fonts and square overlays after display/layout changes."""
    _font_cache.clear()
    global _overlay_cache
    _overlay_cache = {}


def fit_text(font, text, max_width):
    """Return text truncated with ellipsis if wider than max_width."""
    if max_width <= 8:
        return ""
    if font.size(str(text))[0] <= max_width:
        return str(text)
    ell = "..."
    lo, hi = 0, len(str(text))
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.size(str(text)[:mid] + ell)[0] <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return str(text)[:lo] + ell if lo else ell


def get_font(size, bold=False):
    """Return a cached UI font, falling back to Pygame's default font."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    for name in FONT_UI:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            if font:
                _font_cache[key] = font
                return font
        except pygame.error:
            continue
    font = pygame.font.Font(None, size)
    _font_cache[key] = font
    return font


def ease_out_cubic(t):
    """Easing curve used for overlays that slow as they finish."""
    t = max(0.0, min(1.0, t))
    return 1.0 - pow(1.0 - t, 3)


def ease_in_out_quad(t):
    """Easing curve used for piece movement with gentle start and stop."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def lerp(a, b, t):
    """Linear interpolation between two scalar values."""
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    """Interpolate RGB or RGBA color tuples component by component."""
    t = max(0.0, min(1.0, t))
    if len(c1) == 4 or len(c2) == 4:
        return tuple(int(lerp(c1[i], c2[i], t)) for i in range(min(len(c1), len(c2))))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def _ensure_mixer():
    """Try to initialize audio once; failures leave sound playback disabled."""
    global _mixer_ready
    if not _mixer_ready:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            _mixer_ready = True
        except pygame.error:
            _mixer_ready = False


def generate_procedural_piece(piece_name, size):
    """Create a Unicode chess-piece fallback when image assets are missing."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    font = None
    for family in ("segoeuisymbol", "dejavusans", "arial"):
        try:
            font = pygame.font.SysFont(family, max(12, size - 10))
            break
        except pygame.error:
            continue
    if font is None:
        font = pygame.font.Font(None, max(12, size))

    char = _UNICODE_PIECES.get(piece_name, "?")
    color = WHITE if piece_name.startswith("w") else BLACK
    text_surf = font.render(char, True, color)
    text_rect = text_surf.get_rect(center=(size // 2, size // 2))

    outline_color = BLACK if piece_name.startswith("w") else WHITE
    outline_surf = font.render(char, True, outline_color)
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        surface.blit(outline_surf, (text_rect.x + ox, text_rect.y + oy))
    surface.blit(text_surf, text_rect)
    return surface


def load_image(path, size=None, fallback_name=None):
    """Load and cache an image, with procedural piece fallback support."""
    full_path = _asset_path(path) if not os.path.isabs(path) else path
    cache_key = (full_path, size)
    if cache_key in _assets:
        return _assets[cache_key]
    try:
        img = pygame.image.load(full_path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        _assets[cache_key] = img
        return img
    except (pygame.error, FileNotFoundError, OSError) as exc:
        if full_path not in _warned_assets:
            _warned_assets.add(full_path)
            print(f"Could not load image {full_path}: using fallback ({exc})")
        if fallback_name:
            img = generate_procedural_piece(fallback_name, size[0] if size else SQUARE_SIZE)
            _assets[cache_key] = img
            return img
        surf = pygame.Surface(size or (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        _assets[cache_key] = surf
        return surf


class _DummySound:
    """No-op sound object used when audio is unavailable."""

    def play(self):
        pass


def load_sound(path):
    """Load and cache a sound, returning a no-op object if loading fails."""
    full_path = _asset_path(path) if not os.path.isabs(path) else path
    if full_path in _assets:
        return _assets[full_path]
    _ensure_mixer()
    if not _mixer_ready:
        dummy = _DummySound()
        _assets[full_path] = dummy
        return dummy
    try:
        sound = pygame.mixer.Sound(full_path)
        _assets[full_path] = sound
        return sound
    except (pygame.error, FileNotFoundError, OSError):
        dummy = _DummySound()
        _assets[full_path] = dummy
        return dummy


def draw_text(surface, text, font, color, x, y, center=False):
    """Render text at a position and return its rectangle."""
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_text_shadow(
    surface,
    text,
    font,
    color,
    x,
    y,
    center=False,
    offset=(0, 2),
    shadow_alpha=90,
):
    """Render text with a soft shadow for contrast over dark backgrounds."""
    text_surface = font.render(str(text), True, color)
    shadow_surface = font.render(str(text), True, (12, 14, 20))
    shadow_surface.set_alpha(shadow_alpha)
    text_rect = text_surface.get_rect()
    shadow_rect = shadow_surface.get_rect()
    if center:
        text_rect.center = (x, y)
        shadow_rect.center = (x + offset[0], y + offset[1])
    else:
        text_rect.topleft = (x, y)
        shadow_rect.topleft = (x + offset[0], y + offset[1])
    surface.blit(shadow_surface, shadow_rect)
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_rounded_panel(surface, rect, color, border_color=None, radius=12, border=2, alpha=255):
    """Draw a rounded translucent panel with an optional border."""
    panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    fill = color if len(color) == 4 else (*color, alpha)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    if border_color:
        pygame.draw.rect(panel, border_color, panel.get_rect(), width=border, border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_alpha_rect(surface, rect, color):
    """Cached-friendly tinted overlay on a square."""
    overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    if len(color) == 3:
        overlay.fill((*color, 255))
    else:
        overlay.fill(color)
    surface.blit(overlay, rect.topleft)


_overlay_cache = {}


def get_square_overlay(size, color):
    """Return a cached solid overlay surface for board highlights."""
    key = (size, color)
    if key not in _overlay_cache:
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        s.fill(color if len(color) == 4 else (*color, 255))
        _overlay_cache[key] = s
    return _overlay_cache[key]
