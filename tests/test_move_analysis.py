#!/usr/bin/env python3
"""
Simple test to verify move analysis toggle functionality
"""
import pytest

import tests._helpers  # noqa: F401  # pylint: disable=unused-import

from src.Reversi import Game, Board, Settings


def test_move_analysis_toggle():
    """Test that move analysis toggle works and persists across new games"""
    pg = pytest.importorskip("pygame")
    print("Testing move analysis toggle functionality...")

    # Create a game instance
    board = Board()
    settings = Settings()
    game = Game(board, settings)

    # Initial window should be inactive
    assert not game.move_analysis.active, "Move analysis window should start closed"
    print("✓ Initial state is inactive")

    # Toggling with no moves should keep it inactive and update status
    game.on_toggle_move_analysis()
    assert not game.move_analysis.active, "No moves yet, window should remain closed"
    assert (
        game.ui.status == "No moves to analyze yet - make a move first"
    ), "Status should prompt for a move"
    print("✓ No-move toggle handled correctly")

    # Play a legal move to generate analysis data
    first_move = game.board.legal_moves()[0]
    played = game.play(first_move.row, first_move.col)
    assert played, "Expected the move to be applied successfully"
    assert (
        game.ui.last_move_analysis is not None
    ), "Move analysis data should be recorded after a move"

    # Toggle should now open the move analysis window
    game.on_toggle_move_analysis()
    assert game.move_analysis.active, "Move analysis window should open after toggle"
    assert (
        "Move analysis window opened" in game.ui.status
    ), "Status should confirm the window opened"
    print("✓ Toggle opens window with analysis")

    # Toggling again should close the window
    game.on_toggle_move_analysis()
    assert not game.move_analysis.active, "Second toggle should close the window"
    assert (
        game.ui.status == "Move analysis window closed"
    ), "Status should confirm the window closed"
    print("✓ Toggle closes window")

    # Verify window persists across a new game when left open
    game.on_toggle_move_analysis()  # Re-open window
    assert game.move_analysis.active
    game.on_new()
    assert game.move_analysis.active, "Move analysis window should persist across games"
    assert game.ui.status == "New game"
    print("✓ Window persists across new game")

    # Clean up: close window and quit pygame
    if game.move_analysis.active:
        game.on_toggle_move_analysis()

    pg.display.quit()
    if pg.mixer.get_init():
        pg.mixer.quit()

    print(
        "\n🎉 All tests passed! "
        "Move analysis toggle functionality is working correctly."
    )


if __name__ == "__main__":
    test_move_analysis_toggle()
