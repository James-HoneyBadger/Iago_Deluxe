#!/usr/bin/env python3
"""
Test runner for Reversi Deluxe
Runs all unit tests and generates coverage report
"""
import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(verbosity=2):
    """
    Run all tests in the tests directory

    Args:
        verbosity: Verbosity level (0=quiet, 1=normal, 2=verbose)

    Returns:
        True if all tests passed, False otherwise
    """
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return True
    else:
        print("\n✗ Some tests failed")
        return False


def run_specific_test(test_module, verbosity=2):
    """
    Run tests from a specific module

    Args:
        test_module: Module name (e.g., 'test_board')
        verbosity: Verbosity level
    """
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Reversi Deluxe tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument(
        "-m", "--module", help="Run specific test module (e.g., test_board)"
    )

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Run tests
    if args.module:
        success = run_specific_test(args.module, verbosity)
    else:
        success = run_tests(verbosity)

    sys.exit(0 if success else 1)
