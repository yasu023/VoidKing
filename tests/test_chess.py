"""Automated chess rule and engine tests (no pygame display required)."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()

from board import Board
from move import Move


def test_start_position():
    b = Board()
    moves = b.get_valid_moves()
    assert len(moves) == 20, f"expected 20 opening moves, got {len(moves)}"
    assert not b.is_game_over


def test_discovered_check_blocked():
    b = Board()
    b.board = [[None] * 8 for _ in range(8)]
    b.board[7][4] = "wk"
    b.board[0][4] = "bk"
    b.board[6][4] = "wp"
    b.board[1][4] = "br"
    b.white_king_loc = (7, 4)
    b.black_king_loc = (0, 4)
    b.white_to_move = True
    b.en_passant_possible = ()
    b.en_passant_log = [()]
    b.current_castling_rights = b.current_castling_rights.__class__(False, False, False, False)
    b.castle_rights_log = [b.current_castling_rights]
    b.halfmove_clock = 0
    b.halfmove_clock_log = [0]
    b.position_history = [b.get_board_hash()]
    moves = b.get_valid_moves()
    pawn_moves = [m for m in moves if m.start_row == 6 and m.start_col == 4]
    assert len(pawn_moves) == 0, "pawn must not move into discovered check"


def test_castling_no_recursion():
    b = Board()
    b.board[7][7] = None
    b.board[7][5] = None
    b.board[7][6] = None
    moves = b.get_valid_moves()
    castle = [m for m in moves if m.is_castle]
    assert isinstance(moves, list)


def test_en_passant():
    b = Board()
    b.board = [[None] * 8 for _ in range(8)]
    b.board[7][4] = "wk"
    b.board[0][4] = "bk"
    b.board[3][4] = "wp"  # e5
    b.board[3][3] = "bp"  # d5
    b.white_king_loc = (7, 4)
    b.black_king_loc = (0, 4)
    b.white_to_move = True
    b.en_passant_possible = (2, 3)
    b.en_passant_log = [(), (2, 3)]
    cr = b.current_castling_rights.__class__(False, False, False, False)
    b.current_castling_rights = cr
    b.castle_rights_log = [cr]
    b.halfmove_clock = 0
    b.halfmove_clock_log = [0]
    b.position_history = [b.get_board_hash()]
    moves = b.get_valid_moves()
    ep_moves = [m for m in moves if m.is_en_passant]
    assert len(ep_moves) == 1
    assert ep_moves[0].end_row == 2 and ep_moves[0].end_col == 3


def test_stalemate_detection():
    b = Board()
    b.board = [[None] * 8 for _ in range(8)]
    b.board[0][0] = "bk"
    b.board[2][0] = "wn"
    b.board[3][1] = "wn"
    b.board[2][3] = "wn"
    b.board[7][7] = "wk"
    b.white_king_loc = (7, 7)
    b.black_king_loc = (0, 0)
    b.white_to_move = False
    b.en_passant_possible = ()
    b.en_passant_log = [()]
    cr = b.current_castling_rights.__class__(False, False, False, False)
    b.current_castling_rights = cr
    b.castle_rights_log = [cr]
    b.halfmove_clock = 0
    b.halfmove_clock_log = [0]
    b.position_history = [b.get_board_hash()]
    moves = b.get_valid_moves()
    assert len(moves) == 0
    assert b.stalemate and b.is_game_over


def test_ai_search():
    from ai import AI

    b = Board()
    moves = b.get_valid_moves()
    ai = AI()
    q = __import__("queue").Queue()
    ai.find_best_move(b, moves, 2, q)
    move, nodes = q.get(timeout=5)
    assert move is not None
    assert nodes > 0


def run_all():
    test_start_position()
    test_discovered_check_blocked()
    test_castling_no_recursion()
    test_en_passant()
    test_stalemate_detection()
    test_ai_search()
    print("All tests passed.")


if __name__ == "__main__":
    run_all()
