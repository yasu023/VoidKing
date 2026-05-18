from move import Move


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Board:
    def __init__(self):
        self.board = [
            ['br', 'bn', 'bb', 'bq', 'bk', 'bb', 'bn', 'br'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wr', 'wn', 'wb', 'wq', 'wk', 'wb', 'wn', 'wr'],
        ]
        self.white_to_move = True
        self.move_log = []

        self.white_king_loc = (7, 4)
        self.black_king_loc = (0, 4)

        self.checkmate = False
        self.stalemate = False
        self.in_check_flag = False
        self.pins = []
        self.checks = []

        self.en_passant_possible = ()
        self.en_passant_log = [self.en_passant_possible]

        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [
            CastleRights(
                self.current_castling_rights.wks,
                self.current_castling_rights.bks,
                self.current_castling_rights.wqs,
                self.current_castling_rights.bqs,
            )
        ]

        self.halfmove_clock = 0
        self.halfmove_clock_log = [0]
        self.draw_by_fifty_moves = False

        self.position_history = [self.get_board_hash()]
        self.draw_by_repetition = False

        self.is_game_over = False
        self.game_over_reason = ""

    def copy(self):
        """Deep copy of board state for AI search threads."""
        other = Board.__new__(Board)
        other.board = [row[:] for row in self.board]
        other.white_to_move = self.white_to_move
        other.move_log = list(self.move_log)
        other.white_king_loc = self.white_king_loc
        other.black_king_loc = self.black_king_loc
        other.checkmate = self.checkmate
        other.stalemate = self.stalemate
        other.in_check_flag = self.in_check_flag
        other.pins = list(self.pins)
        other.checks = list(self.checks)
        other.en_passant_possible = self.en_passant_possible
        other.en_passant_log = list(self.en_passant_log)
        other.current_castling_rights = CastleRights(
            self.current_castling_rights.wks,
            self.current_castling_rights.bks,
            self.current_castling_rights.wqs,
            self.current_castling_rights.bqs,
        )
        other.castle_rights_log = [
            CastleRights(cr.wks, cr.bks, cr.wqs, cr.bqs) for cr in self.castle_rights_log
        ]
        other.halfmove_clock = self.halfmove_clock
        other.halfmove_clock_log = list(self.halfmove_clock_log)
        other.draw_by_fifty_moves = self.draw_by_fifty_moves
        other.position_history = list(self.position_history)
        other.draw_by_repetition = self.draw_by_repetition
        other.is_game_over = self.is_game_over
        other.game_over_reason = self.game_over_reason
        return other

    def get_board_hash(self):
        return (
            str(self.board)
            + str(self.white_to_move)
            + str(self.en_passant_possible)
            + str(self.current_castling_rights.wks)
            + str(self.current_castling_rights.bks)
            + str(self.current_castling_rights.wqs)
            + str(self.current_castling_rights.bqs)
        )

    def is_insufficient_material(self):
        white = {"p": 0, "n": 0, "b": 0, "r": 0, "q": 0}
        black = {"p": 0, "n": 0, "b": 0, "r": 0, "q": 0}
        white_bishop_squares = []
        black_bishop_squares = []

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if not piece:
                    continue
                color, ptype = piece[0], piece[1]
                if ptype == "k":
                    continue
                bucket = white if color == "w" else black
                bucket[ptype] += 1
                if ptype == "b":
                    if color == "w":
                        white_bishop_squares.append((row + col) % 2)
                    else:
                        black_bishop_squares.append((row + col) % 2)

        if white["p"] or white["r"] or white["q"] or black["p"] or black["r"] or black["q"]:
            return False
        if white["n"] > 1 or black["n"] > 1:
            return False
        if white["b"] > 1 or black["b"] > 1:
            return False
        if white["n"] and black["b"]:
            return False
        if black["n"] and white["b"]:
            return False

        total_minors = white["n"] + white["b"] + black["n"] + black["b"]
        if total_minors == 0:
            return True
        if total_minors == 1:
            return True
        if white["b"] == 1 and black["b"] == 1:
            if white_bishop_squares and black_bishop_squares:
                return white_bishop_squares[0] == black_bishop_squares[0]
        return False

    def update_game_status(self, valid_moves):
        self.checkmate = False
        self.stalemate = False
        self.draw_by_fifty_moves = False
        self.draw_by_repetition = False
        self.is_game_over = False
        self.game_over_reason = ""

        if len(valid_moves) == 0:
            if self.in_check():
                self.checkmate = True
                winner = "Black" if self.white_to_move else "White"
                self.game_over_reason = f"Checkmate! {winner} wins."
            else:
                self.stalemate = True
                self.game_over_reason = "Stalemate!"
            self.is_game_over = True
            return

        if self.halfmove_clock >= 100:
            self.draw_by_fifty_moves = True
            self.game_over_reason = "Draw by 50-move rule!"
            self.is_game_over = True
            return

        if self.position_history.count(self.get_board_hash()) >= 3:
            self.draw_by_repetition = True
            self.game_over_reason = "Draw by threefold repetition!"
            self.is_game_over = True
            return

        if self.is_insufficient_material():
            self.game_over_reason = "Draw by insufficient material!"
            self.is_game_over = True

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = None
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)

        if move.piece_moved == "wk":
            self.white_king_loc = (move.end_row, move.end_col)
        elif move.piece_moved == "bk":
            self.black_king_loc = (move.end_row, move.end_col)

        if move.is_en_passant:
            self.board[move.start_row][move.end_col] = None

        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        if move.is_castle:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = None
            else:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = None

        if move.promotion:
            self.board[move.end_row][move.end_col] = move.promotion

        self.en_passant_log.append(self.en_passant_possible)

        self.update_castle_rights(move)
        self.castle_rights_log.append(
            CastleRights(
                self.current_castling_rights.wks,
                self.current_castling_rights.bks,
                self.current_castling_rights.wqs,
                self.current_castling_rights.bqs,
            )
        )

        if move.piece_moved[1] == "p" or move.piece_captured:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        self.halfmove_clock_log.append(self.halfmove_clock)

        self.white_to_move = not self.white_to_move
        self.position_history.append(self.get_board_hash())

    def undo_move(self):
        if len(self.move_log) == 0:
            return

        move = self.move_log.pop()
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured
        self.white_to_move = not self.white_to_move

        if move.piece_moved == "wk":
            self.white_king_loc = (move.start_row, move.start_col)
        elif move.piece_moved == "bk":
            self.black_king_loc = (move.start_row, move.start_col)

        if move.is_en_passant:
            self.board[move.end_row][move.end_col] = None
            self.board[move.start_row][move.end_col] = move.piece_captured

        self.en_passant_log.pop()
        self.en_passant_possible = self.en_passant_log[-1]

        self.castle_rights_log.pop()
        cr = self.castle_rights_log[-1]
        self.current_castling_rights = CastleRights(cr.wks, cr.bks, cr.wqs, cr.bqs)

        if move.is_castle:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = None
            else:
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = None

        self.halfmove_clock_log.pop()
        self.halfmove_clock = self.halfmove_clock_log[-1]

        self.position_history.pop()

        self.checkmate = False
        self.stalemate = False
        self.is_game_over = False
        self.game_over_reason = ""
        self.draw_by_fifty_moves = False
        self.draw_by_repetition = False

    def update_castle_rights(self, move):
        if move.piece_moved == "wk":
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.piece_moved == "bk":
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False
        elif move.piece_moved == "wr":
            if move.start_row == 7:
                if move.start_col == 0:
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.wks = False
        elif move.piece_moved == "br":
            if move.start_row == 0:
                if move.start_col == 0:
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.bks = False

        if move.piece_captured == "wr":
            if move.end_row == 7:
                if move.end_col == 0:
                    self.current_castling_rights.wqs = False
                elif move.end_col == 7:
                    self.current_castling_rights.wks = False
        elif move.piece_captured == "br":
            if move.end_row == 0:
                if move.end_col == 0:
                    self.current_castling_rights.bqs = False
                elif move.end_col == 7:
                    self.current_castling_rights.bks = False

    def get_valid_moves(self, update_status=True):
        moves = []
        self.in_check_flag, self.pins, self.checks = self.check_for_pins_and_checks()

        if self.white_to_move:
            king_r, king_c = self.white_king_loc
        else:
            king_r, king_c = self.black_king_loc

        if self.in_check_flag:
            if len(self.checks) == 1:
                moves = self.get_all_possible_moves(attack_only=True)
                check = self.checks[0]
                check_r, check_c = check[0], check[1]
                piece_checking = self.board[check_r][check_c]
                valid_squares = []
                if piece_checking[1] == "n":
                    valid_squares = [(check_r, check_c)]
                else:
                    for i in range(1, 8):
                        valid_sq = (king_r + check[2] * i, king_c + check[3] * i)
                        valid_squares.append(valid_sq)
                        if valid_sq[0] == check_r and valid_sq[1] == check_c:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != "k":
                        if (moves[i].end_row, moves[i].end_col) not in valid_squares:
                            moves.pop(i)
            else:
                self.get_king_moves(king_r, king_c, moves, attack_only=True)
        else:
            moves = self.get_all_possible_moves(attack_only=True)

        moves = self.filter_king_safe_moves(moves)

        if update_status:
            self.update_game_status(moves)
        return moves

    def filter_king_safe_moves(self, moves):
        safe_moves = []
        for move in moves:
            self.make_move(move)
            moved_white = move.piece_moved[0] == "w"
            if moved_white:
                king_r, king_c = self.white_king_loc
            else:
                king_r, king_c = self.black_king_loc
            if not self._square_attacked(king_r, king_c, not moved_white):
                safe_moves.append(move)
            self.undo_move()
        return safe_moves

    def in_check(self):
        if self.white_to_move:
            king_r, king_c = self.white_king_loc
            return self._square_attacked(king_r, king_c, False)
        king_r, king_c = self.black_king_loc
        return self._square_attacked(king_r, king_c, True)

    def _square_attacked(self, row, col, by_white):
        """Return True if (row,col) is attacked by pieces of color by_white."""
        direction = -1 if by_white else 1
        for dc in (-1, 1):
            ar, ac = row + direction, col + dc
            if 0 <= ar < 8 and 0 <= ac < 8:
                piece = self.board[ar][ac]
                if piece and piece[0] == ("w" if by_white else "b") and piece[1] == "p":
                    return True

        knight_offsets = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        for dr, dc in knight_offsets:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = self.board[nr][nc]
                if piece and piece[0] == ("w" if by_white else "b") and piece[1] == "n":
                    return True

        king_offsets = (
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        )
        for dr, dc in king_offsets:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                piece = self.board[nr][nc]
                if piece and piece[0] == ("w" if by_white else "b") and piece[1] == "k":
                    return True

        directions = (
            (-1, 0),
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        )
        for j, (dr, dc) in enumerate(directions):
            for i in range(1, 8):
                nr, nc = row + dr * i, col + dc * i
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                piece = self.board[nr][nc]
                if not piece:
                    continue
                if piece[0] != ("w" if by_white else "b"):
                    break
                ptype = piece[1]
                if ptype == "q":
                    return True
                if 0 <= j <= 3 and ptype == "r":
                    return True
                if 4 <= j <= 7 and ptype == "b":
                    return True
                break
        return False

    def square_under_attack(self, row, col):
        """Used for castling: is square attacked by opponent?"""
        attacker_is_white = not self.white_to_move
        return self._square_attacked(row, col, attacker_is_white)

    def get_all_possible_moves(self, attack_only=False):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not piece:
                    continue
                turn = piece[0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    ptype = piece[1]
                    if ptype == "p":
                        self.get_pawn_moves(r, c, moves)
                    elif ptype == "n":
                        self.get_knight_moves(r, c, moves)
                    elif ptype == "b":
                        self.get_bishop_moves(r, c, moves)
                    elif ptype == "r":
                        self.get_rook_moves(r, c, moves)
                    elif ptype == "q":
                        self.get_queen_moves(r, c, moves)
                    elif ptype == "k":
                        self.get_king_moves(r, c, moves, attack_only=attack_only)
        return moves

    def check_for_pins_and_checks(self):
        pins = []
        checks = []
        in_check = False
        if self.white_to_move:
            enemy, ally = "b", "w"
            start_r, start_c = self.white_king_loc
        else:
            enemy, ally = "w", "b"
            start_r, start_c = self.black_king_loc

        directions = (
            (-1, 0),
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        )
        for j, d in enumerate(directions):
            possible_pin = ()
            for i in range(1, 8):
                end_r = start_r + d[0] * i
                end_c = start_c + d[1] * i
                if not (0 <= end_r < 8 and 0 <= end_c < 8):
                    break
                end_piece = self.board[end_r][end_c]
                if end_piece and end_piece[0] == ally and end_piece[1] != "k":
                    if possible_pin == ():
                        possible_pin = (end_r, end_c, d[0], d[1])
                    else:
                        break
                elif end_piece and end_piece[0] == enemy:
                    ptype = end_piece[1]
                    if (
                        (0 <= j <= 3 and ptype == "r")
                        or (4 <= j <= 7 and ptype == "b")
                        or (
                            i == 1
                            and ptype == "p"
                            and ((enemy == "w" and 6 <= j <= 7) or (enemy == "b" and 4 <= j <= 5))
                        )
                        or ptype == "q"
                        or (i == 1 and ptype == "k")
                    ):
                        if possible_pin == ():
                            in_check = True
                            checks.append((end_r, end_c, d[0], d[1]))
                            break
                        pins.append(possible_pin)
                        break
                    break

        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        for m in knight_moves:
            end_r = start_r + m[0]
            end_c = start_c + m[1]
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece and end_piece[0] == enemy and end_piece[1] == "n":
                    in_check = True
                    checks.append((end_r, end_c, m[0], m[1]))
        return in_check, pins, checks

    def is_pinned(self, row, col):
        for p in self.pins:
            if p[0] == row and p[1] == col:
                return True, p
        return False, ()

    def get_pawn_moves(self, row, col, moves):
        pinned, pin_d = self.is_pinned(row, col)

        if self.white_to_move:
            if row - 1 >= 0 and self.board[row - 1][col] is None:
                if not pinned or pin_d in ((-1, 0), (1, 0)):
                    if row == 1:
                        for promo in ("wq", "wr", "wb", "wn"):
                            moves.append(Move((row, col), (row - 1, col), self.board, promotion=promo))
                    else:
                        moves.append(Move((row, col), (row - 1, col), self.board))
                        if row == 6 and self.board[row - 2][col] is None:
                            moves.append(Move((row, col), (row - 2, col), self.board))

            if col - 1 >= 0:
                if not pinned or pin_d in ((-1, -1), (1, 1)):
                    target = self.board[row - 1][col - 1]
                    if target and target[0] == "b":
                        if row == 1:
                            for promo in ("wq", "wr", "wb", "wn"):
                                moves.append(
                                    Move((row, col), (row - 1, col - 1), self.board, promotion=promo)
                                )
                        else:
                            moves.append(Move((row, col), (row - 1, col - 1), self.board))
                    elif (row - 1, col - 1) == self.en_passant_possible:
                        moves.append(Move((row, col), (row - 1, col - 1), self.board, is_en_passant=True))

            if col + 1 <= 7:
                if not pinned or pin_d in ((-1, 1), (1, -1)):
                    target = self.board[row - 1][col + 1]
                    if target and target[0] == "b":
                        if row == 1:
                            for promo in ("wq", "wr", "wb", "wn"):
                                moves.append(
                                    Move((row, col), (row - 1, col + 1), self.board, promotion=promo)
                                )
                        else:
                            moves.append(Move((row, col), (row - 1, col + 1), self.board))
                    elif (row - 1, col + 1) == self.en_passant_possible:
                        moves.append(Move((row, col), (row - 1, col + 1), self.board, is_en_passant=True))
        else:
            if row + 1 <= 7 and self.board[row + 1][col] is None:
                if not pinned or pin_d in ((1, 0), (-1, 0)):
                    if row == 6:
                        for promo in ("bq", "br", "bb", "bn"):
                            moves.append(Move((row, col), (row + 1, col), self.board, promotion=promo))
                    else:
                        moves.append(Move((row, col), (row + 1, col), self.board))
                        if row == 1 and self.board[row + 2][col] is None:
                            moves.append(Move((row, col), (row + 2, col), self.board))

            if col - 1 >= 0:
                if not pinned or pin_d in ((1, -1), (-1, 1)):
                    target = self.board[row + 1][col - 1]
                    if target and target[0] == "w":
                        if row == 6:
                            for promo in ("bq", "br", "bb", "bn"):
                                moves.append(
                                    Move((row, col), (row + 1, col - 1), self.board, promotion=promo)
                                )
                        else:
                            moves.append(Move((row, col), (row + 1, col - 1), self.board))
                    elif (row + 1, col - 1) == self.en_passant_possible:
                        moves.append(Move((row, col), (row + 1, col - 1), self.board, is_en_passant=True))

            if col + 1 <= 7:
                if not pinned or pin_d in ((1, 1), (-1, -1)):
                    target = self.board[row + 1][col + 1]
                    if target and target[0] == "w":
                        if row == 6:
                            for promo in ("bq", "br", "bb", "bn"):
                                moves.append(
                                    Move((row, col), (row + 1, col + 1), self.board, promotion=promo)
                                )
                        else:
                            moves.append(Move((row, col), (row + 1, col + 1), self.board))
                    elif (row + 1, col + 1) == self.en_passant_possible:
                        moves.append(Move((row, col), (row + 1, col + 1), self.board, is_en_passant=True))

    def get_piece_moves(self, row, col, moves, directions):
        pinned, pin_d = self.is_pinned(row, col)
        enemy_color = "b" if self.white_to_move else "w"
        for d in directions:
            if not pinned or pin_d == d or pin_d == (-d[0], -d[1]):
                for i in range(1, 8):
                    end_r = row + d[0] * i
                    end_c = col + d[1] * i
                    if not (0 <= end_r < 8 and 0 <= end_c < 8):
                        break
                    end_piece = self.board[end_r][end_c]
                    if end_piece is None:
                        moves.append(Move((row, col), (end_r, end_c), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row, col), (end_r, end_c), self.board))
                        break
                    else:
                        break

    def get_rook_moves(self, row, col, moves):
        self.get_piece_moves(row, col, moves, ((-1, 0), (0, -1), (1, 0), (0, 1)))

    def get_bishop_moves(self, row, col, moves):
        self.get_piece_moves(row, col, moves, ((-1, -1), (-1, 1), (1, -1), (1, 1)))

    def get_queen_moves(self, row, col, moves):
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_knight_moves(self, row, col, moves):
        pinned, _ = self.is_pinned(row, col)
        if pinned:
            return
        enemy_color = "b" if self.white_to_move else "w"
        directions = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        for d in directions:
            end_r = row + d[0]
            end_c = col + d[1]
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece is None or end_piece[0] == enemy_color:
                    moves.append(Move((row, col), (end_r, end_c), self.board))

    def get_king_moves(self, row, col, moves, attack_only=False):
        ally_color = "w" if self.white_to_move else "b"
        directions = (
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        )

        for d in directions:
            end_r = row + d[0]
            end_c = col + d[1]
            if not (0 <= end_r < 8 and 0 <= end_c < 8):
                continue
            end_piece = self.board[end_r][end_c]
            if end_piece is None or end_piece[0] != ally_color:
                if attack_only:
                    moves.append(Move((row, col), (end_r, end_c), self.board))
                else:
                    if ally_color == "w":
                        self.white_king_loc = (end_r, end_c)
                    else:
                        self.black_king_loc = (end_r, end_c)
                    in_check, _, _ = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move((row, col), (end_r, end_c), self.board))
                    if ally_color == "w":
                        self.white_king_loc = (row, col)
                    else:
                        self.black_king_loc = (row, col)

        if not attack_only:
            self.get_castle_moves(row, col, moves, ally_color)

    def get_castle_moves(self, row, col, moves, ally_color):
        if self.in_check_flag:
            return
        if (self.white_to_move and self.current_castling_rights.wks) or (
            not self.white_to_move and self.current_castling_rights.bks
        ):
            self.get_kingside_castle_moves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
            not self.white_to_move and self.current_castling_rights.bqs
        ):
            self.get_queenside_castle_moves(row, col, moves)

    def get_kingside_castle_moves(self, row, col, moves):
        if self.board[row][col + 1] is None and self.board[row][col + 2] is None:
            if not self.square_under_attack(row, col) and not self.square_under_attack(
                row, col + 1
            ) and not self.square_under_attack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle=True))

    def get_queenside_castle_moves(self, row, col, moves):
        if (
            self.board[row][col - 1] is None
            and self.board[row][col - 2] is None
            and self.board[row][col - 3] is None
        ):
            if not self.square_under_attack(row, col) and not self.square_under_attack(
                row, col - 1
            ) and not self.square_under_attack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle=True))
