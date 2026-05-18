"""Responsive layout metrics derived from the current window size."""


class AppLayout:
    MIN_WIDTH = 880
    MIN_HEIGHT = 600
    DEFAULT_WIDTH = 1000
    DEFAULT_HEIGHT = 720

    def __init__(self, width, height):
        self.width = max(self.MIN_WIDTH, int(width))
        self.height = max(self.MIN_HEIGHT, int(height))
        self.scale = max(0.82, min(1.2, self.width / self.DEFAULT_WIDTH))

        margin = max(6, int(8 * self.scale))
        min_panel = max(260, int(280 * self.scale))
        max_panel = max(300, int(380 * self.scale))

        self.panel_w = max(min_panel, min(max_panel, int(self.width * 0.34)))
        max_board = self.width - self.panel_w
        self.board_size = min(max_board, self.height - margin * 2)
        self.board_size = max(400, self.board_size)
        self.panel_w = self.width - self.board_size

        self.board_x = 0
        self.board_y = max(0, (self.height - self.board_size) // 2)
        self.panel_x = self.board_size

        self.pad = max(14, int(20 * self.scale))
        self.board_border = max(4, int(6 * self.scale))
        inner = self.board_size - self.board_border * 2
        self.square_size = max(36, inner // 8)

        self.font_title = self._fs(48, 40)
        self.font_sub = self._fs(16, 13)
        self.font_btn = self._fs(18, 15)
        self.font_lg = self._fs(21, 17)
        self.font_md = self._fs(17, 14)
        self.font_sm = self._fs(14, 12)
        self.font_hist = self._fs(15, 12)
        self.font_overlay = self._fs(32, 24)

        btn_h = max(36, int(40 * self.scale))
        btn_gap = max(8, int(10 * self.scale))
        self.btn_h = btn_h
        self.btn_gap = btn_gap
        self.panel_buttons_h = btn_h * 2 + btn_gap + self.pad
        self.panel_buttons_top = self.height - self.panel_buttons_h

        header_h = int(36 + 28 * self.scale)
        self.panel_header_h = header_h
        self.history_row_h = max(18, int(21 * self.scale))

        cap_block = int(70 * self.scale)
        self.panel_captured_h = cap_block
        history_bottom = self.panel_buttons_top - self.pad - self.panel_captured_h
        history_top = self.pad + self.panel_header_h
        avail = max(self.history_row_h * 3, history_bottom - history_top)
        self.history_max_rows = max(4, avail // self.history_row_h)
        self.panel_history_top = history_top
        self.panel_history_height = self.history_max_rows * self.history_row_h

    def _fs(self, base, minimum):
        return max(minimum, int(base * self.scale))

    def board_inner_rect(self):
        import pygame

        return pygame.Rect(
            self.board_x + self.board_border,
            self.board_y + self.board_border,
            self.board_size - self.board_border * 2,
            self.board_size - self.board_border * 2,
        )

    def sq_rect(self, row, col):
        import pygame

        inner = self.board_inner_rect()
        sq = inner.w // 8
        return pygame.Rect(inner.x + col * sq, inner.y + row * sq, sq, sq)

    def sq_center(self, row, col):
        r = self.sq_rect(row, col)
        return r.centerx, r.centery

    def menu_button_width(self):
        return min(320, self.width - self.pad * 4)

    def menu_content_top(self):
        return max(int(self.height * 0.22), int(120 * self.scale))

    def menu_button_area_height(self, num_buttons):
        gap = max(10, int(12 * self.scale))
        bh = max(40, int(44 * self.scale))
        return num_buttons * bh + (num_buttons - 1) * gap, bh, gap
