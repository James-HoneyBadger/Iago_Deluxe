"""
board.py – Reversi/Othello board logic for Iago Deluxe.

Contains all pure game rules with no pygame dependency:
  * Move validation and execution
  * Flip detection in all 8 directions
  * Game-over / winner determination
  * Player-skip handling when one side has no moves
"""

from typing import List, Optional, Tuple
from config import EMPTY, PLAYER_BLACK, PLAYER_WHITE, DEFAULT_BOARD_SIZE


class Board:
    """Mutable Reversi board.  ``grid`` is a list-of-lists indexed [row][col]
    where each cell holds EMPTY, PLAYER_BLACK, or PLAYER_WHITE.
    """

    def __init__(self, size: int = DEFAULT_BOARD_SIZE):
        """Create a board of *size* × *size* and place the four starting pieces."""
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.current_player = PLAYER_BLACK
        self.game_over: bool = False
        self.winner: Optional[int] = None
        self.reset()

    def reset(self):
        """Return the board to its initial 4-piece state, ready for a new game."""
        self.grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        # Place initial pieces
        center = self.size // 2
        self.grid[center - 1][center - 1] = PLAYER_WHITE
        self.grid[center - 1][center] = PLAYER_BLACK
        self.grid[center][center - 1] = PLAYER_BLACK
        self.grid[center][center] = PLAYER_WHITE
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.winner = None

    def is_terminal(self) -> bool:
        """Return True when neither player has any legal move (or game_over is
        already set).  Pure query — does not mutate any state."""
        if self.game_over:
            return True
        return (
            not self.get_valid_moves(PLAYER_BLACK)
            and not self.get_valid_moves(PLAYER_WHITE)
        )

    def is_valid_move(self, row: int, col: int, player: int) -> bool:
        """Return True if *player* may legally place at (*row*, *col*).
        Checks bounds, cell occupancy, and that at least one opponent piece
        would be flipped in some direction.
        """
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.grid[row][col] != EMPTY:
            return False

        # Check all 8 directions
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dr, dc in directions:
            if self._would_flip(row, col, dr, dc, player):
                return True

        return False

    def _would_flip(self, row: int, col: int, dr: int, dc: int, player: int) -> bool:
        """Return True if placing *player*'s piece at (*row*, *col*) would flip
        at least one opponent piece in the direction (*dr*, *dc*).
        """
        r, c = row + dr, col + dc
        opponent = 3 - player  # PLAYER_BLACK ↔ PLAYER_WHITE
        found_opponent = False

        while 0 <= r < self.size and 0 <= c < self.size:
            if self.grid[r][c] == EMPTY:
                return False
            if self.grid[r][c] == opponent:
                found_opponent = True
            elif self.grid[r][c] == player:
                return found_opponent
            r += dr
            c += dc

        return False

    def get_valid_moves(self, player: int) -> List[Tuple[int, int]]:
        """Return all (row, col) pairs where *player* has a legal move."""
        moves = []
        for row in range(self.size):
            for col in range(self.size):
                if self.is_valid_move(row, col, player):
                    moves.append((row, col))
        return moves

    def get_flips(self, row: int, col: int, player: int) -> List[Tuple[int, int]]:
        """Return every (row, col) that would be flipped if *player* placed at
        (*row*, *col*).  Does **not** modify the board (used for hover preview).
        Returns an empty list if the move is invalid.
        """
        if not self.is_valid_move(row, col, player):
            return []
        flipped = []
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ]
        for dr, dc in directions:
            flipped.extend(self._get_flips_direction(row, col, dr, dc, player))
        return flipped

    def _get_flips_direction(
        self, row: int, col: int, dr: int, dc: int, player: int
    ) -> List[Tuple[int, int]]:
        """Return the opponent cells that would be captured in direction (*dr*, *dc*)
        if *player* placed at (*row*, *col*).  Pure query, no mutation.
        """
        r, c = row + dr, col + dc
        opponent = 3 - player
        to_flip = []
        while 0 <= r < self.size and 0 <= c < self.size:
            if self.grid[r][c] == opponent:
                to_flip.append((r, c))
            elif self.grid[r][c] == player:
                return to_flip
            else:
                break
            r += dr
            c += dc
        return []

    def make_move(self, row: int, col: int, player: int) -> List[Tuple[int, int]]:
        """Place *player*'s piece at (*row*, *col*), flip all captured opponent
        pieces, switch the active player, and return the list of flipped cells.
        Returns an empty list (without mutating anything) if the move is invalid.
        """
        if not self.is_valid_move(row, col, player):
            return []

        self.grid[row][col] = player
        flipped = []

        # Check all directions and flip pieces
        directions = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for dr, dc in directions:
            flipped.extend(self._flip_direction(row, col, dr, dc, player))

        # Hand control to the next player
        self.switch_player()

        return flipped

    def _flip_direction(
        self, row: int, col: int, dr: int, dc: int, player: int
    ) -> List[Tuple[int, int]]:
        """Walk direction (*dr*, *dc*) from the placed piece; if a bracketing
        own-piece is found, flip every opponent piece in between and return them.
        Returns an empty list if nothing is flipped.
        """
        r, c = row + dr, col + dc
        opponent = 3 - player
        to_flip = []

        while 0 <= r < self.size and 0 <= c < self.size:
            if self.grid[r][c] == opponent:
                to_flip.append((r, c))
            elif self.grid[r][c] == player:
                # Own piece found – commit all pending flips
                for fr, fc in to_flip:
                    self.grid[fr][fc] = player
                return to_flip
            else:
                break
            r += dr
            c += dc

        return []

    def get_score(self) -> Tuple[int, int]:
        """Return (black_count, white_count) by scanning the grid."""
        black = sum(row.count(PLAYER_BLACK) for row in self.grid)
        white = sum(row.count(PLAYER_WHITE) for row in self.grid)
        return black, white

    def check_game_over(self):
        """Determine whether the game has ended.

        * If neither player can move: sets ``game_over = True`` and assigns
          ``winner`` (PLAYER_BLACK, PLAYER_WHITE, or 0 for a draw).
        * If only the *current* player has no moves: passes the turn to the
          opponent and returns False.
        * If the current player has moves: does nothing and returns False.

        Returns True only when the game is freshly declared over.
        """
        black_moves = self.get_valid_moves(PLAYER_BLACK)
        white_moves = self.get_valid_moves(PLAYER_WHITE)

        if not black_moves and not white_moves:
            self.game_over = True
            black_score, white_score = self.get_score()
            if black_score > white_score:
                self.winner = PLAYER_BLACK
            elif white_score > black_score:
                self.winner = PLAYER_WHITE
            else:
                self.winner = 0  # Draw
            return True

        # Current player has no moves – skip their turn
        if not (black_moves if self.current_player == PLAYER_BLACK else white_moves):
            self.current_player = 3 - self.current_player
            return False

        return False

    def switch_player(self):
        """Toggle ``current_player`` between PLAYER_BLACK and PLAYER_WHITE."""
        self.current_player = 3 - self.current_player
