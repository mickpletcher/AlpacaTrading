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


def test_scheduler_launchers_write_machine_readable_status():
    powershell = (ROOT / "Scheduler" / "run_strategy.ps1").read_text(encoding="utf-8")
    shell = (ROOT / "Scheduler" / "run_strategy.sh").read_text(encoding="utf-8")

    assert "scheduler_status.json" in powershell
    assert "Write-SchedulerStatus" in powershell
    assert "scheduler_status.json" in shell
    assert "write_scheduler_status" in shell
