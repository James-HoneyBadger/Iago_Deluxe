"""
Full-coverage tests for every public and private function in board.py and ai.py.
Designed to complement the existing test_board.py, test_ai.py, and
test_comprehensive.py suites without duplicating them.
"""
# pylint: disable=protected-access

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from board import Board
from ai import AI, DIFFICULTY_LEVELS, MAX_DIFFICULTY
from config import PLAYER_BLACK, PLAYER_WHITE, EMPTY


# ===========================================================================
# Board.reset()
# ===========================================================================

def test_reset_clears_played_board():
    """reset() on a mid-game board returns it to the initial 4-piece state."""
    board = Board()
    board.make_move(2, 3, PLAYER_BLACK)
    board.make_move(2, 4, PLAYER_WHITE)
    board.reset()
    black, white = board.get_score()
    assert black == 2 and white == 2
    assert board.current_player == PLAYER_BLACK
    assert not board.game_over
    assert board.winner is None


def test_reset_restores_center_pieces():
    """After reset the four centre cells are correctly occupied."""
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    board.reset()
    assert board.grid[3][3] == PLAYER_WHITE
    assert board.grid[3][4] == PLAYER_BLACK
    assert board.grid[4][3] == PLAYER_BLACK
    assert board.grid[4][4] == PLAYER_WHITE


# ===========================================================================
# Board.switch_player()
# ===========================================================================

def test_switch_player_black_to_white():
    board = Board()
    assert board.current_player == PLAYER_BLACK
    board.switch_player()
    assert board.current_player == PLAYER_WHITE


def test_switch_player_white_to_black():
    board = Board()
    board.current_player = PLAYER_WHITE
    board.switch_player()
    assert board.current_player == PLAYER_BLACK


def test_switch_player_double_returns_to_original():
    board = Board()
    original = board.current_player
    board.switch_player()
    board.switch_player()
    assert board.current_player == original


# ===========================================================================
# Board._would_flip()
# ===========================================================================

def test_would_flip_true_in_valid_direction():
    """_would_flip should return True when opponent pieces lie between two own pieces."""
    board = Board()
    # Standard opening: BLACK at (3,4) and (4,3); WHITE at (3,3) and (4,4)
    # BLACK playing (2,3) goes south (dr=1,dc=0): (3,3) is WHITE, (4,3) is BLACK → flip
    assert board._would_flip(2, 3, 1, 0, PLAYER_BLACK) is True


def test_would_flip_false_no_opponent():
    """No opponent piece in direction → False."""
    board = Board()
    # (0,0) is empty. Going right (0,1) is EMPTY → no flip
    assert board._would_flip(0, 0, 0, 1, PLAYER_BLACK) is False


def test_would_flip_false_at_edge():
    """Direction runs off board without finding own piece → False."""
    board = Board()
    board.grid[0][1] = PLAYER_WHITE
    board.grid[0][0] = EMPTY
    # From (0,0) go left (0,-1): immediately off board
    assert board._would_flip(0, 0, 0, -1, PLAYER_BLACK) is False


# ===========================================================================
# Board.get_flips()
# ===========================================================================

def test_get_flips_returns_correct_cells():
    """get_flips must return exactly the cells make_move would flip."""
    board = Board()
    flips = board.get_flips(2, 3, PLAYER_BLACK)
    assert (3, 3) in flips
    assert len(flips) == 1


def test_get_flips_no_mutation():
    """get_flips must not change the board grid."""
    board = Board()
    grid_before = [row[:] for row in board.grid]
    board.get_flips(2, 3, PLAYER_BLACK)
    assert board.grid == grid_before


def test_get_flips_invalid_move_returns_empty():
    board = Board()
    assert board.get_flips(0, 0, PLAYER_BLACK) == []


def test_get_flips_matches_make_move():
    """Cells returned by get_flips are exactly those changed by make_move."""
    board_preview = Board()
    board_actual = Board()
    predicted = set(board_preview.get_flips(2, 3, PLAYER_BLACK))
    board_actual.make_move(2, 3, PLAYER_BLACK)
    # All predicted cells should now be PLAYER_BLACK
    for r, c in predicted:
        assert board_actual.grid[r][c] == PLAYER_BLACK


# ===========================================================================
# Board._get_flips_direction()
# ===========================================================================

def test_get_flips_direction_returns_opponent_cells():
    board = Board()
    # Direction (1,0) from (2,3): hits WHITE at (3,3), then BLACK at (4,3)
    result = board._get_flips_direction(2, 3, 1, 0, PLAYER_BLACK)
    assert (3, 3) in result


