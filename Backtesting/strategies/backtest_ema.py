"""
Filename: backtest_ema.py
Purpose: Fetch Alpaca historical bars and backtest the shared EMA crossover strategy.
Author: TODO
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from ema_crossover import EMAcrossover

ROOT_DIR = Path(__file__).resolve().parents[2]
JOURNAL_PATH = ROOT_DIR / "Journal" / "trades.csv"
EXPECTED_JOURNAL_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]


@dataclass
class CompletedTrade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    symbol: str
    qty: int
    entry_price: float
    exit_price: float
    pnl_dollars: float
    pnl_percent: float
    hold_days: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest EMA crossover strategy with Alpaca historical bars.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--fast", type=int, default=9)
    parser.add_argument("--slow", type=int, default=21)
    return parser.parse_args()


def ensure_journal_file() -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL_PATH.exists():
        return
    with JOURNAL_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writeheader()


def get_api_client() -> StockHistoricalDataClient:
    env_path = ROOT_DIR / ".env"
    load_dotenv(env_path)
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        print("ALPACA_API_KEY or ALPACA_SECRET_KEY was not set. Falling back to unauthenticated Alpaca data client.")
        return StockHistoricalDataClient()
    return StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)


def fetch_daily_bars(client: StockHistoricalDataClient, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=pd.Timestamp(start_date, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC"),
    )
    response = client.get_stock_bars(request)
    bars = response.df
    if bars.empty:
        raise RuntimeError("No historical bars were returned for the selected symbol/date range.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()
        bars["symbol"] = symbol

    bars = bars.rename(columns={"timestamp": "timestamp", "trade_count": "trade_count"})
    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    return bars.sort_values("timestamp").reset_index(drop=True)


def run_backtest(data: pd.DataFrame, symbol: str, fast: int, slow: int) -> tuple[pd.DataFrame, list[CompletedTrade]]:
    strategy = EMAcrossover(fast_period=fast, slow_period=slow, symbol=symbol)
    signaled = strategy.calculate_signals(data)

    trades: list[CompletedTrade] = []
    current_entry: tuple[pd.Timestamp, float] | None = None

    for _, row in signaled.iterrows():
        signal = str(row["signal"])
        if signal == "BUY" and current_entry is None:
            current_entry = (row["timestamp"], float(row["close"]))
        elif signal == "SELL" and current_entry is not None:
            entry_time, entry_price = current_entry
            exit_time = row["timestamp"]
            exit_price = float(row["close"])
            pnl_dollars = exit_price - entry_price
            pnl_percent = (pnl_dollars / entry_price) * 100 if entry_price else 0.0
            hold_days = max(0, int((exit_time - entry_time).days))
            trades.append(
                CompletedTrade(
                    entry_time=entry_time,
                    exit_time=exit_time,
                    symbol=symbol,
                    qty=1,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pnl_dollars=pnl_dollars,
                    pnl_percent=pnl_percent,
                    hold_days=hold_days,
                )
            )
            current_entry = None

    return signaled, trades


def compute_max_drawdown(trades: list[CompletedTrade]) -> float:
    running = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        running += trade.pnl_dollars
        peak = max(peak, running)
        max_drawdown = max(max_drawdown, peak - running)
    return max_drawdown


def print_summary(symbol: str, trades: list[CompletedTrade], runtime_seconds: float) -> None:
    total_trades = len(trades)
    winning = sum(1 for trade in trades if trade.pnl_dollars > 0)
    losing = sum(1 for trade in trades if trade.pnl_dollars <= 0)
    total_pnl = sum(trade.pnl_dollars for trade in trades)
    average_pnl = total_pnl / total_trades if total_trades else 0.0
    win_rate = (winning / total_trades * 100) if total_trades else 0.0
    max_drawdown = compute_max_drawdown(trades)

    print("\nEMA Crossover Backtest Summary")
    print("=" * 50)
    print(f"Symbol:                  {symbol}")
    print(f"Total trades:            {total_trades}")
    print(f"Winning trades:          {winning}")
    print(f"Losing trades:           {losing}")
    print(f"Win rate:                {win_rate:.2f}%")
    print(f"Total P&L:               ${total_pnl:.2f}")
    print(f"Average P&L per trade:   ${average_pnl:.2f}")
    print(f"Max drawdown:            ${max_drawdown:.2f}")
    print("=" * 50)

    if trades:
        print("\nCompleted Trades")
        print("-" * 110)
        print(f"{'Exit Date':<20} {'Entry':>10} {'Exit':>10} {'P&L $':>10} {'P&L %':>10} {'Hold Days':>10}")
        print("-" * 110)
        for trade in trades:
            print(
                f"{trade.exit_time.isoformat():<20} {trade.entry_price:>10.2f} {trade.exit_price:>10.2f} "
                f"{trade.pnl_dollars:>10.2f} {trade.pnl_percent:>10.2f} {trade.hold_days:>10}"
            )
        print("-" * 110)

    print(f"Runtime: {runtime_seconds:.2f} seconds")


def append_trades_to_journal(trades: list[CompletedTrade]) -> None:
    ensure_journal_file()
    with JOURNAL_PATH.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        for trade in trades:
            writer.writerow(
                {
                    "date": trade.exit_time.date().isoformat(),
                    "symbol": trade.symbol,
                    "side": "SELL",
                    "qty": trade.qty,
                    "entry_price": f"{trade.entry_price:.4f}",
                    "exit_price": f"{trade.exit_price:.4f}",
                    "pnl": f"{trade.pnl_dollars:.4f}",
                    "notes": "backtest_ema_crossover",
                }
            )


def main() -> int:
    started = time.perf_counter()
    args = parse_args()

    try:
        client = get_api_client()
        bars = fetch_daily_bars(client, args.symbol.upper(), args.start, args.end)
        _, trades = run_backtest(bars, args.symbol.upper(), args.fast, args.slow)
        append_trades_to_journal(trades)
        runtime = time.perf_counter() - started
        print_summary(args.symbol.upper(), trades, runtime)
        return 0
    except Exception as exc:
        runtime = time.perf_counter() - started
        print(f"Backtest failed: {exc}")
        print(f"Runtime before failure: {runtime:.2f} seconds")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
