"""
Filename: test_gap_momentum.py
Purpose: Validate Gap Up Momentum strategy behavior using synthetic intraday bars only.
Author: TODO

Run with:
pytest Tests/test_gap_momentum.py -v

All tests use synthetic bars with no Alpaca API calls.
Exit paths are tested independently so stop loss, take profit, and end of day exit each remain safe before live deployment.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from Backtesting.strategies.gap_momentum import GapMomentum

ET_TZ = ZoneInfo("America/New_York")


def make_minute_bars(
    n: int,
    open_price: float,
    trend: str,
    volume_per_bar: float,
    start_hour: int = 9,
    start_minute: int = 30,
) -> pd.DataFrame:
    rows: list[dict[str, float | pd.Timestamp]] = []
    ts = datetime(2026, 1, 5, start_hour, start_minute, tzinfo=ET_TZ)
    current_open = open_price

    for index in range(n):
        if trend == "up":
            close_price = current_open * 1.002
        elif trend == "down":
            close_price = current_open * 0.998
        elif trend == "flat":
            close_price = current_open
        elif trend == "volatile":
            if index % 2 == 0:
                close_price = current_open * 1.003
            else:
                close_price = current_open * 0.997
        else:
            raise ValueError("trend must be up, down, flat, or volatile")

        high_price = max(current_open, close_price) * 1.001
        low_price = min(current_open, close_price) * 0.999
        rows.append(
            {
                "timestamp": pd.Timestamp(ts.astimezone(ZoneInfo("UTC"))),
                "open": float(current_open),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": float(volume_per_bar),
            }
        )
        current_open = close_price
        ts += timedelta(minutes=1)

    return pd.DataFrame(rows)


def make_gap_day(gap_pct: float, momentum: str, volume_ratio: float) -> tuple[pd.DataFrame, float, float]:
    prior_close = 100.0
    avg_daily_volume = 390000.0
    expected_per_minute = avg_daily_volume / 390
    first_volume = expected_per_minute * volume_ratio

    base = make_minute_bars(400, prior_close * (1 + gap_pct), "flat", expected_per_minute)

    base.at[0, "open"] = prior_close * (1 + gap_pct)
    base.at[0, "close"] = base.at[0, "open"] * 1.001
    base.at[0, "high"] = max(base.at[0, "open"], base.at[0, "close"]) * 1.001
    base.at[0, "low"] = min(base.at[0, "open"], base.at[0, "close"]) * 0.999
    base.at[0, "volume"] = first_volume

    for idx in range(1, 4):
        open_price = float(base.at[idx - 1, "close"])
        if momentum == "up":
            close_price = open_price * 1.002
        elif momentum == "down":
            close_price = open_price * 0.998
        else:
            close_price = open_price
        base.at[idx, "open"] = open_price
        base.at[idx, "close"] = close_price
        base.at[idx, "high"] = max(open_price, close_price) * 1.001
        base.at[idx, "low"] = min(open_price, close_price) * 0.999
        base.at[idx, "volume"] = expected_per_minute

    for idx in range(4, len(base)):
        prev_close = float(base.at[idx - 1, "close"])
        close_price = prev_close * 1.0001
        base.at[idx, "open"] = prev_close
        base.at[idx, "close"] = close_price
        base.at[idx, "high"] = max(prev_close, close_price) * 1.001
        base.at[idx, "low"] = min(prev_close, close_price) * 0.999
        base.at[idx, "volume"] = expected_per_minute

    return base, prior_close, avg_daily_volume


def test_gap_detection_above_threshold() -> None:
    strategy = GapMomentum()
    gap = strategy.detect_gap(today_open=103.0, prior_close=100.0)
    assert gap is not None
    assert round(gap, 4) == 0.03


def test_gap_detection_below_threshold() -> None:
    strategy = GapMomentum()
    gap = strategy.detect_gap(today_open=101.0, prior_close=100.0)
    assert gap is None


def test_momentum_confirmation_all_green() -> None:
    strategy = GapMomentum(momentum_bars=3)
    bars = make_minute_bars(3, 100, "up", 1000)
    assert strategy.confirm_momentum(bars) is True


def test_momentum_confirmation_one_red() -> None:
    strategy = GapMomentum(momentum_bars=3)
    bars = make_minute_bars(3, 100, "up", 1000)
    bars.at[1, "close"] = bars.at[1, "open"] * 0.999
    assert strategy.confirm_momentum(bars) is False


def test_volume_confirmation_passes() -> None:
    strategy = GapMomentum(volume_multiplier=1.5)
    assert strategy.confirm_volume(first_bar_volume=2000, avg_daily_volume=390000) is True


def test_volume_confirmation_fails() -> None:
    strategy = GapMomentum(volume_multiplier=1.5)
    assert strategy.confirm_volume(first_bar_volume=1200, avg_daily_volume=390000) is False


def test_no_entry_outside_scan_window() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    shifted = intraday.copy()
    shifted["timestamp"] = shifted["timestamp"] + pd.Timedelta(minutes=20)
    signaled = strategy.calculate_signals(shifted, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    assert "BUY" not in signaled["signal"].values


def test_stop_loss_triggers() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    signaled = strategy.calculate_signals(intraday, prior_close=prior_close, avg_daily_volume=avg_daily_volume)

    buy_idx = signaled.index[signaled["signal"] == "BUY"][0]
    entry_price = float(signaled.at[buy_idx, "close"])
    forced = intraday.copy()
    forced.at[buy_idx + 1, "close"] = entry_price * 0.984
    forced.at[buy_idx + 1, "open"] = entry_price * 0.99

    re_signaled = strategy.calculate_signals(forced, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    exit_idx = re_signaled.index[re_signaled["signal"].isin(["STOP_LOSS", "TAKE_PROFIT", "EOD_EXIT"])][0]
    assert re_signaled.at[exit_idx, "signal"] == "STOP_LOSS"


def test_take_profit_triggers() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    signaled = strategy.calculate_signals(intraday, prior_close=prior_close, avg_daily_volume=avg_daily_volume)

    buy_idx = signaled.index[signaled["signal"] == "BUY"][0]
    entry_price = float(signaled.at[buy_idx, "close"])
    forced = intraday.copy()
    forced.at[buy_idx + 1, "close"] = entry_price * 1.041
    forced.at[buy_idx + 1, "open"] = entry_price * 1.01

    re_signaled = strategy.calculate_signals(forced, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    exit_idx = re_signaled.index[re_signaled["signal"].isin(["STOP_LOSS", "TAKE_PROFIT", "EOD_EXIT"])][0]
    assert re_signaled.at[exit_idx, "signal"] == "TAKE_PROFIT"


def test_eod_exit_triggers() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    intraday["close"] = intraday["open"] * 1.0002
    signaled = strategy.calculate_signals(intraday, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    assert "EOD_EXIT" in signaled["signal"].values


def test_no_double_entry() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    signaled = strategy.calculate_signals(intraday, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    assert int((signaled["signal"] == "BUY").sum()) == 1


def test_summarize_runs_without_error() -> None:
    strategy = GapMomentum()
    intraday, prior_close, avg_daily_volume = make_gap_day(0.03, "up", 2.0)
    signaled = strategy.calculate_signals(intraday, prior_close=prior_close, avg_daily_volume=avg_daily_volume)
    strategy.summarize(signaled)
