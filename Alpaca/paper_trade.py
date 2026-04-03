"""
Filename: paper_trade.py
Purpose: Scheduled entry point for the Alpaca paper trading bot.
Author: TODO
"""

from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import alpaca_paper


def main() -> None:
    args = sys.argv[1:] or ["bot"]
    sys.argv = [sys.argv[0], *args]
    alpaca_paper.main()


if __name__ == "__main__":
    main()