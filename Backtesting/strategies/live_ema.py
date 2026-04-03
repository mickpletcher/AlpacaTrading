"""
Filename: live_ema.py
Purpose: Execute live paper or live trading actions using the shared EMA crossover strategy.
Author: TODO
"""

from __future__ import annotations

import argparse
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
from alpaca.data.timeframe import TimeFrame
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

from ema_crossover import EMAcrossover
from circuit_breaker import is_safe_to_trade

PAPER_TRADING = True
PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"

JOURNAL_CSV = REPO_ROOT / "Journal" / "trades.csv"
LIVE_LOG = REPO_ROOT / "Journal" / "live_ema_log.txt"
EXPECTED_JOURNAL_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]

T = TypeVar("T")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EMA crossover live or paper orders.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--fast", type=int, default=9)
    parser.add_argument("--slow", type=int, default=21)
    return parser.parse_args()


def log_message(message: str) -> None:
    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with LIVE_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{message}\n")
    print(f"{timestamp} | {message}")


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


def call_with_retry(func: Callable[[], T], action_name: str) -> T:
    for attempt in range(2):
        try:
            return func()
        except APIError as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code == 429 and attempt == 0:
                log_message(f"Rate limit hit during {action_name}. Waiting 60 seconds before one retry.")
                time.sleep(60)
                continue
            raise


def fetch_recent_daily_bars(data_client: StockHistoricalDataClient, symbol: str) -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=180)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    response = call_with_retry(lambda: data_client.get_stock_bars(request), "fetch_recent_daily_bars")
    bars = response.df
    if bars.empty:
        raise RuntimeError("No bars returned from Alpaca for live signal generation.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()
        bars["symbol"] = symbol

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").tail(50).reset_index(drop=True)
    return bars


def get_open_position(trading_client: TradingClient, symbol: str):
    try:
        return call_with_retry(lambda: trading_client.get_open_position(symbol), "get_open_position")
    except APIError as exc:
        if getattr(exc, "status_code", None) == 404:
            return None
        raise


def main() -> int:
    args = parse_args()
    symbol = args.symbol.upper()

    try:
        api_key, secret_key = load_credentials()
        trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=PAPER_TRADING)
        data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

        base_url = PAPER_URL if PAPER_TRADING else LIVE_URL
        log_message(f"Running EMA strategy for {symbol} using base URL {base_url}")

        if not PAPER_TRADING:
            log_message("WARNING: PAPER_TRADING is False. Live order routing is enabled.")
            print("WARNING: PAPER_TRADING is False. Live order routing is enabled.")

        bars = fetch_recent_daily_bars(data_client, symbol)
        strategy = EMAcrossover(fast_period=args.fast, slow_period=args.slow, symbol=symbol)
        signaled = strategy.calculate_signals(bars)
        latest_signal = strategy.get_latest_signal(signaled)
        log_message(f"Latest signal: {latest_signal}")

        position = get_open_position(trading_client, symbol)
        has_position = position is not None

        if latest_signal == "HOLD":
            log_message("HOLD — no action taken")
            return 0

        safe, reason = is_safe_to_trade()
        if not safe:
            log_message(f"Circuit breaker blocked trading: {reason}")
            return 0

        if latest_signal == "BUY" and not has_position:
            try:
                order = call_with_retry(
                    lambda: trading_client.submit_order(
                        MarketOrderRequest(
                            symbol=symbol,
                            qty=1,
                            side=OrderSide.BUY,
                            time_in_force=TimeInForce.DAY,
                        )
                    ),
                    "submit_buy_order",
                )
                fill_price = float(getattr(order, "filled_avg_price", 0) or 0)
                append_journal_row(symbol, "BUY", 1, fill_price, 0.0, 0.0, "live_ema_crossover_paper")
                log_message(f"BUY order submitted successfully for {symbol}.")
            except Exception as exc:
                append_journal_row(symbol, "BUY", 1, 0.0, 0.0, 0.0, "live_ema_crossover_paper")
                log_message(f"BUY order failed for {symbol}: {exc}")
            return 0

        if latest_signal == "SELL" and has_position:
            try:
                avg_entry = float(getattr(position, "avg_entry_price", 0) or 0)
                close_order = call_with_retry(lambda: trading_client.close_position(symbol), "close_position")
                fill_price = float(getattr(close_order, "filled_avg_price", 0) or 0)
                append_journal_row(symbol, "SELL", 1, avg_entry, fill_price, 0.0, "live_ema_crossover_paper")
                log_message(f"SELL close order submitted successfully for {symbol}.")
            except Exception as exc:
                append_journal_row(symbol, "SELL", 1, 0.0, 0.0, 0.0, "live_ema_crossover_paper")
                log_message(f"SELL close order failed for {symbol}: {exc}")
            return 0

        if latest_signal == "BUY" and has_position:
            log_message("BUY signal ignored because position is already open.")
            return 0

        if latest_signal == "SELL" and not has_position:
            log_message("SELL signal ignored because no open position exists.")
            return 0

        log_message("No actionable condition met.")
        return 0
    except Exception as exc:
        log_message(f"Live EMA runner exited after error: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
