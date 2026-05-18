import math

import pygame

from constants import *
from board import Board
from move import Move
from ui import Button, Panel
from utils import (
    clear_font_cache,
    draw_rounded_panel,
    draw_text,
    draw_text_shadow,
    ease_in_out_quad,
    ease_out_cubic,
    fit_text,
    get_font,
    get_square_overlay,
    load_image,
    load_sound,
)
from ai import start_ai_search, poll_ai_result, cancel_ai_search


class GameScene:
    def __init__(self, settings, layout):
        self.settings = settings
        self.layout = layout
        self.board = Board()
        self.valid_moves = self.board.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = False

        self.paused = False
        self.request_main_menu = False
        self._pause_alpha = 0.0

        self.animating = False
        self.anim_queue = []
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_queue = None
        self._ai_move_pending = None

        self.promotion_move = None
        self.promotion_choices = []
        self._promo_hover = -1
        self._promo_arm_index = -1

        self._pulse = 0.0
        self._game_over_alpha = 0.0
        self._was_game_over = False

        self._board_bg = None
        self._board_bg_theme = None
        self._board_bg_size = None
        self._panel_content = None
        self._panel_signature = None
        self._last_dt = 1.0 / FPS

        self.panel = Panel(0, 0, 10, 10)
        self.btn_restart = Button(0, 0, 10, 10, "Restart", get_font(16))
        self.btn_undo = Button(0, 0, 10, 10, "Undo", get_font(16))
        self.btn_resume = Button(0, 0, 10, 10, "Resume", get_font(18))
        self.btn_pause_restart = Button(0, 0, 10, 10, "Restart", get_font(18))
        self.btn_main_menu = Button(0, 0, 10, 10, "Main Menu", get_font(18))

        self.snd_move = load_sound("assets/sounds/move.wav")
        self.snd_capture = load_sound("assets/sounds/capture.wav")
        self.snd_castle = load_sound("assets/sounds/castle.wav")
        self.snd_check = load_sound("assets/sounds/check.wav")

        self._rebuild_ui()

    def on_resize(self, layout):
        self.layout = layout
        clear_font_cache()
        self._rebuild_ui()
        self._invalidate_board_cache()
        self._invalidate_panel_cache()

    def _rebuild_ui(self):
        L = self.layout
        self.font_sm = get_font(L.font_sm)
        self.font = get_font(L.font_md)
        self.font_lg = get_font(L.font_lg, bold=True)
        self.large_font = get_font(L.font_overlay, bold=True)
        self.font_hist = get_font(L.font_hist)

        for btn in (
            self.btn_restart,
            self.btn_undo,
            self.btn_resume,
            self.btn_pause_restart,
            self.btn_main_menu,
        ):
            btn.font = self.font

        self.panel.set_geometry(L.panel_x, 0, L.panel_w, L.height)
        pw = L.panel_w - L.pad * 2
        bx = L.panel_x + L.pad
        y = L.panel_buttons_top
        self.btn_restart.rect = pygame.Rect(bx, y + L.btn_h + L.btn_gap, pw, L.btn_h)
        self.btn_undo.rect = pygame.Rect(bx, y, pw, L.btn_h)

        bw = min(280, L.width - 80)
        bh = L.btn_h
        cx, cy = L.width // 2, L.height // 2
        gap = 12
        self.btn_resume.rect = pygame.Rect(cx - bw // 2, cy - bh - gap, bw, bh)
        self.btn_pause_restart.rect = pygame.Rect(cx - bw // 2, cy, bw, bh)
        self.btn_main_menu.rect = pygame.Rect(cx - bw // 2, cy + bh + gap, bw, bh)

    def toggle_pause(self):
        if self.promotion_move:
            return
        self.paused = not self.paused

    def _theme(self):
        name = self.settings.get("board_theme", "classic")
        return BOARD_THEMES.get(name, BOARD_THEMES["classic"])

    def _invalidate_board_cache(self):
        self._board_bg = None
        self._board_bg_theme = None
        self._board_bg_size = None

    def _invalidate_panel_cache(self):
        self._panel_content = None
        self._panel_signature = None

    def _sq_rect(self, row, col):
        return self.layout.sq_rect(row, col)

    def _sq_center(self, row, col):
        return self.layout.sq_center(row, col)

    def _board_inner_rect(self):
        return self.layout.board_inner_rect()

    def _build_board_background(self):
        L = self.layout
        theme = self._theme()
        size = (L.board_size, L.board_size)
        if self._board_bg is not None and self._board_bg_size == size and self._board_bg_theme == self.settings.get(
            "board_theme"
        ):
            return self._board_bg

        surf = pygame.Surface(size)
        surf.fill(theme["border"])
        inner = pygame.Rect(
            L.board_border,
            L.board_border,
            L.board_size - L.board_border * 2,
            L.board_size - L.board_border * 2,
        )
        sq = inner.w // 8
        files = "abcdefgh"
        ranks = "87654321"
        coord_font = get_font(max(10, L.font_sm - 2))

        for r in range(8):
            for c in range(8):
                color = theme["light"] if (r + c) % 2 == 0 else theme["dark"]
                rect = pygame.Rect(inner.x + c * sq, inner.y + r * sq, sq, sq)
                pygame.draw.rect(surf, color, rect)
                if c == 0:
                    label = coord_font.render(ranks[r], True, theme["coord"])
                    label.set_alpha(160)
                    surf.blit(label, (rect.x + 4, rect.y + 4))
                if r == 7:
                    label = coord_font.render(files[c], True, theme["coord"])
                    label.set_alpha(160)
                    surf.blit(label, (rect.x + max(4, sq - 14), rect.y + max(4, sq - 16)))

        self._board_bg = surf
        self._board_bg_size = size
        self._board_bg_theme = self.settings.get("board_theme", "classic")
        return surf

    def reset(self):
        cancel_ai_search()
        self.board = Board()
        self.valid_moves = self.board.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = False
        self.anim_queue = []
        self.animating = False
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_queue = None
        self._ai_move_pending = None
        self.promotion_move = None
        self.promotion_choices = []
        self._promo_arm_index = -1
        self._game_over_alpha = 0.0
        self._was_game_over = False
        self.paused = False
        self._invalidate_panel_cache()

    def _human_plays_white(self):
        return self.settings.get("human_color", "w") == "w"

    def _is_human_turn(self):
        if self.settings["pvp"]:
            return True
        if self._human_plays_white():
            return self.board.white_to_move
        return not self.board.white_to_move

    def update(self, dt=None):
        if dt is None:
            dt = self._last_dt
        self._last_dt = dt
        self._pulse += dt * 2.8

        buttons = [
            self.btn_restart,
            self.btn_undo,
            self.btn_resume,
            self.btn_pause_restart,
            self.btn_main_menu,
        ]
        for btn in buttons:
            btn.update(dt)

        target_pause = 1.0 if self.paused else 0.0
        self._pause_alpha += (target_pause - self._pause_alpha) * min(1.0, dt * 10)

        if self.paused:
            return

        if self.board.is_game_over:
            self._game_over_alpha = min(1.0, self._game_over_alpha + dt * 2.5)
            self._was_game_over = True
        elif self._was_game_over:
            self._game_over_alpha = max(0.0, self._game_over_alpha - dt * 4.0)

        self.process_animations(dt)

        if self.animating:
            return

        if self._ai_move_pending is not None:
            self.execute_move(self._ai_move_pending)
            self._ai_move_pending = None
            self.ai_thinking = False
            return

        if (
            not self.settings["pvp"]
            and not self.board.is_game_over
            and not self.promotion_move
            and self._is_human_turn() is False
            and not self.ai_thinking
        ):
            self.ai_thinking = True
            self.ai_thread, self.ai_queue = start_ai_search(
                self.board, self.valid_moves, self.settings["ai_depth"]
            )

        if self.ai_thinking and self.ai_queue is not None:
            result = poll_ai_result(self.ai_queue)
            if result is not None:
                move, _nodes = result
                cancel_ai_search()
                self.ai_thread = None
                if move is not None and self._move_in_valid(move):
                    self._ai_move_pending = move
                else:
                    self.ai_thinking = False
                self._invalidate_panel_cache()

    def _move_in_valid(self, move):
        for vm in self.valid_moves:
            if vm.move_id == move.move_id and vm.promotion == move.promotion:
                return True
        return False

    def handle_events(self, events):
        if self.paused:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not getattr(e, "repeat", False):
                    self.paused = False
                if self.btn_resume.handle_event(e):
                    self.paused = False
                if self.btn_pause_restart.handle_event(e):
                    self.reset()
                    self.paused = False
                if self.btn_main_menu.handle_event(e):
                    self.request_main_menu = True
            return

        if self.promotion_move is not None:
            self.handle_promotion_events(events)
            return

        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not getattr(e, "repeat", False):
                self.toggle_pause()
                break

        if self.animating or self.ai_thinking:
            for e in events:
                if self.btn_restart.handle_event(e):
                    self.reset()
            return

        for e in events:
            if self.btn_restart.handle_event(e):
                self.reset()
                continue
            if self.btn_undo.handle_event(e):
                self._undo()
                continue

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.board.is_game_over:
                    continue
                if not self._is_human_turn():
                    continue

                location = pygame.mouse.get_pos()
                inner = self._board_inner_rect()
                if not inner.collidepoint(location):
                    continue

                sq = inner.w // 8
                col = (location[0] - inner.x) // sq
                row = (location[1] - inner.y) // sq

                if self.sq_selected == (row, col):
                    self.sq_selected = ()
                    self.player_clicks = []
                else:
                    self.sq_selected = (row, col)
                    self.player_clicks.append(self.sq_selected)

                if len(self.player_clicks) == 2:
                    move_start = self.player_clicks[0]
                    move_end = self.player_clicks[1]
                    matched = False
                    for valid_move in self.valid_moves:
                        if (
                            valid_move.start_row == move_start[0]
                            and valid_move.start_col == move_start[1]
                            and valid_move.end_row == move_end[0]
                            and valid_move.end_col == move_end[1]
                        ):
                            matched = True
                            if valid_move.promotion:
                                self._start_promotion(valid_move)
                            else:
                                self.execute_move(valid_move)
                            break

                    if not matched:
                        self.player_clicks = [self.sq_selected] if self.sq_selected else []

    def _start_promotion(self, base_move):
        color = "w" if self.board.white_to_move else "b"
        self.promotion_move = base_move
        self.promotion_choices = []
        self._promo_arm_index = -1
        for p in ("q", "r", "b", "n"):
            promo_move = Move(
                (base_move.start_row, base_move.start_col),
                (base_move.end_row, base_move.end_col),
                self.board,
                is_en_passant=base_move.is_en_passant,
                is_castle=base_move.is_castle,
                promotion=color + p,
            )
            if any(vm.move_id == promo_move.move_id for vm in self.valid_moves):
                self.promotion_choices.append(promo_move)

    def handle_promotion_events(self, events):
        if self.promotion_move is None:
            return
        self._promo_hover = -1
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                for i, _ in enumerate(self.promotion_choices):
                    if self._promotion_rect(i).collidepoint(pos):
                        self._promo_hover = i
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = e.pos
                self._promo_arm_index = -1
                for i, _ in enumerate(self.promotion_choices):
                    if self._promotion_rect(i).collidepoint(pos):
                        self._promo_arm_index = i
                        break
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                pos = e.pos
                idx = self._promo_arm_index
                self._promo_arm_index = -1
                if idx >= 0 and idx < len(self.promotion_choices):
                    if self._promotion_rect(idx).collidepoint(pos):
                        self.execute_move(self.promotion_choices[idx])
                        self.promotion_move = None
                        self.promotion_choices = []
                        return

    def _promotion_rect(self, index):
        inner = self._board_inner_rect()
        sq = inner.w // 8
        total_w = sq * 4
        x0 = inner.x + (inner.w - total_w) // 2
        y = inner.y + inner.h // 2 - sq // 2
        return pygame.Rect(x0 + index * sq, y, sq, sq)

    def _undo(self):
        cancel_ai_search()
        self.ai_thinking = False
        self.board.undo_move()
        if not self.settings["pvp"]:
            if self.board.move_log:
                self.board.undo_move()
        self.valid_moves = self.board.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = True
        self.anim_queue = []
        self.animating = False
        self._invalidate_panel_cache()

    def execute_move(self, move):
        start_rect = self._sq_rect(move.start_row, move.start_col)
        end_rect = self._sq_rect(move.end_row, move.end_col)

        self.anim_queue.append(
            {
                "move": move,
                "piece": move.piece_moved,
                "start": start_rect.topleft,
                "end": end_rect.topleft,
                "progress": 0.0,
                "duration": 0.22,
            }
        )
        self.animating = True

        if move.piece_captured:
            self.snd_capture.play()
        elif move.is_castle:
            self.snd_castle.play()
        else:
            self.snd_move.play()

        self.board.make_move(move)

        if self.board.in_check():
            self.snd_check.play()

        self.valid_moves = self.board.get_valid_moves()
        self.sq_selected = ()
        self.player_clicks = []
        self.move_made = True
        self._invalidate_panel_cache()

    def process_animations(self, dt):
        if not self.anim_queue:
            self.animating = False
            return
        anim = self.anim_queue[0]
        anim["progress"] += dt / anim["duration"]
        if anim["progress"] >= 1.0:
            self.anim_queue.pop(0)
        if not self.anim_queue:
            self.animating = False

    def _panel_signature_key(self):
        log_len = len(self.board.move_log)
        caps = tuple(m.piece_captured for m in self.board.move_log if m.piece_captured)
        return (
            log_len,
            caps,
            self.board.white_to_move,
            self.ai_thinking,
            self.board.is_game_over,
            self.settings.get("pvp"),
            self.layout.width,
            self.layout.height,
        )

    def _build_panel_content(self):
        L = self.layout
        surf = pygame.Surface((L.panel_w, L.height), pygame.SRCALPHA)
        x = L.pad
        y = L.pad
        content_w = L.panel_w - L.pad * 2

        if self.settings["pvp"]:
            turn_text = "White to move" if self.board.white_to_move else "Black to move"
            turn_color = TEXT_COLOR
        else:
            if self._human_plays_white():
                turn_text, turn_color = (
                    ("Your move", ACCENT) if self.board.white_to_move else ("Opponent thinking", TEXT_MUTED)
                )
            else:
                turn_text, turn_color = (
                    ("Your move", ACCENT) if not self.board.white_to_move else ("Opponent thinking", TEXT_MUTED)
                )

        draw_text_shadow(surf, fit_text(self.font_lg, turn_text, content_w), self.font_lg, turn_color, x, y)
        y += int(34 * L.scale)

        if self.ai_thinking:
            dots = "." * (1 + int(self._pulse * 2) % 3)
            draw_text(surf, f"AI{dots}", self.font_sm, ACCENT, x, y)
            y += int(20 * L.scale)

        draw_text(surf, "MOVE HISTORY", self.font_sm, TEXT_MUTED, x, y)
        y = L.panel_history_top
        hist_bottom = L.panel_buttons_top - L.pad - L.panel_captured_h

        moves = self.board.move_log
        max_pairs = L.history_max_rows
        start_pair = max(0, (len(moves) + 1) // 2 - max_pairs)
        col_w = max(60, (content_w - 32) // 2)
        row_h = L.history_row_h

        for pair_idx in range(start_pair, (len(moves) + 1) // 2):
            row_y = y + (pair_idx - start_pair) * row_h
            if row_y + row_h > hist_bottom:
                break
            move_num = pair_idx + 1
            white_idx = pair_idx * 2
            black_idx = white_idx + 1

            num_surf = self.font_hist.render(f"{move_num}.", True, TEXT_DIM)
            surf.blit(num_surf, (x, row_y + 1))

            if white_idx < len(moves):
                w_not = fit_text(self.font_hist, moves[white_idx].get_chess_notation(), col_w - 4)
                w_color = ACCENT if white_idx == len(moves) - 1 else TEXT_COLOR
                draw_text(surf, w_not, self.font_hist, w_color, x + 26, row_y)

            if black_idx < len(moves):
                b_not = fit_text(self.font_hist, moves[black_idx].get_chess_notation(), col_w - 4)
                b_color = ACCENT if black_idx == len(moves) - 1 else TEXT_COLOR
                draw_text(surf, b_not, self.font_hist, b_color, x + 26 + col_w, row_y)

        cap_y = hist_bottom + 8
        pygame.draw.line(surf, PANEL_BORDER, (x, cap_y - 6), (x + content_w, cap_y - 6), 1)
        draw_text(surf, "CAPTURED", self.font_sm, TEXT_MUTED, x, cap_y)

        cap_y += int(22 * L.scale)
        cap_size = max(22, int(26 * L.scale))
        max_per_row = max(4, content_w // (cap_size + 4))

        white_captured = []
        black_captured = []
        for move in self.board.move_log:
            if move.piece_captured:
                (white_captured if move.piece_captured[0] == "w" else black_captured).append(
                    move.piece_captured
                )

        for i, p in enumerate(white_captured[: max_per_row * 2]):
            img = load_image(f"assets/pieces/{p}.png", (cap_size, cap_size), fallback_name=p)
            surf.blit(img, (x + (i % max_per_row) * (cap_size + 4), cap_y + (i // max_per_row) * (cap_size + 4)))

        if white_captured:
            cap_y += ((min(len(white_captured), max_per_row * 2) - 1) // max_per_row + 1) * (cap_size + 4) + 6

        for i, p in enumerate(black_captured[: max_per_row * 2]):
            img = load_image(f"assets/pieces/{p}.png", (cap_size, cap_size), fallback_name=p)
            surf.blit(img, (x + (i % max_per_row) * (cap_size + 4), cap_y + (i // max_per_row) * (cap_size + 4)))

        return surf

    def _get_panel_content(self):
        sig = self._panel_signature_key()
        if self._panel_content is None or self._panel_signature != sig:
            self._panel_content = self._build_panel_content()
            self._panel_signature = sig
        return self._panel_content

    def _draw_board_layer(self, surface):
        L = self.layout
        self._build_board_background()
        surface.blit(self._board_bg, (L.board_x, L.board_y))

        sq_size = self._sq_rect(0, 0).w

        if self.board.move_log:
            last_move = self.board.move_log[-1]
            for r, c in (
                (last_move.start_row, last_move.start_col),
                (last_move.end_row, last_move.end_col),
            ):
                surface.blit(get_square_overlay(sq_size, LAST_MOVE_COLOR), self._sq_rect(r, c).topleft)

        if self.board.in_check():
            if self.board.white_to_move:
                kr, kc = self.board.white_king_loc
            else:
                kr, kc = self.board.black_king_loc
            pulse = 0.65 + 0.35 * math.sin(self._pulse * 3)
            check_c = (
                CHECK_COLOR[0],
                CHECK_COLOR[1],
                CHECK_COLOR[2],
                int(CHECK_COLOR[3] * pulse),
            )
            surface.blit(get_square_overlay(sq_size, check_c), self._sq_rect(kr, kc).topleft)

        if self.sq_selected and not self.ai_thinking and not self.paused:
            r, c = self.sq_selected
            pulse_a = int(SELECT_PULSE[3] * (0.55 + 0.45 * math.sin(self._pulse * 2)))
            sel_c = (SELECT_PULSE[0], SELECT_PULSE[1], SELECT_PULSE[2], pulse_a)
            surface.blit(get_square_overlay(sq_size, sel_c), self._sq_rect(r, c).topleft)

            for move in self.valid_moves:
                if move.start_row == r and move.start_col == c:
                    cx, cy = self._sq_center(move.end_row, move.end_col)
                    radius = max(5, sq_size // 7)
                    dot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    if self.board.board[move.end_row][move.end_col]:
                        pygame.draw.circle(dot, MOVE_HIGHLIGHT, (radius, radius), radius)
                    else:
                        pygame.draw.circle(dot, MOVE_HIGHLIGHT, (radius, radius), radius, 3)
                    surface.blit(dot, (cx - radius, cy - radius))

        animating_end = None
        if self.animating and self.anim_queue:
            m = self.anim_queue[0]["move"]
            animating_end = (m.end_row, m.end_col)

        for r in range(8):
            for c in range(8):
                if animating_end == (r, c):
                    continue
                piece = self.board.board[r][c]
                if piece:
                    rect = self._sq_rect(r, c)
                    img = load_image(
                        f"assets/pieces/{piece}.png",
                        (rect.w, rect.h),
                        fallback_name=piece,
                    )
                    surface.blit(img, rect)

        if self.animating and self.anim_queue:
            anim = self.anim_queue[0]
            t = ease_in_out_quad(min(1.0, anim["progress"]))
            sx, sy = anim["start"]
            ex, ey = anim["end"]
            lift = math.sin(t * math.pi) * max(4, sq_size // 12)
            curr_x = sx + (ex - sx) * t
            curr_y = sy + (ey - sy) * t - lift
            rect = self._sq_rect(0, 0)
            img = load_image(
                f"assets/pieces/{anim['piece']}.png",
                (rect.w, rect.h),
                fallback_name=anim["piece"],
            )
            surface.blit(img, (curr_x, curr_y))

    def _draw_promotion_ui(self, surface):
        if not self.promotion_move:
            return
        L = self.layout
        board_rect = pygame.Rect(L.board_x, L.board_y, L.board_size, L.board_size)
        overlay = pygame.Surface((L.board_size, L.board_size), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 190))
        surface.blit(overlay, board_rect.topleft)

        inner = self._board_inner_rect()
        draw_text_shadow(
            surface,
            "Promote pawn",
            self.font_lg,
            TEXT_COLOR,
            inner.centerx,
            inner.y + 24,
            center=True,
        )

        for i, promo_move in enumerate(self.promotion_choices):
            rect = self._promotion_rect(i)
            hovered = i == self._promo_hover
            bg = BTN_HOVER if hovered else PANEL_COLOR
            draw_rounded_panel(surface, rect.inflate(6, 6), bg, ACCENT if hovered else PANEL_BORDER, radius=8)
            img = load_image(
                f"assets/pieces/{promo_move.promotion}.png",
                (rect.w - 8, rect.h - 8),
                fallback_name=promo_move.promotion,
            )
            surface.blit(img, rect.move(4, 4))

    def _draw_game_over(self, surface):
        if self._game_over_alpha <= 0.01:
            return
        L = self.layout
        board_rect = pygame.Rect(L.board_x, L.board_y, L.board_size, L.board_size)
        alpha = int(200 * ease_out_cubic(self._game_over_alpha))
        overlay = pygame.Surface((L.board_size, L.board_size), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, alpha))
        surface.blit(overlay, board_rect.topleft)

        card_w = min(420, L.board_size - 40)
        card_h = min(170, int(150 * L.scale))
        card = pygame.Rect(0, 0, card_w, card_h)
        card.center = board_rect.center
        scale = 0.92 + 0.08 * ease_out_cubic(self._game_over_alpha)
        scaled = card.inflate(int(card.w * (scale - 1)), int(card.h * (scale - 1)))
        scaled.center = card.center
        card_alpha = int(255 * self._game_over_alpha)
        draw_rounded_panel(
            surface,
            scaled,
            (36, 40, 52, card_alpha),
            (88, 166, 255, min(255, card_alpha)),
            radius=14,
            border=2,
        )

        reason = fit_text(self.large_font, self.board.game_over_reason, card_w - 32)
        draw_text_shadow(
            surface,
            reason,
            self.large_font,
            TEXT_COLOR,
            scaled.centerx,
            scaled.centery - 14,
            center=True,
        )
        hint_font = get_font(L.font_sm)
        hint = fit_text(hint_font, "Esc: pause menu", card_w - 24)
        hint_surf = hint_font.render(hint, True, TEXT_MUTED)
        hint_surf.set_alpha(int(180 * self._game_over_alpha))
        hint_rect = hint_surf.get_rect(center=(scaled.centerx, scaled.bottom - 26))
        surface.blit(hint_surf, hint_rect)

    def _draw_pause_overlay(self, surface):
        if self._pause_alpha <= 0.01:
            return
        L = self.layout
        alpha = int(190 * self._pause_alpha)
        overlay = pygame.Surface((L.width, L.height), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, alpha))
        surface.blit(overlay, (0, 0))

        card_w = min(320, L.width - 60)
        card_h = L.btn_h * 3 + 12 * 2 + 50
        card = pygame.Rect(0, 0, card_w, card_h)
        card.center = (L.width // 2, L.height // 2)
        draw_rounded_panel(surface, card, (32, 36, 48, int(240 * self._pause_alpha)), ACCENT, radius=14)

        draw_text_shadow(
            surface,
            "Paused",
            self.font_lg,
            TEXT_COLOR,
            card.centerx,
            card.y + 22,
            center=True,
        )

        for btn in (self.btn_resume, self.btn_pause_restart, self.btn_main_menu):
            btn.draw(surface)

    def draw(self, surface):
        L = self.layout
        surface.fill(BG_COLOR)

        self._draw_board_layer(surface)
        self._draw_promotion_ui(surface)

        self.panel.draw(surface)
        surface.blit(self._get_panel_content(), (L.panel_x, 0))

        self.btn_restart.draw(surface)
        self.btn_undo.draw(surface)

        self._draw_game_over(surface)
        if self.paused:
            self._draw_pause_overlay(surface)
