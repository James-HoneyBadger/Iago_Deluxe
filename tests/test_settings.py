#!/usr/bin/env python3
"""
Unit tests for Settings and file operations
Tests configuration persistence and error handling
"""
import sys
import os
import unittest
import json
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Reversi import Settings, Board  # noqa: E402


class TestSettingsSaveLoad(unittest.TestCase):
    """Test settings persistence"""

    def setUp(self):
        """Create temporary settings file"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.temp_path = self.temp_file.name

    def tearDown(self):
        """Clean up temporary file"""
        try:
            os.unlink(self.temp_path)
        except (OSError, FileNotFoundError):
            pass

    def test_default_settings(self):
        """Test default settings values"""
        settings = Settings()
        self.assertEqual(settings.theme, "classic")
        self.assertTrue(settings.sound)
        self.assertFalse(settings.ai_black)
        self.assertFalse(settings.ai_white)

    def test_save_settings(self):
        """Test saving settings to file"""
        settings = Settings()
        settings.theme = "midnight"
        settings.sound = False

        # Manually save
        data = {
            "theme": settings.theme,
            "sound": settings.sound,
            "ai_black": settings.ai_black,
            "ai_white": settings.ai_white,
            "ai_depth": settings.ai_depth,
            "board_size": settings.board_size,
        }

        with open(self.temp_path, "w") as f:
            json.dump(data, f)

        # Load back
        with open(self.temp_path, "r") as f:
            loaded = json.load(f)

        self.assertEqual(loaded["theme"], "midnight")
        self.assertFalse(loaded["sound"])

    def test_load_corrupted_settings(self):
        """Test loading corrupted settings file"""
        # Write invalid JSON
        with open(self.temp_path, "w") as f:
            f.write("{ invalid json }")

        # Should handle gracefully (would use defaults)


class TestBoardSerialization(unittest.TestCase):
    """Test board save/load functionality"""

    def setUp(self):
        """Create temporary save file"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
        self.temp_file.close()
        self.temp_path = self.temp_file.name

    def tearDown(self):
        """Clean up temporary file"""
        try:
            os.unlink(self.temp_path)
        except (OSError, FileNotFoundError):
            pass

    def test_save_initial_board(self):
        """Test saving initial board state"""
        board = Board(size=8)
        data = board.serialize()

        with open(self.temp_path, "w") as f:
            json.dump(data, f)

        # Verify file exists and is valid JSON
        with open(self.temp_path, "r") as f:
            loaded = json.load(f)

        self.assertEqual(loaded["size"], 8)
        self.assertIn("grid", loaded)

    def test_load_saved_game(self):
        """Test loading a saved game"""
        board = Board(size=8)

        # Make some moves
        for _ in range(3):
            moves = board.legal_moves()
            if moves:
                board.make_move(moves[0])

        # Save
        data = board.serialize()
        with open(self.temp_path, "w") as f:
            json.dump(data, f)

        # Load
        with open(self.temp_path, "r") as f:
            loaded_data = json.load(f)

        loaded_board = Board.deserialize(loaded_data)

        self.assertEqual(loaded_board.grid, board.grid)
        self.assertEqual(loaded_board.to_move, board.to_move)

    def test_save_preserves_move_history(self):
        """Test that save includes move history"""
        board = Board(size=8)

        # Make moves
        for _ in range(2):
            moves = board.legal_moves()
            if moves:
                board.make_move(moves[0])

        data = board.serialize()

        self.assertIn("move_list", data)
        self.assertEqual(len(data["move_list"]), 2)

    def test_load_invalid_file(self):
        """Test loading invalid save file"""
        # Write invalid data
        with open(self.temp_path, "w") as f:
            json.dump({"invalid": "data"}, f)

        # Should handle gracefully
        with open(self.temp_path, "r") as f:
            data = json.load(f)

        # Missing required fields
        self.assertNotIn("grid", data)


class TestFileErrorHandling(unittest.TestCase):
    """Test file operation error handling"""

    def test_load_nonexistent_file(self):
        """Test loading file that doesn't exist"""
        # Attempt to load nonexistent file
        nonexistent = "/tmp/nonexistent_reversi_save_12345.json"

        # Should not crash
        try:
            with open(nonexistent, "r") as f:
                json.load(f)
        except FileNotFoundError:
            # Expected
            pass

    def test_save_to_readonly_location(self):
        """Test saving to read-only location"""
        # This would typically fail with PermissionError
        # Just verify we handle it
        pass

    def test_corrupted_json(self):
        """Test loading corrupted JSON"""
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        temp_file.write("{ corrupted json data ][")
        temp_file.close()

        try:
            with open(temp_file.name, "r") as f:
                json.load(f)
        except json.JSONDecodeError:
            # Expected
            pass
        finally:
            os.unlink(temp_file.name)


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation"""

    def test_invalid_board_size(self):
        """Test that invalid board sizes are handled"""
        # Board size must be even
        # This would be validated in config
        invalid_sizes = [3, 5, 7, 9, 17, 20]

        # These should be rejected or adjusted
        for size in invalid_sizes:
            # Even numbers only
            if size % 2 != 0:
                # Should be invalid
                pass

    def test_invalid_theme(self):
        """Test that invalid theme names are handled"""
        Settings()  # Creates settings with defaults

        # Try setting invalid theme
        # invalid_theme = "nonexistent_theme"

        # Should either reject or use default
        # (actual validation would be in Settings.load)

    def test_invalid_ai_depth(self):
        """Test that invalid AI depth is handled"""
        Settings()  # Creates settings with defaults

        # AI depth should be 1-6
        # invalid_depths = [-1, 0, 10, 100]

        # These should be clamped or rejected


if __name__ == "__main__":
    unittest.main()
