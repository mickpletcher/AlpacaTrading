"""
Filename: test_ema_crossover.py
Purpose: Validate EMA crossover signal behavior using synthetic data only.
Author: TODO

Run with:
pytest Tests/test_ema_crossover.py -v
"""

from __future__ import annotations

import pandas as pd

from Backtesting.strategies.ema_crossover import EMAcrossover


def make_price_frame(close_values: list[float]) -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-01", periods=len(close_values), freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close_values,
            "high": [value + 0.5 for value in close_values],
            "low": [value - 0.5 for value in close_values],
            "close": close_values,
            "volume": [1_000] * len(close_values),
        }
    )


def test_no_signal_on_flat_data() -> None:
    strategy = EMAcrossover(symbol="SPY")
    df = make_price_frame([100.0] * 80)
    signaled = strategy.calculate_signals(df)
    assert not ((signaled["signal"] == "BUY") | (signaled["signal"] == "SELL")).any()


def test_buy_signal_on_crossover() -> None:
    strategy = EMAcrossover(symbol="SPY")
    prices = [100.0] * 30 + [99, 98, 97, 96, 95, 96, 97, 99, 102, 106, 110, 113]
    signaled = strategy.calculate_signals(make_price_frame(prices))
    buy_rows = signaled[signaled["signal"] == "BUY"]
    assert not buy_rows.empty


def test_sell_signal_on_crossover() -> None:
    strategy = EMAcrossover(symbol="SPY")
    strategy.position_open = True
    prices = [100.0] * 30 + [101, 102, 103, 104, 105, 104, 103, 101, 98, 95, 92, 90]
    signaled = strategy.calculate_signals(make_price_frame(prices))
    sell_rows = signaled[signaled["signal"] == "SELL"]
    assert not sell_rows.empty


def test_no_double_signals() -> None:
    strategy = EMAcrossover(symbol="SPY")
    prices = [100.0] * 20 + [95, 94, 95, 97, 100, 103, 101, 98, 95, 92, 95, 99, 104, 100, 96, 91]
    signaled = strategy.calculate_signals(make_price_frame(prices))
    actionable = [signal for signal in signaled["signal"].tolist() if signal in {"BUY", "SELL"}]
    assert all(actionable[index] != actionable[index + 1] for index in range(len(actionable) - 1))


def test_position_gating() -> None:
    bullish_prices = [100.0] * 30 + [99, 98, 97, 96, 95, 96, 97, 99, 102, 106, 110, 113]
    bearish_prices = [100.0] * 30 + [101, 102, 103, 104, 105, 104, 103, 101, 98, 95, 92, 90]

    buy_blocked = EMAcrossover(symbol="SPY")
    buy_blocked.position_open = True
    buy_output = buy_blocked.calculate_signals(make_price_frame(bullish_prices))
    assert "BUY" not in buy_output["signal"].values

    sell_blocked = EMAcrossover(symbol="SPY")
    sell_blocked.position_open = False
    sell_output = sell_blocked.calculate_signals(make_price_frame(bearish_prices))
    assert "SELL" not in sell_output["signal"].values


def test_summarize_runs_without_error() -> None:
    strategy = EMAcrossover(symbol="SPY")
    prices = [100.0] * 30 + [99, 98, 97, 96, 95, 96, 97, 99, 102, 106, 110, 113, 108, 104, 99, 95]
    signaled = strategy.calculate_signals(make_price_frame(prices))
    strategy.summarize(signaled)
