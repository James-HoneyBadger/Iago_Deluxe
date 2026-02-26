#!/usr/bin/env python3
"""
Iago Deluxe - Main launcher
"""

import sys
import os
import warnings

# Suppress DeprecationWarning from pkg_resources, which pygame's internal font
# loader (pygame/pkgdata.py) triggers on Python 3.12+ via setuptools >=67.
# Tracked upstream: https://github.com/pygame/pygame/issues/3260
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r".*pkg_resources.*",
)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from game import Game  # noqa: E402


def main():
    """Main function"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
