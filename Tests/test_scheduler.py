from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALPACA_DIR = ROOT / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

import paper_trade


def test_scheduler_entrypoint_defaults_to_bot(monkeypatch):
    captured = []
    monkeypatch.setattr(sys, "argv", ["paper_trade.py"])
    monkeypatch.setattr(paper_trade.alpaca_paper, "main", lambda: captured.append(list(sys.argv)))

    paper_trade.main()

    assert captured == [["paper_trade.py", "bot"]]
