"""
Filename: analyze_journal.py
Purpose: Summarize the trade journal CSV and generate an HTML performance report.
Author: TODO
"""

from __future__ import annotations

import csv
from collections import defaultdict
from html import escape
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
JOURNAL_DIR = ROOT_DIR / "Journal"
TRADES_PATH = JOURNAL_DIR / "trades.csv"
REPORT_PATH = JOURNAL_DIR / "report.html"
EXPECTED_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]
SAMPLE_ROW = {
    "date": "2026-01-02",
    "symbol": "AAPL",
    "side": "BUY",
    "qty": "10",
    "entry_price": "200.00",
    "exit_price": "202.50",
    "pnl": "25.00",
    "notes": "Sample paper trade",
}


def ensure_trade_csv() -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    if TRADES_PATH.exists():
        return

    with TRADES_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerow(SAMPLE_ROW)


def read_trades() -> list[dict[str, str]]:
    ensure_trade_csv()
    with TRADES_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = [column for column in EXPECTED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing expected trade journal columns: {', '.join(missing)}")
        return list(reader)


def to_float(value: str) -> float:
    return float((value or "0").strip())


def summarize(trades: list[dict[str, str]]) -> dict[str, object]:
    pnl_values = [to_float(trade["pnl"]) for trade in trades]
    total_trades = len(trades)
    total_pnl = sum(pnl_values)
    wins = [value for value in pnl_values if value > 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades else 0.0
    average_pnl = total_pnl / total_trades if total_trades else 0.0
    largest_win = max(pnl_values) if pnl_values else 0.0
    largest_loss = min(pnl_values) if pnl_values else 0.0

    symbol_totals: dict[str, float] = defaultdict(float)
    for trade in trades:
        symbol_totals[trade["symbol"].strip().upper()] += to_float(trade["pnl"])

    best_symbol = max(symbol_totals.items(), key=lambda item: item[1]) if symbol_totals else ("N/A", 0.0)
    worst_symbol = min(symbol_totals.items(), key=lambda item: item[1]) if symbol_totals else ("N/A", 0.0)

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "average_pnl": average_pnl,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "best_symbol": best_symbol,
        "worst_symbol": worst_symbol,
        "trades": trades,
    }


def build_html_report(summary: dict[str, object]) -> str:
    trades = summary["trades"]
    rows = []
    for trade in trades:
        rows.append(
            "<tr>"
            f"<td>{escape(trade['date'])}</td>"
            f"<td>{escape(trade['symbol'])}</td>"
            f"<td>{escape(trade['side'])}</td>"
            f"<td>{escape(trade['qty'])}</td>"
            f"<td>{escape(trade['entry_price'])}</td>"
            f"<td>{escape(trade['exit_price'])}</td>"
            f"<td>{escape(trade['pnl'])}</td>"
            f"<td>{escape(trade['notes'])}</td>"
            "</tr>"
        )

    best_symbol_name, best_symbol_value = summary["best_symbol"]
    worst_symbol_name, worst_symbol_value = summary["worst_symbol"]

    return f"""<!-- Filename: report.html | Purpose: Generated trading journal summary report. | Author: TODO -->
  <!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Trading Journal Report</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 2rem; background: #f5f7fa; color: #1f2933; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
    .card {{ background: white; border-radius: 10px; padding: 1rem; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08); }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #d2d6dc; padding: 0.75rem; text-align: left; }}
    th {{ background: #e5eef7; }}
  </style>
</head>
<body>
  <h1>Trading Journal Summary</h1>
  <p>Source file: {escape(str(TRADES_PATH.name))}</p>
  <div class=\"grid\">
    <div class=\"card\"><strong>Total Trades</strong><br>{summary['total_trades']}</div>
    <div class=\"card\"><strong>Win Rate</strong><br>{summary['win_rate']:.2f}%</div>
    <div class=\"card\"><strong>Total P&amp;L</strong><br>{summary['total_pnl']:.2f}</div>
    <div class=\"card\"><strong>Average P&amp;L</strong><br>{summary['average_pnl']:.2f}</div>
    <div class=\"card\"><strong>Largest Win</strong><br>{summary['largest_win']:.2f}</div>
    <div class=\"card\"><strong>Largest Loss</strong><br>{summary['largest_loss']:.2f}</div>
    <div class=\"card\"><strong>Best Symbol</strong><br>{escape(best_symbol_name)} ({best_symbol_value:.2f})</div>
    <div class=\"card\"><strong>Worst Symbol</strong><br>{escape(worst_symbol_name)} ({worst_symbol_value:.2f})</div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Symbol</th>
        <th>Side</th>
        <th>Qty</th>
        <th>Entry Price</th>
        <th>Exit Price</th>
        <th>P&amp;L</th>
        <th>Notes</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""


def print_summary(summary: dict[str, object]) -> None:
    best_symbol_name, best_symbol_value = summary["best_symbol"]
    worst_symbol_name, worst_symbol_value = summary["worst_symbol"]
    print(f"Total trades: {summary['total_trades']}")
    print(f"Win rate: {summary['win_rate']:.2f}%")
    print(f"Total P&L: {summary['total_pnl']:.2f}")
    print(f"Average P&L per trade: {summary['average_pnl']:.2f}")
    print(f"Largest win: {summary['largest_win']:.2f}")
    print(f"Largest loss: {summary['largest_loss']:.2f}")
    print(f"Best symbol: {best_symbol_name} ({best_symbol_value:.2f})")
    print(f"Worst symbol: {worst_symbol_name} ({worst_symbol_value:.2f})")


def main() -> None:
    trades = read_trades()
    summary = summarize(trades)
    print_summary(summary)
    REPORT_PATH.write_text(build_html_report(summary), encoding="utf-8")
    print(f"HTML report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()