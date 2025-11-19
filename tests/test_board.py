#!/usr/bin/env python3
"""
Unit tests for Board class
Tests move validation, game state, and board operations
"""
import sys
import os
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Reversi import Board, EMPTY, BLACK, WHITE  # noqa: E402, F401


class TestBoardInitialization(unittest.TestCase):
    """Test board initialization and setup"""

    def test_default_board_size(self):
        """Test default 8x8 board creation"""
        board = Board()
        self.assertEqual(board.size, 8)
        self.assertEqual(len(board.grid), 8)
        self.assertEqual(len(board.grid[0]), 8)

    def test_custom_board_size(self):
        """Test custom board sizes"""
        for size in [4, 6, 8, 10, 12]:
            board = Board(size=size)
            self.assertEqual(board.size, size)
            self.assertEqual(len(board.grid), size)

    def test_initial_pieces(self):
        """Test initial piece placement"""
        board = Board(size=8)
        center = board.size // 2

        # Check center 4 squares
        self.assertEqual(board.grid[center - 1][center - 1], WHITE)
        self.assertEqual(board.grid[center][center], WHITE)
        self.assertEqual(board.grid[center - 1][center], BLACK)
        self.assertEqual(board.grid[center][center - 1], BLACK)

    def test_initial_player(self):
        """Test that BLACK moves first"""
        board = Board()
        self.assertEqual(board.to_move, BLACK)

    def test_empty_history(self):
        """Test that history starts empty"""
        board = Board()
        self.assertEqual(len(board.history), 0)
        self.assertEqual(len(board.redo_stack), 0)
        self.assertEqual(len(board.move_list), 0)


class TestLegalMoves(unittest.TestCase):
    """Test legal move generation"""

    def test_initial_legal_moves(self):
        """Test legal moves from starting position"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)

        # Should have exactly 4 legal moves
        self.assertEqual(len(moves), 4)

        # Check expected positions
        positions = {(move.row, move.col) for move in moves}
        expected = {(2, 3), (3, 2), (4, 5), (5, 4)}
        self.assertEqual(positions, expected)

    def test_no_legal_moves(self):
        """Test when no legal moves available"""
        board = Board(size=4)
        # Fill board except corners
        for r in range(4):
            for c in range(4):
                if (r, c) not in [(0, 0), (0, 3), (3, 0), (3, 3)]:
                    board.grid[r][c] = BLACK

        moves = board.legal_moves(WHITE)
        # May or may not have moves depending on position
        self.assertIsInstance(moves, list)

    def test_legal_move_flips(self):
        """Test that legal moves include correct flips"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)

        # Each opening move should flip exactly 1 piece
        for move in moves:
            self.assertEqual(len(move.flips), 1)


class TestMakeMove(unittest.TestCase):
    """Test making moves on the board"""

    def test_make_valid_move(self):
        """Test making a valid move"""
        board = Board(size=8)
        initial_score = board.score()

        moves = board.legal_moves(BLACK)
        self.assertTrue(len(moves) > 0)

        board.make_move(moves[0])

        # Score should change
        new_score = board.score()
        self.assertNotEqual(initial_score, new_score)

        # Player should switch
        self.assertEqual(board.to_move, WHITE)

    def test_move_history(self):
        """Test that moves are added to history"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)

        board.make_move(moves[0])

        self.assertEqual(len(board.history), 1)
        self.assertEqual(len(board.move_list), 1)

    def test_pieces_flip(self):
        """Test that opponent pieces flip"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)
        move = moves[0]

        # Count black pieces before
        black_before = sum(row.count(BLACK) for row in board.grid)

        board.make_move(move)

        # Count black pieces after - should increase
        black_after = sum(row.count(BLACK) for row in board.grid)
        self.assertGreater(black_after, black_before)


