"""
Filename: backtest_gap_momentum.py
Purpose: Backtest Gap Up Momentum strategy with Alpaca intraday and daily bars.
Author: TODO
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from gap_momentum import GapMomentum

ET_TZ = ZoneInfo("America/New_York")
ROOT_DIR = Path(__file__).resolve().parents[2]
JOURNAL_PATH = ROOT_DIR / "Journal" / "trades.csv"
EXPECTED_JOURNAL_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]


@dataclass
class TradeRecord:
    trade_date: date
    symbol: str
    gap_pct: float
    entry_time_et: pd.Timestamp
    exit_time_et: pd.Timestamp
    exit_reason: str
    entry_price: float
    exit_price: float
    pnl_dollars: float
    pnl_percent: float
    hold_minutes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest Gap Up Momentum strategy.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default=date.today().isoformat())
    parser.add_argument("--gap-threshold", type=float, default=0.02)
    parser.add_argument("--momentum-bars", type=int, default=3)
    parser.add_argument("--stop-loss", type=float, default=0.015)
    parser.add_argument("--take-profit", type=float, default=0.04)
    parser.add_argument("--volume-multiplier", type=float, default=1.5)
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


def fetch_intraday_bars(client: StockHistoricalDataClient, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=pd.Timestamp(start_date, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1),
    )
    bars = client.get_stock_bars(request).df
    if bars.empty:
        raise RuntimeError("No 1 minute bars returned for selected date range.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars["timestamp_et"] = bars["timestamp"].dt.tz_convert(ET_TZ)
    bars["trade_date_et"] = bars["timestamp_et"].dt.date
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    return bars


def fetch_daily_bars(client: StockHistoricalDataClient, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    preload_start = (pd.Timestamp(start_date) - pd.Timedelta(days=50)).date().isoformat()
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=pd.Timestamp(preload_start, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1),
    )
    bars = client.get_stock_bars(request).df
    if bars.empty:
        raise RuntimeError("No daily bars returned for selected date range.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars["timestamp_et"] = bars["timestamp"].dt.tz_convert(ET_TZ)
    bars["trade_date_et"] = bars["timestamp_et"].dt.date
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    return bars


def build_daily_context(daily_bars: pd.DataFrame) -> dict[date, dict[str, float]]:
    context: dict[date, dict[str, float]] = {}
    for idx in range(1, len(daily_bars)):
        current_date = daily_bars.at[idx, "trade_date_et"]
        prior_close = float(daily_bars.at[idx - 1, "close"])
        history = daily_bars.iloc[max(0, idx - 20) : idx]
        avg_daily_volume = float(history["volume"].mean()) if not history.empty else 0.0
        context[current_date] = {
            "prior_close": prior_close,
            "avg_daily_volume": avg_daily_volume,
            "history_len": float(len(history)),
        }
    return context


def extract_trade(day_df: pd.DataFrame, signal_df: pd.DataFrame, symbol: str) -> TradeRecord | None:
    buy_rows = signal_df[signal_df["signal"] == "BUY"]
    exit_rows = signal_df[signal_df["signal"].isin(["STOP_LOSS", "TAKE_PROFIT", "EOD_EXIT"])]
    if buy_rows.empty or exit_rows.empty:
        return None

    buy_row = buy_rows.iloc[0]
    exit_row = exit_rows.iloc[0]
    strategy = GapMomentum(symbol=symbol)
    entry_price = float(buy_row["close"])
    exit_price = strategy.get_exit_price(exit_row, str(exit_row["signal"]))
    pnl_dollars = exit_price - entry_price
    pnl_percent = (pnl_dollars / entry_price) * 100 if entry_price else 0.0
    hold_minutes = int((exit_row["timestamp"] - buy_row["timestamp"]).total_seconds() // 60)

    return TradeRecord(
        trade_date=buy_row["timestamp_et"].date(),
        symbol=symbol,
        gap_pct=float(signal_df["gap_pct"].iloc[0]),
        entry_time_et=buy_row["timestamp_et"],
        exit_time_et=exit_row["timestamp_et"],
        exit_reason=str(exit_row["signal"]).lower(),
        entry_price=entry_price,
        exit_price=exit_price,
        pnl_dollars=pnl_dollars,
        pnl_percent=pnl_percent,
        hold_minutes=hold_minutes,
    )


def append_trades_to_journal(trades: list[TradeRecord]) -> None:
    ensure_journal_file()
    with JOURNAL_PATH.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        for trade in trades:
            writer.writerow(
                {
                    "date": trade.trade_date.isoformat(),
                    "symbol": trade.symbol,
                    "side": "SELL",
                    "qty": 1,
                    "entry_price": f"{trade.entry_price:.4f}",
                    "exit_price": f"{trade.exit_price:.4f}",
                    "pnl": f"{trade.pnl_dollars:.4f}",
                    "notes": f"backtest_gap_momentum_{trade.exit_reason}",
                }
            )


def print_summary(
    total_days: int,
    days_with_gap: int,
    momentum_fail_days: int,
    volume_fail_days: int,
    valid_entry_days: int,
    trades: list[TradeRecord],
    runtime_seconds: float,
) -> None:
    total_pnl = sum(trade.pnl_dollars for trade in trades)
    avg_pnl = total_pnl / len(trades) if trades else 0.0
    avg_hold = sum(trade.hold_minutes for trade in trades) / len(trades) if trades else 0.0

    take_profit_count = sum(1 for trade in trades if trade.exit_reason == "take_profit")
    stop_loss_count = sum(1 for trade in trades if trade.exit_reason == "stop_loss")
    denominator = take_profit_count + stop_loss_count
    win_rate = (take_profit_count / denominator * 100) if denominator else 0.0

    exit_counter = Counter(trade.exit_reason for trade in trades)
    common_exit = exit_counter.most_common(1)[0][0] if exit_counter else "n/a"

    print("\nGap Up Momentum Backtest Summary")
    print("=" * 92)
    print(f"Total days scanned:                        {total_days}")
    print(f"Days with qualifying gap (>= threshold):   {days_with_gap}")
    print(f"Days entry blocked by momentum failure:    {momentum_fail_days}")
    print(f"Days entry blocked by volume failure:      {volume_fail_days}")
    print(f"Days with valid entry:                     {valid_entry_days}")
    print(f"Win rate % (TP vs SL exits):               {win_rate:.2f}%")
    print(f"Total P&L across all trades:               ${total_pnl:.2f}")
    print(f"Average P&L per trade:                     ${avg_pnl:.2f}")
    print(f"Average hold time in minutes:              {avg_hold:.2f}")
    print(f"Most common exit reason:                   {common_exit}")
    print("=" * 92)

    print("\nPer Trade Detail")
    print("-" * 150)
    print(
        f"{'Date':<12} {'Gap %':>8} {'Entry ET':<25} {'Exit ET':<25} {'Exit':<12} "
        f"{'Entry':>10} {'Exit':>10} {'PnL $':>10} {'PnL %':>10}"
    )
    print("-" * 150)
    for trade in trades:
        print(
            f"{trade.trade_date.isoformat():<12} {trade.gap_pct * 100:>7.2f}% "
            f"{trade.entry_time_et.isoformat():<25} {trade.exit_time_et.isoformat():<25} "
            f"{trade.exit_reason:<12} {trade.entry_price:>10.4f} {trade.exit_price:>10.4f} "
            f"{trade.pnl_dollars:>10.4f} {trade.pnl_percent:>9.2f}%"
        )
    print("-" * 150)
    print(f"Runtime: {runtime_seconds:.2f} seconds")


def main() -> int:
    started = time.perf_counter()
    args = parse_args()
    symbol = args.symbol.upper()

    try:
        client = get_api_client()
        intraday = fetch_intraday_bars(client, symbol, args.start, args.end)
        daily = fetch_daily_bars(client, symbol, args.start, args.end)
        if len(daily) < 20:
            print("Warning: fewer than 20 trading days of daily data returned. Volume average may be unreliable.")

        daily_context = build_daily_context(daily)

        trades: list[TradeRecord] = []
        total_days = 0
        days_with_gap = 0
        momentum_fail_days = 0
        volume_fail_days = 0
        valid_entry_days = 0

        for trade_date, day_df in intraday.groupby("trade_date_et"):
            if trade_date not in daily_context:
                continue

            total_days += 1
            context = daily_context[trade_date]
            prior_close = float(context["prior_close"])
            avg_daily_volume = float(context["avg_daily_volume"])

            day_slice = day_df[
                (day_df["timestamp_et"].dt.time >= pd.Timestamp("09:30").time())
                & (day_df["timestamp_et"].dt.time <= pd.Timestamp("15:45").time())
            ][["timestamp", "open", "high", "low", "close", "volume"]].copy()

            if day_slice.empty:
                continue

            strategy = GapMomentum(
                gap_threshold=args.gap_threshold,
                momentum_bars=args.momentum_bars,
                stop_loss_pct=args.stop_loss,
                take_profit_pct=args.take_profit,
                volume_multiplier=args.volume_multiplier,
                symbol=symbol,
            )
            signal_df = strategy.calculate_signals(day_slice, prior_close=prior_close, avg_daily_volume=avg_daily_volume)

            day_status = str(signal_df["day_status"].iloc[0]) if not signal_df.empty else "no_gap"
            gap_pct = float(signal_df["gap_pct"].iloc[0]) if not signal_df.empty else 0.0
            if gap_pct >= args.gap_threshold:
                days_with_gap += 1
            if day_status == "momentum_fail":
                momentum_fail_days += 1
            if day_status == "volume_fail":
                volume_fail_days += 1
            if day_status == "entry":
                valid_entry_days += 1

            trade = extract_trade(day_slice, signal_df, symbol)
            if trade is not None:
                trades.append(trade)

        append_trades_to_journal(trades)
        runtime = time.perf_counter() - started
        print_summary(
            total_days=total_days,
            days_with_gap=days_with_gap,
            momentum_fail_days=momentum_fail_days,
            volume_fail_days=volume_fail_days,
            valid_entry_days=valid_entry_days,
            trades=trades,
            runtime_seconds=runtime,
        )
        return 0
    except Exception as exc:
        runtime = time.perf_counter() - started
        print(f"Backtest failed: {exc}")
        print(f"Runtime before failure: {runtime:.2f} seconds")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
