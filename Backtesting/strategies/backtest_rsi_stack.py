"""
Filename: backtest_rsi_stack.py
Purpose: Backtest multi timeframe RSI stack strategy with Alpaca historical bars.
Author: TODO
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from rsi_stack import RSIStack

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
    hold_bars: int
    entry_score: int
    exit_score: int


def timeframe_from_label(label: str) -> TimeFrame:
    mapping = {
        "1Min": TimeFrame(1, TimeFrameUnit.Minute),
        "5Min": TimeFrame(5, TimeFrameUnit.Minute),
        "15Min": TimeFrame(15, TimeFrameUnit.Minute),
        "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
        "1Day": TimeFrame(1, TimeFrameUnit.Day),
    }
    if label not in mapping:
        raise ValueError(f"Unsupported timeframe label: {label}")
    return mapping[label]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest RSI stack strategy with Alpaca bars.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--fast-tf", default="1Hour")
    parser.add_argument("--slow-tf", default="1Day")
    parser.add_argument("--oversold", type=float, default=35)
    parser.add_argument("--overbought", type=float, default=65)
    return parser.parse_args()


def ensure_journal_file() -> None:
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL_PATH.exists():
        return
    with JOURNAL_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writeheader()


def get_api_client() -> StockHistoricalDataClient:
    load_dotenv(ROOT_DIR / ".env")
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise RuntimeError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")
    return StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)


def fetch_bars(
    client: StockHistoricalDataClient,
    symbol: str,
    timeframe_label: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe_from_label(timeframe_label),
        start=pd.Timestamp(start_date, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC"),
    )
    response = client.get_stock_bars(request)
    bars = response.df
    if bars.empty:
        raise RuntimeError(f"No bars returned for timeframe {timeframe_label}")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    return bars


def run_backtest(data: pd.DataFrame, symbol: str) -> list[CompletedTrade]:
    trades: list[CompletedTrade] = []
    current_entry: tuple[int, pd.Timestamp, float, int] | None = None

    for index, row in data.iterrows():
        signal = str(row["signal"])
        if signal == "BUY" and current_entry is None:
            current_entry = (index, row["timestamp"], float(row["close"]), int(row["rsi_stack_score"]))
        elif signal == "SELL" and current_entry is not None:
            entry_index, entry_time, entry_price, entry_score = current_entry
            exit_time = row["timestamp"]
            exit_price = float(row["close"])
            exit_score = int(row["rsi_stack_score"])
            pnl_dollars = exit_price - entry_price
            pnl_percent = (pnl_dollars / entry_price * 100) if entry_price else 0.0
            hold_bars = index - entry_index
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
                    hold_bars=hold_bars,
                    entry_score=entry_score,
                    exit_score=exit_score,
                )
            )
            current_entry = None

    return trades


def compute_max_drawdown(trades: list[CompletedTrade]) -> float:
    running = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        running += trade.pnl_dollars
        peak = max(peak, running)
        max_drawdown = max(max_drawdown, peak - running)
    return max_drawdown


def append_trades_to_journal(trades: list[CompletedTrade], fast_tf: str, slow_tf: str) -> None:
    ensure_journal_file()
    note = f"backtest_rsi_stack_{fast_tf}_{slow_tf}"
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
                    "notes": note,
                }
            )


def print_summary(symbol: str, data: pd.DataFrame, trades: list[CompletedTrade], blocked_buy: int, runtime_seconds: float, timeframes: list[str]) -> None:
    total_trades = len(trades)
    wins = sum(1 for trade in trades if trade.pnl_dollars > 0)
    losses = sum(1 for trade in trades if trade.pnl_dollars <= 0)
    total_pnl = sum(trade.pnl_dollars for trade in trades)
    average_pnl = total_pnl / total_trades if total_trades else 0.0
    win_rate = (wins / total_trades * 100) if total_trades else 0.0
    largest_win = max((trade.pnl_dollars for trade in trades), default=0.0)
    largest_loss = min((trade.pnl_dollars for trade in trades), default=0.0)
    max_drawdown = compute_max_drawdown(trades)

    print("\nRSI Stack Backtest Summary")
    print("=" * 80)
    print(f"Symbol:                       {symbol}")
    print(f"Total completed trades:       {total_trades}")
    print(f"Win rate:                     {win_rate:.2f}%")
    print(f"Total P&L:                    ${total_pnl:.2f}")
    print(f"Average P&L per trade:        ${average_pnl:.2f}")
    print(f"Largest win:                  ${largest_win:.2f}")
    print(f"Largest loss:                 ${largest_loss:.2f}")
    print(f"Max drawdown:                 ${max_drawdown:.2f}")
    print(f"Blocked BUY (slow not confirm): {blocked_buy}")
    print("=" * 80)

    print("\nSignal Bars")
    print("-" * 140)
    headers = ["Date", "Close", *[f"rsi_{tf}" for tf in timeframes], "Stack", "Signal"]
    print(" ".join(f"{header:>16}" for header in headers))
    print("-" * 140)
    signal_rows = data[data["signal"] != "HOLD"]
    for _, row in signal_rows.iterrows():
        fields = [
            f"{row['timestamp'].isoformat():>16}",
            f"{row['close']:>16.2f}",
            *[f"{row[f'rsi_{tf}']:>16.2f}" for tf in timeframes],
            f"{int(row['rsi_stack_score']):>16}",
            f"{row['signal']:>16}",
        ]
        print(" ".join(fields))
    print("-" * 140)
    print(f"Runtime: {runtime_seconds:.2f} seconds")


def main() -> int:
    started = time.perf_counter()
    args = parse_args()
    if args.fast_tf == args.slow_tf:
        print("--fast-tf and --slow-tf must be different timeframes")
        return 1

    symbol = args.symbol.upper()
    timeframes = [args.fast_tf, args.slow_tf]
    rsi_periods = {args.fast_tf: 14, args.slow_tf: 14}

    try:
        client = get_api_client()
        bars_by_tf: dict[str, pd.DataFrame] = {}
        for tf in timeframes:
            bars = fetch_bars(client, symbol, tf, args.start, args.end)
            if len(bars) < 50:
                print(f"Warning: fewer than 50 bars returned for timeframe {tf}")
            bars_by_tf[tf] = bars

        strategy = RSIStack(
            timeframes=timeframes,
            rsi_periods=rsi_periods,
            oversold=args.oversold,
            overbought=args.overbought,
            symbol=symbol,
        )
        aligned = strategy.align_timeframes(bars_by_tf)
        signaled = strategy.calculate_signals(aligned)
        trades = run_backtest(signaled, symbol)
        blocked_buy = int(signaled["blocked_buy_unconfirmed"].sum())
        append_trades_to_journal(trades, args.fast_tf, args.slow_tf)
        runtime = time.perf_counter() - started
        print_summary(symbol, signaled, trades, blocked_buy, runtime, timeframes)
        return 0
    except Exception as exc:
        runtime = time.perf_counter() - started
        print(f"Backtest failed: {exc}")
        print(f"Runtime before failure: {runtime:.2f} seconds")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
