"""
ai.py – AI opponent for Iago Deluxe.

Four selectable difficulty levels:
  1 – Easy   : random legal move
  2 – Medium : instant positional heuristic (corners > edges > centre, avoid X-squares)
  3 – Hard   : iterative-deepening minimax with alpha-beta pruning, 1-second budget
  4 – Expert : same algorithm with a 3-second thinking budget

Levels 3 and 4 also consult a small opening book for the first few moves.
All search is done on throw-away board copies so the live board is never mutated.
"""

import random
import time
from typing import Optional, Tuple, List
from board import Board
from config import PLAYER_BLACK, PLAYER_WHITE


# Maps difficulty level → (display name, unused_depth, think_time_secs)
# think_time=0.0 means the level does not use iterative deepening.
DIFFICULTY_LEVELS = {
    1: ("Easy",   0,  0.0),
    2: ("Medium", 0,  0.0),
    3: ("Hard",   0,  1.0),   # iterative deepening, 1 second
    4: ("Expert", 0,  3.0),   # iterative deepening, 3 seconds
}
MAX_DIFFICULTY = max(DIFFICULTY_LEVELS)

# Opening book: maps the move-log tuple (player, row, col)* → response (row, col).
# Covers White's first reply to each of Black's four standard opening moves,
# plus two second-ply continuations of the Tiger line.
_OPENING_BOOK: dict = {
    ((PLAYER_BLACK, 2, 3),): (2, 4),   # Black d3 → White e3 (Tiger)
    ((PLAYER_BLACK, 3, 2),): (2, 2),   # Black c4 → White c3
    ((PLAYER_BLACK, 4, 5),): (3, 5),   # Black f5 → White f4
    ((PLAYER_BLACK, 5, 4),): (5, 3),   # Black e6 → White d6
    # Second-ply responses (Tiger line continuation)
    ((PLAYER_BLACK, 2, 3), (PLAYER_WHITE, 2, 4), (PLAYER_BLACK, 2, 5)): (3, 5),
    ((PLAYER_BLACK, 2, 3), (PLAYER_WHITE, 2, 4), (PLAYER_BLACK, 4, 2)): (2, 2),
}


