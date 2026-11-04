"""Generate deterministic, credential-free HTML fixtures for browser accessibility QA."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Backtesting.reproducible_backtest import DEFAULT_CONFIG, build_report, write_outputs
from Journal.analyze_journal import SAMPLE_ROW, build_html_report, summarize
from Operations.health import CheckResult, write_report


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    write_outputs(build_report(DEFAULT_CONFIG), output)
    trades = [
        dict(SAMPLE_ROW, symbol="SAMPLE", notes="Synthetic winning trade, no account data."),
        dict(SAMPLE_ROW, symbol="DEMO", pnl="-10.00", notes="Synthetic losing trade."),
    ]
    (output / "journal-report.html").write_text(build_html_report(summarize(trades)), encoding="utf-8")
    results = [
        CheckResult("Synthetic freshness", "PASS", "Fixture is current", "fixture.json"),
        CheckResult("Synthetic warning", "WARN", "Review this example", "example only"),
        CheckResult("Synthetic failure", "FAIL", "Example failure", "No external request was made"),
        CheckResult("Synthetic unknown", "UNKNOWN", "Example missing evidence", "fixture/missing.json"),
    ]
    write_report(results, output, datetime(2026, 11, 4, 12, tzinfo=timezone.utc))
    print(f"Generated three synthetic HTML reports in {output.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / ".reports")
    generate(parser.parse_args().output)
