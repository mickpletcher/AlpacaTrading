"""
Filename: test_bollinger_rsi.py
Purpose: Validate Bollinger Bands plus RSI strategy logic using synthetic data only.
Author: TODO

Run with:
pytest Tests/test_bollinger_rsi.py -v
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from Backtesting.strategies.bollinger_rsi import BollingerRSI


def make_price_series(n: int, base: float, direction: str) -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC")
    if direction == "flat":
        close = np.full(n, base, dtype=float)
    elif direction == "up":
        close = np.array([base + idx * 1.5 for idx in range(n)], dtype=float)
    elif direction == "down":
        close = np.array([base - idx * 1.5 for idx in range(n)], dtype=float)
    else:
        raise ValueError("direction must be flat, up, or down")

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1000),
        }
    )


def test_indicator_columns_exist() -> None:
    strategy = BollingerRSI(symbol="SPY")
    indicators = strategy.calculate_indicators(make_price_series(120, 100, "flat"))
    for column in ["bb_upper", "bb_lower", "bb_middle", "bb_bandwidth", "rsi"]:
        assert column in indicators.columns


def test_rsi_bounds() -> None:
    strategy = BollingerRSI(symbol="SPY")
    indicators = strategy.calculate_indicators(make_price_series(160, 100, "up"))
    rsi_tail = indicators["rsi"].iloc[14:]
    assert not rsi_tail.isna().any()
    assert ((rsi_tail >= 0) & (rsi_tail <= 100)).all()


def test_no_buy_in_trending_market() -> None:
    strategy = BollingerRSI(symbol="SPY")
    signals = strategy.calculate_signals(make_price_series(200, 20, "up"))
    bandwidth_tail = signals["bb_bandwidth"].dropna()
    above_threshold_ratio = (bandwidth_tail > 0.1).mean() if not bandwidth_tail.empty else 0
    assert above_threshold_ratio > 0.7
    assert "BUY" not in signals["signal"].values


def test_buy_requires_both_conditions() -> None:
    base = BollingerRSI(symbol="SPY")
    frame = make_price_series(80, 100, "flat")
    indicators = base.calculate_indicators(frame)
    indicators["signal"] = "HOLD"

    case_one = indicators.copy()
    case_one.at[40, "close"] = case_one.at[40, "bb_lower"] - 1
    case_one.at[39, "close"] = case_one.at[39, "bb_lower"] + 1
    case_one.at[40, "rsi"] = 45
    case_one.at[40, "bb_bandwidth"] = 0.05

    strategy_one = BollingerRSI(symbol="SPY")
    strategy_one.calculate_indicators = lambda _df: case_one  # type: ignore[method-assign]
    output_one = strategy_one.calculate_signals(frame)
    assert "BUY" not in output_one["signal"].values

    case_two = indicators.copy()
    case_two.at[40, "close"] = case_two.at[40, "bb_middle"]
    case_two.at[39, "close"] = case_two.at[39, "bb_middle"]
    case_two.at[40, "rsi"] = 25
    case_two.at[40, "bb_bandwidth"] = 0.05

    strategy_two = BollingerRSI(symbol="SPY")
    strategy_two.calculate_indicators = lambda _df: case_two  # type: ignore[method-assign]
    output_two = strategy_two.calculate_signals(frame)
    assert "BUY" not in output_two["signal"].values


def test_sell_signal_on_upper_band_breach() -> None:
    strategy = BollingerRSI(symbol="SPY")
    strategy.position_open = True
    frame = make_price_series(80, 100, "flat")
    base = strategy.calculate_indicators(frame)
    base["signal"] = "HOLD"
    base.at[39, "close"] = base.at[39, "bb_upper"] - 1
    base.at[40, "close"] = base.at[40, "bb_upper"] + 1
    base.at[40, "rsi"] = 75

    strategy.calculate_indicators = lambda _df: base  # type: ignore[method-assign]
    signals = strategy.calculate_signals(frame)
    assert "SELL" in signals["signal"].values


def test_no_double_signals() -> None:
    strategy = BollingerRSI(symbol="SPY")
    close = [
        100, 101, 102, 103, 104, 105, 104, 103, 102, 101,
        100, 99, 98, 97, 96, 95, 96, 97, 98, 99,
        100, 101, 102, 103, 104, 103, 102, 101, 100, 99,
        98, 97, 96, 95, 96, 97, 98, 99, 100, 101,
        102, 103, 104, 105, 104, 103, 102, 101, 100, 99,
        98, 97, 96, 95, 94, 95, 96, 97, 98, 99,
    ]
    n = len(close)
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=n, freq="D", tz="UTC"),
            "open": close,
            "high": [value + 0.5 for value in close],
            "low": [value - 0.5 for value in close],
            "close": close,
            "volume": [1000] * n,
        }
    )
    signals = strategy.calculate_signals(frame)
    actionable = [signal for signal in signals["signal"].tolist() if signal in {"BUY", "SELL"}]
    assert all(actionable[idx] != actionable[idx + 1] for idx in range(len(actionable) - 1))


def test_position_gating() -> None:
    strategy_buy_blocked = BollingerRSI(symbol="SPY")
    strategy_buy_blocked.position_open = True
    frame_down = make_price_series(120, 200, "down")
    result_buy_blocked = strategy_buy_blocked.calculate_signals(frame_down)
    assert "BUY" not in result_buy_blocked["signal"].values

    strategy_sell_blocked = BollingerRSI(symbol="SPY")
    strategy_sell_blocked.position_open = False
    frame_up = make_price_series(120, 50, "up")
    result_sell_blocked = strategy_sell_blocked.calculate_signals(frame_up)
    assert "SELL" not in result_sell_blocked["signal"].values


def test_summarize_runs_without_error() -> None:
    strategy = BollingerRSI(symbol="SPY")
    frame = make_price_series(160, 100, "up")
    signals = strategy.calculate_signals(frame)
    strategy.summarize(signals)
