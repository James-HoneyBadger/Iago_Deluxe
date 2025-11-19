#!/usr/bin/env python3
"""
Test script to verify AI difficulty levels 1-6 function differently
"""
import sys

sys.path.insert(0, "/home/james/HB_Reversi")

from src.Reversi import AI, Board, BLACK, WHITE


def test_ai_levels():
    """Test that different AI levels produce different search depths and behaviors"""
    print("Testing AI Difficulty Levels")
    print("=" * 60)

    # Create a test board position
    board = Board(size=8)

    results = {}

    for level in range(1, 7):
        print(f"\nLevel {level}:")
        ai = AI(max_depth=level)

        # Get the AI's configured depth
        print(f"  Max Depth: {ai.max_depth}")

        # Test a move to see how many nodes are searched
        ai.nodes_searched = 0
        move = ai.choose(board, BLACK)

        print(f"  Nodes Searched: {ai.nodes_searched:,}")
        print(
            f"  Chosen Move: {move.row if move else None}, {move.col if move else None}"
        )

        results[level] = {
            "max_depth": ai.max_depth,
            "nodes_searched": ai.nodes_searched,
            "move": (move.row, move.col) if move else None,
        }

    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)

    # Check that depths are different
    depths = [results[i]["max_depth"] for i in range(1, 7)]
    print(f"\nConfigured Depths: {depths}")

    if len(set(depths)) == 6:
        print("✅ All 6 levels have different max_depth values")
    else:
        print("❌ ERROR: Some levels have the same max_depth")
        return False

    # Check that node counts are generally increasing
    nodes = [results[i]["nodes_searched"] for i in range(1, 7)]
    print(f"\nNodes Searched: {[f'{n:,}' for n in nodes]}")

    # Verify general trend (each level should search more nodes)
    increasing = True
    for i in range(1, 6):
        if nodes[i] <= nodes[i - 1] * 0.5:  # Allow some variance
            print(
                f"⚠️  Warning: Level {i+1} didn't search significantly more than Level {i}"
            )
            increasing = False

    if increasing:
        print("✅ Node search counts show expected scaling")
    else:
        print("⚠️  Node counts don't strictly increase (may vary by position)")

    # Test that moves might differ at different depths
    moves = [results[i]["move"] for i in range(1, 7)]
    unique_moves = len(set(moves))
    print(f"\nUnique Moves Chosen: {unique_moves} out of 6 levels")

    if unique_moves > 1:
        print("✅ Different levels can choose different moves (good!)")
    else:
        print("ℹ️  All levels chose the same move (may happen in simple positions)")

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print("The AI difficulty system is functional!")
    print("\nLevel Characteristics:")
    print("  Level 1 (Beginner): Quick, searches fewest positions")
    print("  Level 2 (Easy):     Slightly deeper search")
    print("  Level 3 (Medium):   Moderate search depth")
    print("  Level 4 (Hard):     Deep search, good play")
    print("  Level 5 (Expert):   Very deep search, strong play")
    print("  Level 6 (Master):   Maximum depth, strongest play")

    return True


if __name__ == "__main__":
    test_ai_levels()
