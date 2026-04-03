"""
Filename: test_rsi_stack.py
Purpose: Validate multi timeframe RSI stack logic using synthetic data only.
Author: TODO

Run with:
pytest Tests/test_rsi_stack.py -v

Synthetic data is used so tests are deterministic, fast, and independent of live Alpaca API availability.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from Backtesting.strategies.rsi_stack import RSIStack


def make_ohlcv(n: int, base_price: float, trend: str) -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    if trend == "flat":
        close = np.full(n, base_price, dtype=float)
    elif trend == "up":
        close = np.array([base_price + idx * 0.8 for idx in range(n)], dtype=float)
    elif trend == "down":
        close = np.array([base_price - idx * 0.8 for idx in range(n)], dtype=float)
    elif trend == "volatile":
        close = np.array([base_price + math.sin(idx / 3) * 4 + ((-1) ** idx) * 1.2 for idx in range(n)], dtype=float)
    else:
        raise ValueError("trend must be flat, up, down, or volatile")

    return pd.DataFrame(
        {
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1000),
        },
        index=index,
    )


def make_multiframe_bars(n: int) -> dict[str, pd.DataFrame]:
    hourly = make_ohlcv(n, 100, "volatile")
    daily = hourly.resample("1D").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    ).dropna()
    return {"1Hour": hourly.reset_index().rename(columns={"index": "timestamp"}), "1Day": daily.reset_index().rename(columns={"index": "timestamp"})}


def test_rsi_wilder_smoothing() -> None:
    closes = [
        44.34,
        44.09,
        44.15,
        43.61,
        44.33,
        44.83,
        45.10,
        45.42,
        45.84,
        46.08,
        45.89,
        46.03,
        45.61,
        46.28,
        46.28,
        46.00,
        46.03,
        46.41,
        46.22,
        45.64,
        46.21,
    ]
    df = pd.DataFrame(
        {
            "open": closes,
            "high": [value + 0.1 for value in closes],
            "low": [value - 0.1 for value in closes],
            "close": closes,
            "volume": [1000] * len(closes),
        }
    )
    strategy = RSIStack()
    rsi = strategy.calculate_rsi(df, 14).round(2)
    assert float(rsi.iloc[14]) == 50.66
    assert float(rsi.iloc[19]) == 43.20
    assert float(rsi.iloc[20]) == 50.40


def test_rsi_bounds_all_timeframes() -> None:
    strategy = RSIStack()
    for trend in ["flat", "up", "down"]:
        df = make_ohlcv(200, 100, trend)
        rsi = strategy.calculate_rsi(df, 14)
        tail = rsi.iloc[14:]
        assert not tail.isna().any()
        assert ((tail >= 0) & (tail <= 100)).all()


def test_alignment_produces_rsi_columns() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"], rsi_periods={"1Hour": 14, "1Day": 14})
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    assert "rsi_1Hour" in aligned.columns
    assert "rsi_1Day" in aligned.columns
    assert not aligned[["rsi_1Hour", "rsi_1Day"]].iloc[14:].isna().any().any()


def test_no_signal_when_timeframes_disagree() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    aligned["rsi_1Hour"] = 20
    aligned["rsi_1Day"] = 50
    signals = strategy.calculate_signals(aligned)
    assert "BUY" not in signals["signal"].values


def test_buy_requires_full_stack_agreement() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    aligned["rsi_1Hour"] = 50
    aligned["rsi_1Day"] = 50
    aligned.loc[100:, "rsi_1Hour"] = 20
    aligned.loc[100:, "rsi_1Day"] = 25
    signals = strategy.calculate_signals(aligned)
    assert "BUY" in signals["signal"].values


def test_sell_requires_full_stack_agreement() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    strategy.position_open = True
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    aligned["rsi_1Hour"] = 50
    aligned["rsi_1Day"] = 50
    aligned.loc[120:, "rsi_1Hour"] = 80
    aligned.loc[120:, "rsi_1Day"] = 85
    signals = strategy.calculate_signals(aligned)
    assert "SELL" in signals["signal"].values


def test_no_double_signals() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    aligned["rsi_1Hour"] = np.where(np.arange(len(aligned)) % 40 < 20, 20, 80)
    aligned["rsi_1Day"] = np.where(np.arange(len(aligned)) % 40 < 20, 25, 85)
    strategy.position_open = False
    signals = strategy.calculate_signals(aligned)
    actionable = [signal for signal in signals["signal"].tolist() if signal in {"BUY", "SELL"}]
    assert all(actionable[idx] != actionable[idx + 1] for idx in range(len(actionable) - 1))


def test_position_gating() -> None:
    aligned = RSIStack(timeframes=["1Hour", "1Day"]).align_timeframes(make_multiframe_bars(720))

    buy_blocked = RSIStack(timeframes=["1Hour", "1Day"])
    buy_blocked.position_open = True
    buy_df = aligned.copy()
    buy_df["rsi_1Hour"] = 20
    buy_df["rsi_1Day"] = 20
    buy_signals = buy_blocked.calculate_signals(buy_df)
    assert "BUY" not in buy_signals["signal"].values

    sell_blocked = RSIStack(timeframes=["1Hour", "1Day"])
    sell_blocked.position_open = False
    sell_df = aligned.copy()
    sell_df["rsi_1Hour"] = 80
    sell_df["rsi_1Day"] = 80
    sell_signals = sell_blocked.calculate_signals(sell_df)
    assert "SELL" not in sell_signals["signal"].values


def test_stack_score_range() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    signals = strategy.calculate_signals(aligned)
    assert ((signals["rsi_stack_score"] >= 0) & (signals["rsi_stack_score"] <= len(strategy.timeframes))).all()


def test_summarize_runs_without_error() -> None:
    strategy = RSIStack(timeframes=["1Hour", "1Day"])
    aligned = strategy.align_timeframes(make_multiframe_bars(720))
    signals = strategy.calculate_signals(aligned)
    strategy.summarize(signals)
