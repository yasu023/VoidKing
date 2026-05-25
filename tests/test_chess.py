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


def set_position(b, pieces, white_to_move=True, rights=None):
    b.board = [[None] * 8 for _ in range(8)]
    for square, piece in pieces.items():
        row, col = square
        b.board[row][col] = piece
        if piece == "wk":
            b.white_king_loc = square
        elif piece == "bk":
            b.black_king_loc = square
    b.white_to_move = white_to_move
    b.en_passant_possible = ()
    b.en_passant_log = [()]
    if rights is None:
        rights = b.current_castling_rights.__class__(False, False, False, False)
    b.current_castling_rights = rights
    b.castle_rights_log = [
        b.current_castling_rights.__class__(rights.wks, rights.bks, rights.wqs, rights.bqs)
    ]
    b.halfmove_clock = 0
    b.halfmove_clock_log = [0]
    b.position_history = [b.get_board_hash()]
    b.checkmate = False
    b.stalemate = False
    b.is_game_over = False
    b.game_over_reason = ""


def castle_targets(moves):
    return {(m.start_row, m.start_col, m.end_row, m.end_col) for m in moves if m.is_castle}


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


def test_legal_castling_white_and_black_both_sides():
    b = Board()
    rights = b.current_castling_rights.__class__(True, True, True, True)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (7, 7): "wr",
            (0, 4): "bk",
            (0, 0): "br",
            (0, 7): "br",
        },
        white_to_move=True,
        rights=rights,
    )
    moves = b.get_valid_moves()
    assert (7, 4, 7, 6) in castle_targets(moves)
    assert (7, 4, 7, 2) in castle_targets(moves)

    castle = next(m for m in moves if m.is_castle and m.end_col == 6)
    before_hash = b.get_board_hash()
    b.make_move(castle)
    assert b.board[7][6] == "wk"
    assert b.board[7][5] == "wr"
    assert b.board[7][7] is None
    assert not b.current_castling_rights.wks
    assert not b.current_castling_rights.wqs
    b.undo_move()
    assert b.get_board_hash() == before_hash
    assert b.board[7][4] == "wk"
    assert b.board[7][7] == "wr"

    b.white_to_move = False
    b.position_history = [b.get_board_hash()]
    moves = b.get_valid_moves()
    assert (0, 4, 0, 6) in castle_targets(moves)
    assert (0, 4, 0, 2) in castle_targets(moves)


def test_castling_illegal_while_in_check():
    b = Board()
    rights = b.current_castling_rights.__class__(True, False, True, False)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (7, 7): "wr",
            (0, 0): "bk",
            (5, 4): "br",
        },
        rights=rights,
    )
    assert castle_targets(b.get_valid_moves()) == set()


def test_castling_illegal_through_attacked_square():
    b = Board()
    rights = b.current_castling_rights.__class__(True, False, True, False)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (7, 7): "wr",
            (0, 4): "bk",
            (2, 0): "bb",
        },
        rights=rights,
    )
    targets = castle_targets(b.get_valid_moves())
    assert (7, 4, 7, 6) not in targets
    assert (7, 4, 7, 2) in targets


def test_castling_illegal_after_king_or_rook_moved():
    b = Board()
    rights = b.current_castling_rights.__class__(True, False, True, False)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (7, 7): "wr",
            (0, 4): "bk",
        },
        rights=rights,
    )

    b.make_move(Move((7, 7), (7, 6), b.board))
    b.make_move(Move((0, 4), (0, 3), b.board))
    b.make_move(Move((7, 6), (7, 7), b.board))
    b.make_move(Move((0, 3), (0, 4), b.board))
    targets = castle_targets(b.get_valid_moves())
    assert (7, 4, 7, 6) not in targets
    assert (7, 4, 7, 2) in targets

    b.make_move(Move((7, 4), (7, 3), b.board))
    b.make_move(Move((0, 4), (0, 3), b.board))
    b.make_move(Move((7, 3), (7, 4), b.board))
    b.make_move(Move((0, 3), (0, 4), b.board))
    assert castle_targets(b.get_valid_moves()) == set()


def test_castling_requires_actual_rook():
    b = Board()
    rights = b.current_castling_rights.__class__(True, False, True, False)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (0, 4): "bk",
        },
        rights=rights,
    )
    targets = castle_targets(b.get_valid_moves())
    assert (7, 4, 7, 6) not in targets
    assert (7, 4, 7, 2) in targets


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


def test_ai_search_handles_castling_state():
    from ai import AI

    b = Board()
    rights = b.current_castling_rights.__class__(True, True, True, True)
    set_position(
        b,
        {
            (7, 4): "wk",
            (7, 0): "wr",
            (7, 7): "wr",
            (0, 4): "bk",
            (0, 0): "br",
            (0, 7): "br",
        },
        white_to_move=True,
        rights=rights,
    )
    moves = b.get_valid_moves()
    assert castle_targets(moves)

    before_hash = b.get_board_hash()
    for castle in [m for m in moves if m.is_castle]:
        b.make_move(castle)
        b.undo_move()
        assert b.get_board_hash() == before_hash

    ai = AI()
    q = __import__("queue").Queue()
    ai.find_best_move(b, moves, 2, q)
    move, nodes = q.get(timeout=5)
    assert move is not None
    assert any(move == valid for valid in moves)
    assert nodes > 0
    assert b.get_board_hash() == before_hash


def run_all():
    test_start_position()
    test_discovered_check_blocked()
    test_castling_no_recursion()
    test_legal_castling_white_and_black_both_sides()
    test_castling_illegal_while_in_check()
    test_castling_illegal_through_attacked_square()
    test_castling_illegal_after_king_or_rook_moved()
    test_castling_requires_actual_rook()
    test_en_passant()
    test_stalemate_detection()
    test_ai_search()
    test_ai_search_handles_castling_state()
    print("All tests passed.")


if __name__ == "__main__":
    run_all()