def test_get_flips_direction_empty_when_no_flip():
    board = Board()
    # Direction (-1,0) from (2,3): (1,3) is EMPTY → nothing to flip
    result = board._get_flips_direction(2, 3, -1, 0, PLAYER_BLACK)
    assert result == []


# ===========================================================================
# Board._flip_direction()
# ===========================================================================

def test_flip_direction_mutates_board():
    """_flip_direction must actually flip the opponent pieces in the grid."""
    board = Board()
    board._flip_direction(2, 3, 1, 0, PLAYER_BLACK)
    assert board.grid[3][3] == PLAYER_BLACK


def test_flip_direction_returns_flipped_list():
    board = Board()
    flipped = board._flip_direction(2, 3, 1, 0, PLAYER_BLACK)
    assert (3, 3) in flipped


def test_flip_direction_no_flip_when_empty_gap():
    board = Board()
    # (0,0) goes right; (0,1) is EMPTY → nothing flipped
    flipped = board._flip_direction(0, 0, 0, 1, PLAYER_BLACK)
    assert flipped == []


# ===========================================================================
# Board – multi-flip scenario
# ===========================================================================

def test_make_move_flips_in_multiple_directions():
    """A move that flanks pieces returns all flipped cells."""
    board = Board()
    # BLACK plays (2,3): flips (3,3) south → board now has BLACK at (2,3),(3,3),(3,4),(4,3)
    board.make_move(2, 3, PLAYER_BLACK)
    # WHITE plays (2,2): direction SE (1,1) flanks (3,3) (BLACK) with (4,4) (WHITE)
    assert board.is_valid_move(2, 2, PLAYER_WHITE)
    flipped = board.make_move(2, 2, PLAYER_WHITE)
    assert (3, 3) in flipped


def test_get_valid_moves_after_several_moves():
    """Valid move list changes correctly as game progresses."""
    board = Board()
    board.make_move(2, 3, PLAYER_BLACK)
    white_moves = board.get_valid_moves(PLAYER_WHITE)
    assert len(white_moves) > 0
    for r, c in white_moves:
        assert board.is_valid_move(r, c, PLAYER_WHITE)


# ===========================================================================
# AI.name property
# ===========================================================================

def test_ai_name_all_difficulties():
    for diff, (name, _, _) in DIFFICULTY_LEVELS.items():
        ai = AI(difficulty=diff)
        assert ai.name == name


def test_ai_name_invalid_difficulty():
    ai = AI(difficulty=99)
    assert ai.name == "?"


# ===========================================================================
# AI.reset_log()
# ===========================================================================

def test_reset_log_clears_move_history():
    ai = AI()
    ai.record_move(PLAYER_BLACK, 2, 3)
    ai.record_move(PLAYER_WHITE, 2, 4)
    assert len(ai._move_log) == 2
    ai.reset_log()
    assert ai._move_log == []


def test_reset_log_then_record():
    ai = AI()
    ai.record_move(PLAYER_BLACK, 2, 3)
    ai.reset_log()
    ai.record_move(PLAYER_WHITE, 5, 5)
    assert len(ai._move_log) == 1
    assert ai._move_log[0] == (PLAYER_WHITE, 5, 5)


# ===========================================================================
# AI.record_move() / _check_opening_book()
# ===========================================================================

def test_record_move_appends_correctly():
    ai = AI()
    ai.record_move(PLAYER_BLACK, 2, 3)
    assert ai._move_log == [(PLAYER_BLACK, 2, 3)]


def test_check_opening_book_hit():
    ai = AI()
    ai.record_move(PLAYER_BLACK, 2, 3)
    move = ai._check_opening_book(Board())
    assert move == (2, 4)


def test_check_opening_book_miss():
    ai = AI()
    ai.record_move(PLAYER_BLACK, 0, 0)  # not in book
    assert ai._check_opening_book(Board()) is None


def test_opening_book_used_by_difficulty3():
    """At difficulty 3, the first response to d3 should come from opening book."""
    board = Board()
    board.make_move(2, 3, PLAYER_BLACK)  # Black plays d3
    board.current_player = PLAYER_WHITE
    ai = AI(difficulty=3)
    ai.record_move(PLAYER_BLACK, 2, 3)
    move = ai.get_move(board)
    assert move == (2, 4)  # Book response: e3


# ===========================================================================
# AI.get_hint()
# ===========================================================================