class AI:
    """Reversi AI opponent.

    Instantiate with a ``difficulty`` from 1 (Easy) to 4 (Expert).  Call
    ``get_move(board)`` to receive the chosen (row, col), or ``get_hint(board)``
    for an instant best-move suggestion using the quick heuristic.

    ``record_move`` / ``reset_log`` maintain the move history used by the
    opening book; call ``reset_log`` at the start of every new game.
    """

    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty  # 1–4, higher is stronger
        self._move_log: List[Tuple[int, int, int]] = []  # (player, row, col) history

    @property
    def name(self) -> str:
        """Human-readable name of the current difficulty."""
        return DIFFICULTY_LEVELS.get(self.difficulty, ("?", 0, 0))[0]

    def record_move(self, player: int, row: int, col: int):
        """Record a move so the opening book can be consulted."""
        self._move_log.append((player, row, col))

    def reset_log(self):
        """Clear the move log (call on new game)."""
        self._move_log.clear()

    def get_move(self, board: Board) -> Optional[Tuple[int, int]]:
        """Get AI move, using opening book or search as appropriate."""
        valid_moves = board.get_valid_moves(board.current_player)
        if not valid_moves:
            return None

        if self.difficulty == 1:
            return random.choice(valid_moves)

        if self.difficulty == 2:
            return self._get_best_move_simple(board, valid_moves)

        # levels 3 & 4 – check opening book first
        book_move = self._check_opening_book(board)
        if book_move and book_move in valid_moves:
            return book_move

        # Iterative deepening with time limit
        think_time = DIFFICULTY_LEVELS[self.difficulty][2]
        return self._get_move_timed(board, valid_moves, think_time)

    def get_hint(self, board: Board) -> Optional[Tuple[int, int]]:
        """Return the recommended move using the instant positional heuristic.

        This is the same function used by Medium difficulty and runs in O(n²)
        time, making it safe to call every frame without blocking.
        Returns None when no legal moves exist.
        """
        valid_moves = board.get_valid_moves(board.current_player)
        if not valid_moves:
            return None
        return self._get_best_move_simple(board, valid_moves)

    # ------------------------------------------------------------------
    # Opening book
    # ------------------------------------------------------------------

    def _check_opening_book(self, board: Board) -> Optional[Tuple[int, int]]:
        """Return a book move if the current position is in the opening book."""
        key = tuple(self._move_log)
        return _OPENING_BOOK.get(key)

    # ------------------------------------------------------------------
    # Iterative deepening
    # ------------------------------------------------------------------

    def _get_move_timed(
        self, board: Board, valid_moves: List[Tuple[int, int]], time_limit: float
    ) -> Tuple[int, int]:
        """Iterative-deepening search: increase depth 1-15 until *time_limit*
        is consumed, then return the best move found at the deepest complete
        depth.  Guarantees a legal move even if time is up before depth 1.
        """
        start = time.time()
        best_move = valid_moves[0]

        for depth in range(1, 16):
            if time.time() - start >= time_limit * 0.85:
                break
            move = self._search_at_depth(board, valid_moves, depth, start, time_limit)
            if move is not None:
                best_move = move
            if time.time() - start >= time_limit:
                break

        return best_move

    def _search_at_depth(
        self,
        board: Board,
        valid_moves: List[Tuple[int, int]],
        depth: int,
        start: float,
        time_limit: float,
    ) -> Optional[Tuple[int, int]]:
        """Run a single minimax pass at exactly *depth* plies.  Returns the best
        move found so far, or None if the time limit was hit mid-search (the
        caller always has a fallback from the previous iteration).
        """
        best_move = None
        best_score = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        for move in valid_moves:
            if time.time() - start >= time_limit:
                return None
            board_copy = self._copy_board(board)
            board_copy.make_move(move[0], move[1], board.current_player)
            score = self._minimax_alpha_beta(
                board_copy, depth - 1, False, alpha, beta, start, time_limit
            )
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)

        return best_move

    # ------------------------------------------------------------------
    # Simple heuristic (level 2)
    # ------------------------------------------------------------------

    def _get_best_move_simple(
        self, board: Board, valid_moves: List[Tuple[int, int]]
    ) -> Tuple[int, int]:
        """Instant positional heuristic used by Medium difficulty and hints.

        Move scores: corner = 100, X-square = −10, edge = 5, centre = 3, other = 1.
        X-squares are the four cells diagonally adjacent to corners; capturing them
        often gifts the corner to the opponent.
        """
        size = board.size
        corners = [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]
        # X-squares: diagonally adjacent to corners — avoid these
        x_squares = [(1, 1), (1, size-2), (size-2, 1), (size-2, size-2)]
        edges = []
        for i in range(1, size - 1):
            edges.extend([(0, i), (size - 1, i), (i, 0), (i, size - 1)])

        best_move: Tuple[int, int] = valid_moves[0]
        best_score = -999

        for move in valid_moves:
            score = 1
            if move in corners:
                score = 100
            elif move in x_squares:
                score = -10
            elif move in edges:
                score = 5
            else:
                row, col = move
                center_start = size // 2 - 1
                center_end = size // 2 + 1
                in_range = (
                    center_start <= row <= center_end
                    and center_start <= col <= center_end
                )
                if in_range:
                    score = 3

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    # ------------------------------------------------------------------
    # Minimax with alpha-beta
    # ------------------------------------------------------------------

    def _get_best_move_minimax(
        self, board: Board, valid_moves: List[Tuple[int, int]]
    ) -> Tuple[int, int]:
        """Convenience wrapper: run a 1-second iterative-deepening search.
        Retained for legacy compatibility; prefer ``_get_move_timed`` directly.
        """
        return self._get_move_timed(board, valid_moves, 1.0)

    def _minimax_alpha_beta(
        self,
        board: Board,
        depth: int,
        maximizing: bool,
        alpha: float,
        beta: float,
        start: float = 0.0,
        time_limit: float = 999.0,
    ) -> float:
        """Minimax with alpha-beta pruning.

        ``maximizing`` is True when evaluating from the root player's perspective.
        Returns immediately with a static evaluation if:
          * the time budget is exhausted,
          * depth reaches zero, or
          * the position is terminal.
        When the current player has no moves the function passes the turn and
        recurses rather than treating a forced-pass as terminal.
        """
        if time.time() - start >= time_limit:
            return self._evaluate_board_advanced(board)

        if depth == 0 or board.is_terminal():
            return self._evaluate_board_advanced(board)

        valid_moves = board.get_valid_moves(board.current_player)

        if not valid_moves:
            board_copy = self._copy_board(board)
            board_copy.switch_player()
            return self._minimax_alpha_beta(
                board_copy, depth - 1, not maximizing, alpha, beta, start, time_limit
            )

        if maximizing:
            max_eval = -float("inf")
            for move in valid_moves:
                board_copy = self._copy_board(board)
                board_copy.make_move(move[0], move[1], board.current_player)
                eval_score = self._minimax_alpha_beta(
                    board_copy, depth - 1, False, alpha, beta, start, time_limit
                )
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in valid_moves:
                board_copy = self._copy_board(board)
                board_copy.make_move(move[0], move[1], board.current_player)
                eval_score = self._minimax_alpha_beta(
                    board_copy, depth - 1, True, alpha, beta, start, time_limit
                )
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate_board_advanced(self, board: Board) -> int:
        """Static evaluation from the current player's perspective.

        Terminal positions are scored ±10 000.  Open positions combine:
          * material (piece difference × 10)
          * positional weight table (corners 100, edges 10)
          * mobility (legal-move count difference × 10)
          * corner ownership (× 20)
          * non-corner edge ownership (× 5)
        """
        if board.game_over:
            if board.winner == board.current_player:
                return 10000
            elif board.winner == 0:
                return 0
            else:
                return -10000

        black_score, white_score = board.get_score()
        current_player = board.current_player
        opponent = 3 - current_player

        score = (black_score - white_score) if current_player == PLAYER_BLACK \
            else (white_score - black_score)

        positional_value = (
            self._calculate_positional_value(board, current_player)
            - self._calculate_positional_value(board, opponent)
        )
        current_mobility = len(board.get_valid_moves(current_player))
        opponent_mobility = len(board.get_valid_moves(opponent))
        mobility_value = 10 * (current_mobility - opponent_mobility)
        corner_value = (
            self._calculate_corner_value(board, current_player)
            - self._calculate_corner_value(board, opponent)
        )
        edge_value = (
            self._calculate_edge_value(board, current_player)
            - self._calculate_edge_value(board, opponent)
        )

        return (
            score * 10
            + positional_value
            + mobility_value
            + corner_value * 20
            + edge_value * 5
        )

    def evaluate_for_black(self, board: Board) -> int:
        """Return the board evaluation always from Black's point of view.

        Used by the win-probability bar: positive = Black is ahead, negative =
        White is ahead.  The sign is flipped when it's White's turn because
        ``_evaluate_board_advanced`` scores from the current-player's perspective.
        """
        raw = self._evaluate_board_advanced(board)
        if board.current_player == PLAYER_WHITE:
            return -raw
        return raw

    def _calculate_positional_value(self, board: Board, player: int) -> int:
        """Sum position-weight-table values for all of *player*'s pieces.
        Corners = 100, non-corner edges = 10, interior = 0.
        """
        size = board.size
        value = 0
        position_weights = [[0] * size for _ in range(size)]
        position_weights[0][0] = 100
        position_weights[0][size - 1] = 100
        position_weights[size - 1][0] = 100
        position_weights[size - 1][size - 1] = 100
        for i in range(1, size - 1):
            position_weights[0][i] = 10
            position_weights[size - 1][i] = 10
            position_weights[i][0] = 10
            position_weights[i][size - 1] = 10
        for row in range(size):
            for col in range(size):
                if board.grid[row][col] == player:
                    value += position_weights[row][col]
        return value

    def _calculate_corner_value(self, board: Board, player: int) -> int:
        """Return the number of the four corners currently owned by *player*."""
        size = board.size
        corners = [(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)]
        return sum(1 for r, c in corners if board.grid[r][c] == player)

    def _calculate_edge_value(self, board: Board, player: int) -> int:
        """Count non-corner edge cells owned by *player* (top/bottom rows and
        left/right columns, excluding the four corner positions).
        """
        size = board.size
        value = 0
        for col in range(1, size - 1):
            if board.grid[0][col] == player:
                value += 1
            if board.grid[size - 1][col] == player:
                value += 1
        for row in range(1, size - 1):
            if board.grid[row][0] == player:
                value += 1
            if board.grid[row][size - 1] == player:
                value += 1
        return value

    def _copy_board(self, board: Board) -> Board:
        """Return a deep copy of *board* suitable for speculative search.
        Grid rows are shallow-copied (lists of ints), which is sufficient since
        cell values are replaced rather than mutated in place.
        """
        new_board = Board(board.size)
        new_board.grid = [row[:] for row in board.grid]
        new_board.current_player = board.current_player
        new_board.game_over = board.game_over
        new_board.winner = board.winner
        return new_board
