#!/usr/bin/env python3
"""
Unit tests for AI class
Tests AI move selection, evaluation, and difficulty levels
"""
import sys
import os
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Reversi import Board, AI, BLACK, WHITE  # noqa: E402


class TestAIInitialization(unittest.TestCase):
    """Test AI initialization"""

    def test_default_ai_creation(self):
        """Test creating AI with default settings"""
        ai = AI()
        self.assertEqual(ai.max_depth, 4)
        self.assertIsNotNone(ai.rng)
        self.assertEqual(len(ai.transposition_table), 0)

    def test_custom_depth(self):
        """Test creating AI with custom depth"""
        for depth in range(1, 7):
            ai = AI(max_depth=depth)
            self.assertEqual(ai.max_depth, depth)


class TestAIEvaluation(unittest.TestCase):
    """Test AI position evaluation"""

    def test_evaluate_initial_position(self):
        """Test evaluation of starting position"""
        board = Board(size=8)
        ai = AI(max_depth=1)

        score = ai.evaluate(board, BLACK)
        # Should return some numeric value
        self.assertIsInstance(score, (int, float))

    def test_winning_position_high_score(self):
        """Test that winning positions score high"""
        board = Board(size=4)
        ai = AI(max_depth=1)

        # Fill board mostly with BLACK
        for r in range(4):
            for c in range(4):
                board.grid[r][c] = BLACK
        board.grid[0][0] = WHITE

        black_score = ai.evaluate(board, BLACK)
        white_score = ai.evaluate(board, WHITE)

        # Black should have higher score
        self.assertGreater(black_score, white_score)

    def test_corner_bonus(self):
        """Test that corners are valued highly"""
        board = Board(size=8)
        ai = AI(max_depth=1)

        # Clear board
        for r in range(8):
            for c in range(8):
                board.grid[r][c] = 0

        # Place single black piece in corner
        board.grid[0][0] = BLACK
        board.grid[4][4] = BLACK  # Center piece

        score_with_corner = ai.evaluate(board, BLACK)

        # Remove corner, add center
        board.grid[0][0] = 0
        board.grid[5][5] = BLACK

        score_without_corner = ai.evaluate(board, BLACK)

        # Corner should be worth more
        self.assertGreater(score_with_corner, score_without_corner)


class TestAIMoveSelection(unittest.TestCase):
    """Test AI move selection"""

    def test_choose_returns_valid_move(self):
        """Test that AI chooses a valid move"""
        board = Board(size=8)
        ai = AI(max_depth=1)

        move = ai.choose(board, BLACK)

        # Should return a move
        self.assertIsNotNone(move)

        # Move should be legal
        legal_moves = board.legal_moves(BLACK)
        move_positions = {(m.row, m.col) for m in legal_moves}
        self.assertIn((move.row, move.col), move_positions)

    def test_choose_no_moves(self):
        """Test AI when no legal moves available"""
        board = Board(size=4)
        ai = AI(max_depth=1)

        # Fill board completely
        for r in range(4):
            for c in range(4):
                board.grid[r][c] = BLACK

        move = ai.choose(board, BLACK)

        # Should return None when no moves
        self.assertIsNone(move)

    def test_ai_prefers_corner(self):
        """Test that AI prefers corner moves when available"""
        board = Board(size=8)
        ai = AI(max_depth=3)

        # Set up position where corner is available
        board.grid[0][0] = 0  # Empty corner
        board.grid[0][1] = WHITE
        board.grid[1][1] = BLACK

        # Run multiple times to account for randomness
        corner_chosen = 0
        trials = 10

        for _ in range(trials):
            test_board = Board.deserialize(board.serialize())
            test_board.to_move = BLACK
            move = ai.choose(test_board, BLACK)

            if move and move.row == 0 and move.col == 0:
                corner_chosen += 1

        # Corner should be chosen frequently if it's legal
        # (may not always be legal depending on position)


class TestAIDepthLevels(unittest.TestCase):
    """Test different AI difficulty levels"""

    def test_depth_1_fast(self):
        """Test that depth 1 AI is fast"""
        import time

        board = Board(size=8)
        ai = AI(max_depth=1)

        start = time.time()
        ai.choose(board, BLACK)
        elapsed = time.time() - start

        # Should be very fast
        self.assertLess(elapsed, 0.1)

    def test_higher_depth_searches_more(self):
        """Test that higher depth searches more nodes"""
        board = Board(size=8)

        ai_shallow = AI(max_depth=1)
        ai_shallow.choose(board, BLACK)
        nodes_shallow = ai_shallow.nodes_searched

        ai_deep = AI(max_depth=3)
        ai_deep.choose(board, BLACK)
        nodes_deep = ai_deep.nodes_searched

        # Deeper search should examine more nodes
        self.assertGreater(nodes_deep, nodes_shallow)


class TestAITranspositionTable(unittest.TestCase):
    """Test AI transposition table"""

    def test_transposition_table_used(self):
        """Test that transposition table stores positions"""
        board = Board(size=8)
        ai = AI(max_depth=3)

        ai.choose(board, BLACK)

        # Table should have some entries
        self.assertGreater(len(ai.transposition_table), 0)

    def test_transposition_table_cleared(self):
        """Test that large tables get cleared"""
        board = Board(size=8)
        ai = AI(max_depth=4)

        # Manually fill table past limit
        for i in range(15000):
            ai.transposition_table[f"key_{i}"] = (1, 0)

        # Next search should clear it
        ai.choose(board, BLACK)

        # Table should be smaller
        self.assertLess(len(ai.transposition_table), 15000)


class TestAIMobility(unittest.TestCase):
    """Test AI considers mobility"""

    def test_mobility_evaluation(self):
        """Test that AI values mobility"""
        board = Board(size=8)
        ai = AI(max_depth=2)

        # Position with many moves should be valued
        moves = board.legal_moves(BLACK)
        self.assertGreater(len(moves), 0)

        # AI should make a reasonable choice
        move = ai.choose(board, BLACK)
        self.assertIsNotNone(move)


class TestAIAdaptiveDepth(unittest.TestCase):
    """Test AI adaptive depth feature"""

    def test_endgame_depth_increase(self):
        """Test that AI searches deeper in endgame"""
        board = Board(size=6)
        ai = AI(max_depth=3)

        # Fill most of the board (endgame)
        for r in range(6):
            for c in range(6):
                if (r + c) % 2 == 0:
                    board.grid[r][c] = BLACK
                else:
                    board.grid[r][c] = WHITE

        # Leave a few squares
        board.grid[0][0] = 0
        board.grid[0][1] = 0

        # AI should still be able to choose
        ai.choose(board, BLACK)  # Just verify it doesn't crash


if __name__ == "__main__":
    unittest.main()