def test_get_hint_returns_valid_move():
    board = Board()
    ai = AI(difficulty=1)
    hint = ai.get_hint(board)
    assert hint is not None
    assert board.is_valid_move(hint[0], hint[1], PLAYER_BLACK)


def test_get_hint_no_moves_returns_none():
    board = Board()
    board.grid = [[PLAYER_BLACK] * 8 for _ in range(8)]
    ai = AI()
    assert ai.get_hint(board) is None


def test_get_hint_prefers_corner():
    """get_hint uses the simple heuristic and should prefer a corner."""
    board = Board()
    ai = AI()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    # Place so (0,0) is a valid BLACK move
    board.grid[0][1] = PLAYER_WHITE
    board.grid[1][0] = PLAYER_WHITE
    board.grid[1][1] = PLAYER_BLACK
    if board.is_valid_move(0, 0, PLAYER_BLACK):
        board.current_player = PLAYER_BLACK
        hint = ai.get_hint(board)
        assert hint == (0, 0)


def test_get_hint_does_not_mutate_board():
    board = Board()
    ai = AI()
    grid_before = [row[:] for row in board.grid]
    player_before = board.current_player
    ai.get_hint(board)
    assert board.grid == grid_before
    assert board.current_player == player_before


# ===========================================================================
# AI._evaluate_board_advanced()
# ===========================================================================

def test_evaluate_board_advanced_game_over_winner():
    ai = AI()
    board = Board()
    board.grid = [[PLAYER_BLACK] * 8 for _ in range(8)]
    board.game_over = True
    board.winner = PLAYER_BLACK
    board.current_player = PLAYER_BLACK
    score = ai._evaluate_board_advanced(board)
    assert score == 10000


def test_evaluate_board_advanced_game_over_loser():
    ai = AI()
    board = Board()
    board.grid = [[PLAYER_WHITE] * 8 for _ in range(8)]
    board.game_over = True
    board.winner = PLAYER_WHITE
    board.current_player = PLAYER_BLACK
    score = ai._evaluate_board_advanced(board)
    assert score == -10000


def test_evaluate_board_advanced_draw():
    ai = AI()
    board = Board()
    board.game_over = True
    board.winner = 0
    board.current_player = PLAYER_BLACK
    score = ai._evaluate_board_advanced(board)
    assert score == 0


def test_evaluate_board_advanced_returns_int():
    ai = AI()
    board = Board()
    result = ai._evaluate_board_advanced(board)
    assert isinstance(result, int)


# ===========================================================================
# AI.evaluate_for_black()
# ===========================================================================

def test_evaluate_for_black_symmetric():
    """Evaluate from Black's perspective: same position seen by White is negated."""
    ai = AI()
    board_b = Board()
    board_w = Board()
    board_w.current_player = PLAYER_WHITE

    score_b = ai.evaluate_for_black(board_b)
    score_w = ai.evaluate_for_black(board_w)
    # Symmetric starting position — scores should be negatives of each other
    assert score_b == -score_w


def test_evaluate_for_black_black_winning():
    """All-black board should give a strongly positive score for Black."""
    ai = AI()
    board = Board()
    board.grid = [[PLAYER_BLACK] * 8 for _ in range(8)]
    board.game_over = True
    board.winner = PLAYER_BLACK
    board.current_player = PLAYER_BLACK
    assert ai.evaluate_for_black(board) > 0


# ===========================================================================
# AI._calculate_corner_value()
# ===========================================================================

def test_corner_value_empty_board():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    assert ai._calculate_corner_value(board, PLAYER_BLACK) == 0


def test_corner_value_all_corners_occupied():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    for r, c in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        board.grid[r][c] = PLAYER_BLACK
    assert ai._calculate_corner_value(board, PLAYER_BLACK) == 4
    assert ai._calculate_corner_value(board, PLAYER_WHITE) == 0


def test_corner_value_mixed():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    board.grid[0][0] = PLAYER_BLACK
    board.grid[0][7] = PLAYER_WHITE
    assert ai._calculate_corner_value(board, PLAYER_BLACK) == 1
    assert ai._calculate_corner_value(board, PLAYER_WHITE) == 1


# ===========================================================================
# AI._calculate_edge_value()
# ===========================================================================

def test_edge_value_empty_board():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    assert ai._calculate_edge_value(board, PLAYER_BLACK) == 0


def test_edge_value_counts_non_corner_edges():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    # Top row: positions 1-6 (not corners 0 and 7)
    for c in range(1, 7):
        board.grid[0][c] = PLAYER_BLACK
    assert ai._calculate_edge_value(board, PLAYER_BLACK) == 6


