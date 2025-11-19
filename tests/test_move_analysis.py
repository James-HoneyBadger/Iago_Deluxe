#!/usr/bin/env python3
"""
Simple test to verify move analysis toggle functionality
"""
import sys
import os

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_move_analysis_toggle():
    """Test that move analysis toggle works and persists across new games"""
    print("Testing move analysis toggle functionality...")

    # Import classes locally to avoid module execution
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "reversi", "/home/james/Reversi/Reversi.py"
    )
    reversi_module = importlib.util.module_from_spec(spec)

    # Mock the main execution to prevent GUI from starting
    reversi_module.__name__ = "not_main"
    spec.loader.exec_module(reversi_module)

    Game = reversi_module.Game
    Board = reversi_module.Board
    Settings = reversi_module.Settings

    # Create a game instance
    board = Board()
    settings = Settings()
    game = Game(board, settings)

    # Initial state should be False
    assert not game.ui.show_move_analysis, "Initial state should be False"
    print("✓ Initial state is False")

    # Toggle it on
    game.on_toggle_move_analysis()
    assert game.ui.show_move_analysis, "Should be True after toggle"
    print("✓ Toggle works - now True")

    # Toggle it off
    game.on_toggle_move_analysis()
    assert not game.ui.show_move_analysis, "Should be False after second toggle"
    print("✓ Toggle works - now False")

    # Toggle it on again
    game.on_toggle_move_analysis()
    assert game.ui.show_move_analysis, "Should be True after third toggle"
    print("✓ Toggle works - now True again")

    # Start a new game - this should preserve the setting
    game.on_new()
    assert game.ui.show_move_analysis, "Should still be True after new game"
    print("✓ Setting preserved across new game")

    # Test with False state
    game.on_toggle_move_analysis()  # Turn off
    assert not game.ui.show_move_analysis, "Should be False"
    game.on_new()  # New game
    assert not game.ui.show_move_analysis, "Should still be False after new game"
    print("✓ False state also preserved across new game")

    print(
        "\n🎉 All tests passed! "
        "Move analysis toggle functionality is working correctly."
    )


if __name__ == "__main__":
    test_move_analysis_toggle()
