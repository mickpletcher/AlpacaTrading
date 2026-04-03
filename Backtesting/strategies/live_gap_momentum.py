"""
Filename: live_gap_momentum.py
Purpose: Live paper or live execution runner for Gap Up Momentum intraday strategy.
Author: TODO
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, TypeVar
from zoneinfo import ZoneInfo

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

from circuit_breaker import is_safe_to_trade
from gap_momentum import EOD_EXIT, SCAN_END, SCAN_START, GapMomentum

ET_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")

PAPER_TRADING = True
PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"

SYMBOL = "SPY"
GAP_THRESHOLD = 0.02
MOMENTUM_BARS = 3
STOP_LOSS_PCT = 0.015
TAKE_PROFIT_PCT = 0.04
VOLUME_MULTIPLIER = 1.5
POLL_INTERVAL_SEC = 30
SCAN_START_TIME = datetime.strptime(SCAN_START, "%H:%M").time()
SCAN_END_TIME = datetime.strptime(SCAN_END, "%H:%M").time()
EOD_EXIT_TIME = datetime.strptime(EOD_EXIT, "%H:%M").time()

JOURNAL_CSV = REPO_ROOT / "Journal" / "trades.csv"
LIVE_LOG = REPO_ROOT / "Journal" / "live_gap_momentum_log.txt"
EXPECTED_JOURNAL_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]

T = TypeVar("T")


def et_now() -> datetime:
    return datetime.now(tz=ET_TZ)


def ensure_journal_file() -> None:
    JOURNAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    if JOURNAL_CSV.exists():
        return
    with JOURNAL_CSV.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writeheader()


def append_trade_rows(
    symbol: str,
    entry_price: float,
    exit_price: float,
    pnl: float,
    exit_reason: str,
) -> None:
    ensure_journal_file()
    note_prefix = "paper" if PAPER_TRADING else "live"
    note_value = f"live_gap_momentum_{note_prefix}_{exit_reason}"
    trade_date = et_now().date().isoformat()

    with JOURNAL_CSV.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXPECTED_JOURNAL_COLUMNS)
        writer.writerow(
            {
                "date": trade_date,
                "symbol": symbol,
                "side": "BUY",
                "qty": 1,
                "entry_price": f"{entry_price:.4f}",
                "exit_price": "0.0000",
                "pnl": "0.0000",
                "notes": note_value,
            }
        )
        writer.writerow(
            {
                "date": trade_date,
                "symbol": symbol,
                "side": "SELL",
                "qty": 1,
                "entry_price": f"{entry_price:.4f}",
                "exit_price": f"{exit_price:.4f}",
                "pnl": f"{pnl:.4f}",
                "notes": note_value,
            }
        )


def log_message(message: str, gap_pct: float | None = None, volume_ratio: float | None = None, exit_reason: str = "") -> None:
    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC_TZ).isoformat()
    parts = [stamp, SYMBOL, message]
    if gap_pct is not None:
        parts.append(f"gap_pct={gap_pct:.4%}")
    if volume_ratio is not None:
        parts.append(f"volume_ratio={volume_ratio:.2f}")
    if exit_reason:
        parts.append(f"exit_reason={exit_reason}")
    line = "\t".join(parts)
    with LIVE_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")
    print(line)


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
                log_message(f"Rate limit during {action_name}. Waiting 60 seconds before one retry.")
                time.sleep(60)
                continue
            raise


def fetch_daily_context(data_client: StockHistoricalDataClient, symbol: str) -> tuple[float, float]:
    end_utc = datetime.now(tz=UTC_TZ)
    start_utc = end_utc - timedelta(days=60)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start_utc,
        end=end_utc,
    )
    bars = call_with_retry(lambda: data_client.get_stock_bars(request), "fetch_daily_context").df
    if bars.empty:
        raise RuntimeError("No daily bars returned for startup checks.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    if len(bars) < 21:
        raise RuntimeError("Need at least 21 daily bars to compute prior close and 20 day average volume.")

    prior_close = float(bars.iloc[-2]["close"])
    avg_daily_volume = float(bars.iloc[-21:-1]["volume"].mean())
    return prior_close, avg_daily_volume


def fetch_today_minute_bars(data_client: StockHistoricalDataClient, symbol: str) -> pd.DataFrame:
    now_utc = datetime.now(tz=UTC_TZ)
    start_et = datetime.combine(et_now().date(), SCAN_START_TIME, tzinfo=ET_TZ)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=start_et.astimezone(UTC_TZ),
        end=now_utc,
    )
    bars = call_with_retry(lambda: data_client.get_stock_bars(request), "fetch_today_minute_bars").df
    if bars.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    return bars


def fetch_latest_price(data_client: StockHistoricalDataClient, symbol: str) -> float:
    now_utc = datetime.now(tz=UTC_TZ)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=now_utc - timedelta(minutes=10),
        end=now_utc,
        limit=1,
    )
    bars = call_with_retry(lambda: data_client.get_stock_bars(request), "fetch_latest_price").df
    if bars.empty:
        raise RuntimeError("No latest minute bar available.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol]
    else:
        bars = bars.reset_index()

    return float(bars.iloc[-1]["close"])


def wait_until(target_et: datetime) -> None:
    while et_now() < target_et:
        remaining = (target_et - et_now()).total_seconds()
        sleep_for = min(30, max(1, int(remaining)))
        time.sleep(sleep_for)


def confirm_fill_price(trading_client: TradingClient, order_id: str) -> float | None:
    deadline = time.time() + 30
    while time.time() < deadline:
        order = call_with_retry(lambda: trading_client.get_order_by_id(order_id), "get_order_by_id")
        fill_price = getattr(order, "filled_avg_price", None)
        if fill_price:
            return float(fill_price)
        time.sleep(2)
    return None


def attempt_force_exit(trading_client: TradingClient, reason: str) -> bool:
    for _ in range(5):
        try:
            call_with_retry(lambda: trading_client.close_position(SYMBOL), "close_position_force")
            log_message("Force exit order submitted.", exit_reason=reason)
            return True
        except Exception as exc:
            log_message(f"Force exit retry failed: {exc}", exit_reason=reason)
            time.sleep(15)
    return False


def run_scan_phase(
    strategy: GapMomentum,
    data_client: StockHistoricalDataClient,
    trading_client: TradingClient,
    prior_close: float,
    avg_daily_volume: float,
) -> tuple[float, pd.Timestamp, float, float] | None:
    if et_now().time() >= SCAN_END_TIME:
        log_message("Launched after scan window ended. Exiting without trade.")
        return None

    first_bar_ready = datetime.combine(et_now().date(), SCAN_START_TIME, tzinfo=ET_TZ) + timedelta(minutes=1)
    if et_now() < first_bar_ready:
        wait_until(first_bar_ready)

    bars = fetch_today_minute_bars(data_client, SYMBOL)
    if bars.empty:
        log_message("No minute bars available after open. Exiting.")
        return None

    first_bar = bars.iloc[0]
    today_open = float(first_bar["open"])
    gap_pct_raw = (today_open - prior_close) / prior_close if prior_close > 0 else 0.0

    gap_pct = strategy.detect_gap(today_open=today_open, prior_close=prior_close)
    if gap_pct is None:
        log_message(f"No gap today. gap was {gap_pct_raw:.4%}", gap_pct=gap_pct_raw)
        return None

    expected_per_minute = avg_daily_volume / 390 if avg_daily_volume > 0 else 0.0
    volume_ratio = float(first_bar["volume"]) / expected_per_minute if expected_per_minute > 0 else 0.0
    log_message("Qualifying gap detected. Waiting for momentum confirmation.", gap_pct=gap_pct, volume_ratio=volume_ratio)

    while True:
        bars = fetch_today_minute_bars(data_client, SYMBOL)
        if len(bars) >= 1 + MOMENTUM_BARS:
            break
        if et_now().time() > SCAN_END_TIME:
            log_message("Not enough confirmation bars before scan window ended.", gap_pct=gap_pct, volume_ratio=volume_ratio)
            return None
        time.sleep(5)

    momentum_bars = bars.iloc[1 : 1 + MOMENTUM_BARS]
    momentum_ok = strategy.confirm_momentum(momentum_bars)
    volume_ok = strategy.confirm_volume(float(first_bar["volume"]), avg_daily_volume)

    if not momentum_ok or not volume_ok:
        fail_bits: list[str] = []
        if not momentum_ok:
            fail_bits.append("momentum")
        if not volume_ok:
            fail_bits.append("volume")
        log_message(
            "Gap found but confirmation failed: " + ",".join(fail_bits),
            gap_pct=gap_pct,
            volume_ratio=volume_ratio,
        )
        return None

    buy_order = call_with_retry(
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

    fill_price = confirm_fill_price(trading_client, str(buy_order.id))
    if fill_price is None:
        log_message("BUY submitted but no fill confirmation in 30 seconds. Attempting cancel.", gap_pct=gap_pct, volume_ratio=volume_ratio)
        try:
            call_with_retry(lambda: trading_client.cancel_order_by_id(str(buy_order.id)), "cancel_buy_order")
        except Exception as exc:
            log_message(f"Cancel after unfilled buy failed: {exc}", gap_pct=gap_pct, volume_ratio=volume_ratio)
        return None

    entry_time = pd.Timestamp(datetime.now(tz=UTC_TZ))
    log_message("BUY filled and hold phase started.", gap_pct=gap_pct, volume_ratio=volume_ratio)
    return fill_price, entry_time, gap_pct, volume_ratio


def run_hold_phase(
    data_client: StockHistoricalDataClient,
    trading_client: TradingClient,
    entry_price: float,
    entry_time: pd.Timestamp,
    gap_pct: float,
    volume_ratio: float,
) -> tuple[float, str, int]:
    stop_price = entry_price * (1 - STOP_LOSS_PCT)
    take_price = entry_price * (1 + TAKE_PROFIT_PCT)

    while True:
        now_et = et_now()
        elapsed_minutes = int((pd.Timestamp(datetime.now(tz=UTC_TZ)) - entry_time).total_seconds() // 60)

        if now_et.time() >= EOD_EXIT_TIME:
            exit_reason = "eod_exit"
        else:
            exit_reason = ""

        try:
            current_price = fetch_latest_price(data_client, SYMBOL)
        except Exception as exc:
            log_message(f"API error during hold: {exc}", gap_pct=gap_pct, volume_ratio=volume_ratio)
            force_ok = attempt_force_exit(trading_client, "eod_exit")
            if force_ok:
                return entry_price, "eod_exit", elapsed_minutes
            return entry_price, "eod_exit", elapsed_minutes

        unrealized = current_price - entry_price
        unrealized_pct = (unrealized / entry_price) * 100 if entry_price else 0.0

        if not exit_reason:
            if current_price <= stop_price:
                exit_reason = "stop_loss"
            elif current_price >= take_price:
                exit_reason = "take_profit"

        if exit_reason:
            try:
                close_order = call_with_retry(lambda: trading_client.close_position(SYMBOL), "close_position")
                exit_price = float(getattr(close_order, "filled_avg_price", None) or current_price)
            except Exception:
                force_ok = attempt_force_exit(trading_client, "eod_exit")
                exit_reason = "eod_exit"
                exit_price = current_price
                if not force_ok:
                    log_message("Force exit could not be confirmed.", gap_pct=gap_pct, volume_ratio=volume_ratio, exit_reason=exit_reason)
            log_message(
                f"Exit triggered. entry={entry_price:.4f} exit={exit_price:.4f} pnl={exit_price - entry_price:.4f}",
                gap_pct=gap_pct,
                volume_ratio=volume_ratio,
                exit_reason=exit_reason,
            )
            return exit_price, exit_reason, elapsed_minutes

        log_message(
            (
                f"HOLD current={current_price:.4f} entry={entry_price:.4f} "
                f"unrealized={unrealized:.4f} unrealized_pct={unrealized_pct:.2f}% elapsed_min={elapsed_minutes}"
            ),
            gap_pct=gap_pct,
            volume_ratio=volume_ratio,
        )
        time.sleep(POLL_INTERVAL_SEC)


def main() -> int:
    try:
        if not PAPER_TRADING:
            print("WARNING: PAPER_TRADING is False. LIVE ORDER ROUTING IS ENABLED.")
            print("WARNING: REVIEW SETTINGS BEFORE CONTINUING.")

        safe_to_trade, safe_reason = is_safe_to_trade()
        if not safe_to_trade:
            log_message(f"Circuit breaker blocked startup: {safe_reason}")
            return 0

        api_key, secret_key = load_credentials()
        trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=PAPER_TRADING)
        data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

        base_url = PAPER_URL if PAPER_TRADING else LIVE_URL
        log_message(f"Session started. base_url={base_url}")

        prior_close, avg_daily_volume = fetch_daily_context(data_client, SYMBOL)
        log_message(f"Startup context prior_close={prior_close:.4f} avg_daily_volume={avg_daily_volume:.0f}")

        strategy = GapMomentum(
            gap_threshold=GAP_THRESHOLD,
            momentum_bars=MOMENTUM_BARS,
            stop_loss_pct=STOP_LOSS_PCT,
            take_profit_pct=TAKE_PROFIT_PCT,
            volume_multiplier=VOLUME_MULTIPLIER,
            symbol=SYMBOL,
        )

        scan_result = run_scan_phase(strategy, data_client, trading_client, prior_close, avg_daily_volume)
        if scan_result is None:
            return 0

        entry_price, entry_time, gap_pct, volume_ratio = scan_result
        exit_price, exit_reason, hold_minutes = run_hold_phase(
            data_client,
            trading_client,
            entry_price=entry_price,
            entry_time=entry_time,
            gap_pct=gap_pct,
            volume_ratio=volume_ratio,
        )

        pnl = exit_price - entry_price
        append_trade_rows(SYMBOL, entry_price, exit_price, pnl, exit_reason)
        log_message(
            f"Round trip complete entry={entry_price:.4f} exit={exit_price:.4f} pnl={pnl:.4f} hold_min={hold_minutes}",
            gap_pct=gap_pct,
            volume_ratio=volume_ratio,
            exit_reason=exit_reason,
        )
        return 0
    except Exception as exc:
        log_message(f"Runner exited after error: {exc}", exit_reason="eod_exit")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