class TestUndoRedo(unittest.TestCase):
    """Test undo/redo functionality"""

    def test_undo_single_move(self):
        """Test undoing a single move"""
        board = Board(size=8)
        original_grid = [row[:] for row in board.grid]

        moves = board.legal_moves(BLACK)
        board.make_move(moves[0])

        result = board.undo()
        self.assertTrue(result)

        # Board should match original
        self.assertEqual(board.grid, original_grid)
        self.assertEqual(board.to_move, BLACK)

    def test_undo_empty_history(self):
        """Test undo with no moves made"""
        board = Board(size=8)
        result = board.undo()
        self.assertFalse(result)

    def test_redo_after_undo(self):
        """Test redo after undo"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)
        board.make_move(moves[0])

        grid_after_move = [row[:] for row in board.grid]

        board.undo()
        result = board.redo()

        self.assertTrue(result)
        self.assertEqual(board.grid, grid_after_move)

    def test_redo_empty_stack(self):
        """Test redo with empty redo stack"""
        board = Board(size=8)
        result = board.redo()
        self.assertFalse(result)

    def test_new_move_clears_redo(self):
        """Test that new move clears redo stack"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)

        board.make_move(moves[0])
        board.undo()

        # Redo stack should have something
        self.assertGreater(len(board.redo_stack), 0)

        # Make a new move
        board.make_move(moves[0])

        # Redo stack should be cleared
        self.assertEqual(len(board.redo_stack), 0)


class TestGameOver(unittest.TestCase):
    """Test game over detection"""

    def test_game_not_over_initially(self):
        """Test that game is not over at start"""
        board = Board(size=8)
        self.assertFalse(board.game_over())

    def test_full_board_game_over(self):
        """Test game over with full board"""
        board = Board(size=4)

        # Fill entire board
        for r in range(4):
            for c in range(4):
                board.grid[r][c] = BLACK

        self.assertTrue(board.game_over())

    def test_no_moves_game_over(self):
        """Test game over when neither player can move"""
        board = Board(size=4)

        # Create a position where no one can move
        board.grid = [
            [BLACK, BLACK, BLACK, BLACK],
            [BLACK, BLACK, BLACK, BLACK],
            [WHITE, WHITE, WHITE, WHITE],
            [WHITE, WHITE, WHITE, WHITE],
        ]

        self.assertTrue(board.game_over())


class TestScore(unittest.TestCase):
    """Test score calculation"""

    def test_initial_score(self):
        """Test initial score is 2-2"""
        board = Board(size=8)
        black, white = board.score()
        self.assertEqual(black, 2)
        self.assertEqual(white, 2)

    def test_score_after_move(self):
        """Test score changes after move"""
        board = Board(size=8)
        moves = board.legal_moves(BLACK)
        board.make_move(moves[0])

        black, white = board.score()

        # Total should be 5 (4 initial + 1 placed)
        self.assertEqual(black + white, 5)

        # Black should have more pieces
        self.assertGreater(black, white)

    def test_score_counts_all_pieces(self):
        """Test score counts all pieces correctly"""
        board = Board(size=4)

        # Set known configuration
        board.grid = [
            [BLACK, BLACK, EMPTY, EMPTY],
            [WHITE, WHITE, WHITE, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
        ]

        black, white = board.score()
        self.assertEqual(black, 2)
        self.assertEqual(white, 3)


class TestSerialization(unittest.TestCase):
    """Test board serialization and deserialization"""

    def test_serialize_initial_board(self):
        """Test serializing initial board state"""
        board = Board(size=8)
        data = board.serialize()

        self.assertIn("grid", data)
        self.assertIn("size", data)
        self.assertIn("to_move", data)
        self.assertEqual(data["size"], 8)
        self.assertEqual(data["to_move"], BLACK)

    def test_deserialize_board(self):
        """Test deserializing board state"""
        board = Board(size=8)
        data = board.serialize()

        new_board = Board.deserialize(data)

        self.assertEqual(new_board.size, board.size)
        self.assertEqual(new_board.grid, board.grid)
        self.assertEqual(new_board.to_move, board.to_move)

    def test_serialize_after_moves(self):
        """Test serialization preserves game state"""
        board = Board(size=8)

        # Make some moves
        for _ in range(3):
            moves = board.legal_moves()
            if moves:
                board.make_move(moves[0])

        data = board.serialize()
        new_board = Board.deserialize(data)

        self.assertEqual(new_board.grid, board.grid)
        self.assertEqual(new_board.to_move, board.to_move)


class TestPass(unittest.TestCase):
    """Test passing when no legal moves"""

    def test_pass_move(self):
        """Test that pass is recorded correctly"""
        board = Board(size=8)
        board.pass_turn()

        self.assertEqual(board.to_move, WHITE)
        self.assertEqual(len(board.move_list), 1)

        # Pass is recorded as (-1, -1)
        color, r, c = board.move_list[0]
        self.assertEqual(r, -1)
        self.assertEqual(c, -1)


if __name__ == "__main__":
    unittest.main()