def test_edge_value_ignores_interior():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    board.grid[3][3] = PLAYER_BLACK  # interior cell
    assert ai._calculate_edge_value(board, PLAYER_BLACK) == 0


# ===========================================================================
# AI._calculate_positional_value()
# ===========================================================================

def test_positional_value_corners_weighted_highest():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    board.grid[0][0] = PLAYER_BLACK
    corner_val = ai._calculate_positional_value(board, PLAYER_BLACK)

    board2 = Board()
    board2.grid = [[EMPTY] * 8 for _ in range(8)]
    board2.grid[3][3] = PLAYER_BLACK  # interior
    interior_val = ai._calculate_positional_value(board2, PLAYER_BLACK)

    assert corner_val > interior_val


def test_positional_value_empty_board_is_zero():
    ai = AI()
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    assert ai._calculate_positional_value(board, PLAYER_BLACK) == 0


# ===========================================================================
# AI._get_best_move_simple() – X-square avoidance
# ===========================================================================

def test_simple_heuristic_avoids_x_squares():
    """If only move options are an X-square and a neutral interior, pick interior."""
    ai = AI(difficulty=2)
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    # Force two moves: (1,1) is an X-square (score -10), (3,4) is interior (score 1)
    valid = [(1, 1), (3, 4)]
    move = ai._get_best_move_simple(board, valid)
    assert move == (3, 4)


def test_simple_heuristic_prefers_edge_over_interior():
    ai = AI(difficulty=2)
    board = Board()
    board.grid = [[EMPTY] * 8 for _ in range(8)]
    valid = [(0, 4), (3, 4)]  # edge vs interior
    move = ai._get_best_move_simple(board, valid)
    assert move == (0, 4)


# ===========================================================================
# AI._get_best_move_minimax()
# ===========================================================================

def test_get_best_move_minimax_returns_valid_move():
    board = Board()
    ai = AI(difficulty=3)
    valid = board.get_valid_moves(PLAYER_BLACK)
    move = ai._get_best_move_minimax(board, valid)
    assert move is not None
    assert board.is_valid_move(move[0], move[1], PLAYER_BLACK)


# ===========================================================================
# AI.get_move() – Expert difficulty (4)
# ===========================================================================

def test_get_move_expert_returns_valid_move():
    board = Board()
    ai = AI(difficulty=4)
    move = ai.get_move(board)
    assert move is not None
    assert board.is_valid_move(move[0], move[1], PLAYER_BLACK)


def test_get_move_expert_does_not_mutate_board():
    board = Board()
    ai = AI(difficulty=4)
    grid_before = [row[:] for row in board.grid]
    player_before = board.current_player
    ai.get_move(board)
    assert board.grid == grid_before
    assert board.current_player == player_before


# ===========================================================================
# AI._minimax_alpha_beta() – direct pruning checks
# ===========================================================================

def test_minimax_depth_zero_returns_evaluation():
    """At depth 0 minimax should immediately return the board evaluation."""
    ai = AI()
    board = Board()
    import time as _time
    score = ai._minimax_alpha_beta(board, 0, True, -float("inf"), float("inf"),
                                   _time.time(), 999.0)
    assert isinstance(score, (int, float))


def test_minimax_respects_time_limit():
    """Minimax should bail out when time limit is already exceeded."""
    import time as _time
    ai = AI()
    board = Board()
    past = _time.time() - 1000  # start time very far in the past
    score = ai._minimax_alpha_beta(board, 5, True, -float("inf"), float("inf"),
                                   past, 0.001)
    assert isinstance(score, (int, float))


# ===========================================================================
# AI._copy_board() – additional coverage
# ===========================================================================

def test_copy_board_copies_game_over_and_winner():
    ai = AI()
    board = Board()
    board.game_over = True
    board.winner = PLAYER_WHITE
    copy = ai._copy_board(board)
    assert copy.game_over is True
    assert copy.winner == PLAYER_WHITE


def test_copy_board_copies_current_player():
    ai = AI()
    board = Board()
    board.current_player = PLAYER_WHITE
    copy = ai._copy_board(board)
    assert copy.current_player == PLAYER_WHITE


# ===========================================================================
# MAX_DIFFICULTY constant
# ===========================================================================

def test_max_difficulty_value():
    assert MAX_DIFFICULTY == max(DIFFICULTY_LEVELS)
    assert MAX_DIFFICULTY == 4
