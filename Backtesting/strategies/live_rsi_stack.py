"""
Filename: live_rsi_stack.py
Purpose: Live or paper runner for multi timeframe RSI stack strategy.
Author: TODO
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, TypeVar

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

REPO_ROOT = Path(__file__).resolve().parents[2]
ALPACA_DIR = REPO_ROOT / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

from rsi_stack import RSIStack
from circuit_breaker import is_safe_to_trade

PAPER_TRADING = True
PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"

SYMBOL = "SPY"
FAST_TF = "1Hour"
SLOW_TF = "1Day"
BARS_LIMIT = 75
OVERSOLD = 35
OVERBOUGHT = 65

JOURNAL_CSV = REPO_ROOT / "Journal" / "trades.csv"
LIVE_LOG = REPO_ROOT / "Journal" / "live_rsi_stack_log.txt"
EXPECTED_JOURNAL_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]

T = TypeVar("T")


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


def ensure_journal_file() -> None:
    JOURNAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL_CSV.exists():
        return
    with JOURNAL_CSV.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writeheader()


def append_journal_row(symbol: str, side: str, qty: int, entry_price: float, exit_price: float, pnl: float, notes: str) -> None:
    ensure_journal_file()
    with JOURNAL_CSV.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writerow(
            {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "entry_price": f"{entry_price:.4f}",
                "exit_price": f"{exit_price:.4f}",
                "pnl": f"{pnl:.4f}",
                "notes": notes,
            }
        )


def load_credentials() -> tuple[str, str]:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise RuntimeError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")
    return api_key, secret_key


def log_message(message: str, snapshot: dict[str, float | int | str]) -> None:
    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    snapshot_text = " ".join(f"{key}={value}" for key, value in snapshot.items())
    line = f"{timestamp}\t{SYMBOL}\t{snapshot_text}\t{message}"
    with LIVE_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")
    print(line)


def call_with_retry(func: Callable[[], T], action_name: str) -> T:
    for attempt in range(2):
        try:
            return func()
        except APIError as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code == 429 and attempt == 0:
                print(f"Rate limit hit during {action_name}. Waiting 60 seconds before one retry.")
                time.sleep(60)
                continue
            raise


def fetch_latest_bars(data_client: StockHistoricalDataClient, timeframe_label: str) -> pd.DataFrame:
    start = datetime.now(timezone.utc) - timedelta(days=365)
    request = StockBarsRequest(
        symbol_or_symbols=SYMBOL,
        timeframe=timeframe_from_label(timeframe_label),
        start=start,
        end=datetime.now(timezone.utc),
        limit=BARS_LIMIT,
    )
    response = call_with_retry(lambda: data_client.get_stock_bars(request), f"fetch_{timeframe_label}")
    bars = response.df
    if bars.empty:
        raise RuntimeError(f"No bars returned for timeframe {timeframe_label}")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == SYMBOL]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").tail(BARS_LIMIT).reset_index(drop=True)
    return bars


def get_open_position(trading_client: TradingClient):
    try:
        return call_with_retry(lambda: trading_client.get_open_position(SYMBOL), "get_open_position")
    except APIError as exc:
        if getattr(exc, "status_code", None) == 404:
            return None
        raise


def main() -> int:
    try:
        api_key, secret_key = load_credentials()
        trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=PAPER_TRADING)
        data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

        base_url = PAPER_URL if PAPER_TRADING else LIVE_URL
        print(f"Running RSI Stack for {SYMBOL} using base URL {base_url}")
        if not PAPER_TRADING:
            print("WARNING: PAPER_TRADING is False. Live order routing is enabled.")

        bars_by_tf = {
            FAST_TF: fetch_latest_bars(data_client, FAST_TF),
            SLOW_TF: fetch_latest_bars(data_client, SLOW_TF),
        }

        strategy = RSIStack(
            timeframes=[FAST_TF, SLOW_TF],
            rsi_periods={FAST_TF: 14, SLOW_TF: 14},
            oversold=OVERSOLD,
            overbought=OVERBOUGHT,
            symbol=SYMBOL,
        )

        try:
            aligned = strategy.align_timeframes(bars_by_tf)
        except ValueError as exc:
            log_message(f"Alignment failure: {exc}", {"signal": "HOLD", "rsi_stack_score": 0})
            return 0

        signaled = strategy.calculate_signals(aligned)
        latest_signal = strategy.get_latest_signal(signaled)
        snapshot = strategy.get_stack_snapshot(signaled)
        latest_close = float(signaled.iloc[-1]["close"])
        print(
            f"Snapshot | close={latest_close:.2f} "
            + " ".join(f"{key}={value}" for key, value in snapshot.items())
        )

        if latest_signal == "HOLD":
            log_message("HOLD — no action taken", snapshot)
            return 0

        safe, reason = is_safe_to_trade()
        if not safe:
            log_message(f"Circuit breaker blocked trading: {reason}", snapshot)
            return 0

        position = get_open_position(trading_client)
        has_position = position is not None

        if latest_signal == "BUY" and not has_position:
            try:
                order = call_with_retry(
                    lambda: trading_client.submit_order(
                        MarketOrderRequest(
                            symbol=SYMBOL,
                            qty=1,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY,
                        )
                    ),
                    "submit_buy_order",
                )
                fill_price = float(getattr(order, "filled_avg_price", 0) or 0)
                append_journal_row(SYMBOL, "BUY", 1, fill_price, 0.0, 0.0, "live_rsi_stack_paper")
                log_message("BUY order submitted", snapshot)
            except Exception as exc:
                append_journal_row(SYMBOL, "BUY", 1, 0.0, 0.0, 0.0, "live_rsi_stack_paper")
                log_message(f"BUY order failed: {exc}", snapshot)
            return 0

        if latest_signal == "SELL" and has_position:
            try:
                avg_entry = float(getattr(position, "avg_entry_price", 0) or 0)
                close_order = call_with_retry(lambda: trading_client.close_position(SYMBOL), "close_position")
                fill_price = float(getattr(close_order, "filled_avg_price", 0) or 0)
                append_journal_row(SYMBOL, "SELL", 1, avg_entry, fill_price, 0.0, "live_rsi_stack_paper")
                log_message("SELL close order submitted", snapshot)
            except Exception as exc:
                append_journal_row(SYMBOL, "SELL", 1, 0.0, 0.0, 0.0, "live_rsi_stack_paper")
                log_message(f"SELL order failed: {exc}", snapshot)
            return 0

        if latest_signal == "BUY" and has_position:
            log_message("BUY signal ignored because position already open", snapshot)
            return 0

        if latest_signal == "SELL" and not has_position:
            log_message("SELL signal ignored because no open position", snapshot)
            return 0

        log_message("No actionable condition met", snapshot)
        return 0
    except Exception as exc:
        fallback_snapshot = {"signal": "HOLD", "rsi_stack_score": 0}
        log_message(f"Runner exited after error: {exc}", fallback_snapshot)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
