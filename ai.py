import random
import threading
from queue import Queue, Empty
from constants import (
    PIECE_VALUES,
    PAWN_PST,
    KNIGHT_PST,
    BISHOP_PST,
    ROOK_PST,
    QUEEN_PST,
    KING_MID_PST,
    KING_END_PST,
)
from board import Board

CHECKMATE = 100000
STALEMATE = 0
MAX_DEPTH = 5


class AI:
    def __init__(self):
        self.next_move = None
        self.nodes_evaluated = 0
        self.start_depth = 3
        self.transposition = {}

    def clear_transposition(self):
        self.transposition.clear()

    def is_endgame(self, board):
        queens = 0
        minors = 0
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece:
                    if piece[1] == "q":
                        queens += 1
                    elif piece[1] in ("n", "b", "r"):
                        minors += 1
        return queens == 0 or (queens == 2 and minors <= 2)

    def evaluate_board(self, board):
        if board.checkmate:
            return -CHECKMATE if board.white_to_move else CHECKMATE
        if board.stalemate or board.draw_by_fifty_moves or board.draw_by_repetition:
            return STALEMATE

        score = 0
        endgame = self.is_endgame(board)

        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if not piece:
                    continue
                is_white = piece[0] == "w"
                sign = 1 if is_white else -1
                ptype = piece[1]

                score += sign * PIECE_VALUES[ptype]
                pr = r if not is_white else 7 - r
                if ptype == "p":
                    score += sign * PAWN_PST[pr][c]
                elif ptype == "n":
                    score += sign * KNIGHT_PST[pr][c]
                elif ptype == "b":
                    score += sign * BISHOP_PST[pr][c]
                elif ptype == "r":
                    score += sign * ROOK_PST[pr][c]
                elif ptype == "q":
                    score += sign * QUEEN_PST[pr][c]
                elif ptype == "k":
                    if endgame:
                        score += sign * KING_END_PST[pr][c]
                    else:
                        score += sign * KING_MID_PST[pr][c]

        return score

    def order_moves(self, moves):
        def move_score(move):
            score = 0
            if move.piece_captured:
                score += 10 * PIECE_VALUES[move.piece_captured[1]] - PIECE_VALUES[move.piece_moved[1]]
            if move.promotion:
                score += PIECE_VALUES[move.promotion[1]]
            if move.is_castle:
                score += 50
            return score

        return sorted(moves, key=move_score, reverse=True)

    def find_best_move(self, board, valid_moves, depth, result_queue):
        self.next_move = None
        self.nodes_evaluated = 0
        self.start_depth = min(depth, MAX_DEPTH)
        self.clear_transposition()

        search_board = board.copy()
        fresh_moves = search_board.get_valid_moves(update_status=False)
        move_lookup = {m.move_id: m for m in fresh_moves}
        ordered = []
        for m in self.order_moves(valid_moves):
            if m.move_id in move_lookup:
                ordered.append(move_lookup[m.move_id])
        if not ordered:
            ordered = fresh_moves

        if self.start_depth <= 2 and len(ordered) > 1:
            random.shuffle(ordered[: min(6, len(ordered))])

        ordered = self.order_moves(ordered)

        if search_board.white_to_move:
            self.find_move_minimax(search_board, ordered, self.start_depth, -CHECKMATE, CHECKMATE, 1)
        else:
            self.find_move_minimax(search_board, ordered, self.start_depth, -CHECKMATE, CHECKMATE, -1)

        if self.next_move is None and ordered:
            self.next_move = ordered[0]

        result_queue.put((self.next_move, self.nodes_evaluated))

    def find_move_minimax(self, board, valid_moves, depth, alpha, beta, turn_multiplier):
        if depth == 0:
            self.nodes_evaluated += 1
            return turn_multiplier * self._quiescence(board, alpha, beta, turn_multiplier, 3)

        if not valid_moves:
            board.update_game_status([])
            score = turn_multiplier * self.evaluate_board(board)
            board.checkmate = False
            board.stalemate = False
            board.is_game_over = False
            return score

        tt_key = (board.get_board_hash(), depth, alpha, beta)
        cached = self.transposition.get(tt_key)
        if cached is not None:
            return cached

        max_score = -CHECKMATE
        for move in valid_moves:
            board.make_move(move)
            next_moves = board.get_valid_moves(update_status=False)
            score = -self.find_move_minimax(
                board,
                self.order_moves(next_moves),
                depth - 1,
                -beta,
                -alpha,
                -turn_multiplier,
            )
            board.undo_move()

            if score > max_score:
                max_score = score
                if depth == self.start_depth:
                    self.next_move = move

            if max_score > alpha:
                alpha = max_score
            if alpha >= beta:
                break

        self.transposition[tt_key] = max_score
        if len(self.transposition) > 50000:
            self.transposition.clear()
        return max_score

    def _quiescence(self, board, alpha, beta, turn_multiplier, depth_left):
        stand_pat = turn_multiplier * self.evaluate_board(board)
        if depth_left == 0:
            return stand_pat

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        moves = board.get_valid_moves(update_status=False)
        captures = [m for m in moves if m.piece_captured or m.promotion]
        if not captures:
            return stand_pat

        for move in self.order_moves(captures):
            board.make_move(move)
            score = -self._quiescence(board, -beta, -alpha, -turn_multiplier, depth_left - 1)
            board.undo_move()
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha


_ai_worker = None
_ai_thread = None
_ai_queue = None
_ai_lock = threading.Lock()


def start_ai_search(board, valid_moves, depth):
    """Run AI search on a background thread; returns (thread, queue)."""
    global _ai_thread, _ai_queue

    with _ai_lock:
        if _ai_thread is not None and _ai_thread.is_alive():
            return _ai_thread, _ai_queue

    result_queue = Queue(maxsize=1)
    ai = AI()
    search_board = board.copy()

    def run():
        try:
            ai.find_best_move(search_board, valid_moves, depth, result_queue)
        except Exception:
            if valid_moves:
                result_queue.put((valid_moves[0], 0))

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    _ai_thread = thread
    _ai_queue = result_queue
    return thread, result_queue


def cancel_ai_search():
    global _ai_thread, _ai_queue
    with _ai_lock:
        _ai_thread = None
        _ai_queue = None


def poll_ai_result(queue, timeout=0):
    if queue is None:
        return None
    try:
        return queue.get_nowait()
    except Empty:
        return None
