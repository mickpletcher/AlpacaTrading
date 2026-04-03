"""
Filename: ema_crossover.py
Purpose: Shared EMA crossover strategy logic for backtesting and live trading.
Author: TODO
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd


class EMAcrossover:
    def __init__(self, fast_period: int = 9, slow_period: int = 21, symbol: str = "SPY") -> None:
        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("EMA periods must be greater than zero.")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be smaller than slow_period.")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.symbol = symbol
        self.position_open = False
        self.logger = logging.getLogger("ema_crossover")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

    @staticmethod
    def _validate_columns(df: pd.DataFrame, expected: Iterable[str]) -> None:
        missing = [column for column in expected if column not in df.columns]
        if missing:
            raise ValueError(f"DataFrame is missing required columns: {', '.join(missing)}")

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        self._validate_columns(df, required)

        data = df.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
        data = data.sort_values("timestamp").reset_index(drop=True)
        data["fast_ema"] = data["close"].ewm(span=self.fast_period, adjust=False).mean()
        data["slow_ema"] = data["close"].ewm(span=self.slow_period, adjust=False).mean()
        data["signal"] = "HOLD"

        in_position = self.position_open
        last_signal = None

        for index in range(1, len(data)):
            previous_fast = data.at[index - 1, "fast_ema"]
            previous_slow = data.at[index - 1, "slow_ema"]
            current_fast = data.at[index, "fast_ema"]
            current_slow = data.at[index, "slow_ema"]

            if pd.isna(previous_fast) or pd.isna(previous_slow) or pd.isna(current_fast) or pd.isna(current_slow):
                continue

            buy_cross = previous_fast < previous_slow and current_fast > current_slow
            sell_cross = previous_fast > previous_slow and current_fast < current_slow
            signal = "HOLD"

            if buy_cross and not in_position and last_signal != "BUY":
                signal = "BUY"
                in_position = True
                last_signal = "BUY"
            elif sell_cross and in_position and last_signal != "SELL":
                signal = "SELL"
                in_position = False
                last_signal = "SELL"

            data.at[index, "signal"] = signal

            if signal != "HOLD":
                self.logger.info(
                    "%s | %s | %s | fast=%.4f | slow=%.4f | close=%.4f",
                    data.at[index, "timestamp"],
                    self.symbol,
                    signal,
                    current_fast,
                    current_slow,
                    data.at[index, "close"],
                )

        self.position_open = in_position
        return data

    def get_latest_signal(self, df: pd.DataFrame) -> str:
        if "signal" not in df.columns:
            raise ValueError("DataFrame must include a signal column. Call calculate_signals first.")
        if df.empty:
            return "HOLD"
        return str(df.iloc[-1]["signal"])

    def summarize(self, df: pd.DataFrame) -> None:
        if "signal" not in df.columns:
            raise ValueError("DataFrame must include a signal column. Call calculate_signals first.")

        trades = int((df["signal"] == "BUY").sum())
        print(f"Total trade entries: {trades}")

        if "entry_price" in df.columns and "exit_price" in df.columns:
            completed = df[(df["entry_price"] > 0) & (df["exit_price"] > 0)].copy()
            if completed.empty:
                print("No completed trades found for win/loss summary.")
                return

            completed["pnl"] = completed["exit_price"] - completed["entry_price"]
            wins = int((completed["pnl"] > 0).sum())
            losses = int((completed["pnl"] <= 0).sum())
            print(f"Completed trades: {len(completed)}")
            print(f"Wins: {wins}")
            print(f"Losses: {losses}")
        else:
            print("No entry/exit columns provided for win/loss summary.")
