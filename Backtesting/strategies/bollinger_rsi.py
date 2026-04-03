"""
Filename: bollinger_rsi.py
Purpose: Shared Bollinger Bands plus RSI strategy logic for backtesting and live runs.
Author: TODO
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd


class BollingerRSI:
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14, symbol: str = "SPY") -> None:
        if bb_period <= 1:
            raise ValueError("bb_period must be greater than 1.")
        if bb_std <= 0:
            raise ValueError("bb_std must be greater than zero.")
        if rsi_period <= 1:
            raise ValueError("rsi_period must be greater than 1.")

        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.symbol = symbol
        self.position_open = False
        self.logger = logging.getLogger("bollinger_rsi")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

    @staticmethod
    def _validate_columns(df: pd.DataFrame, expected: Iterable[str]) -> None:
        missing = [column for column in expected if column not in df.columns]
        if missing:
            raise ValueError(f"DataFrame is missing required columns: {', '.join(missing)}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        self._validate_columns(df, required)

        data = df.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
        data = data.sort_values("timestamp").reset_index(drop=True)

        data["bb_middle"] = data["close"].rolling(window=self.bb_period, min_periods=self.bb_period).mean()
        rolling_std = data["close"].rolling(window=self.bb_period, min_periods=self.bb_period).std(ddof=0)
        data["bb_upper"] = data["bb_middle"] + self.bb_std * rolling_std
        data["bb_lower"] = data["bb_middle"] - self.bb_std * rolling_std
        data["bb_bandwidth"] = (data["bb_upper"] - data["bb_lower"]) / data["bb_middle"].replace(0, pd.NA)

        delta = data["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        alpha = 1 / self.rsi_period
        avg_gain = gain.ewm(alpha=alpha, adjust=False, min_periods=self.rsi_period).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False, min_periods=self.rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss > 0, 100.0)
        rsi = rsi.where(avg_gain > 0, 0.0)
        rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
        data["rsi"] = rsi.clip(lower=0, upper=100)
        return data

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = self.calculate_indicators(df)
        data["signal"] = "HOLD"
        data["buy_cross_no_bandwidth"] = False

        in_position = self.position_open
        last_signal = None

        for index in range(1, len(data)):
            previous_close = data.at[index - 1, "close"]
            current_close = data.at[index, "close"]
            previous_lower = data.at[index - 1, "bb_lower"]
            current_lower = data.at[index, "bb_lower"]
            previous_upper = data.at[index - 1, "bb_upper"]
            current_upper = data.at[index, "bb_upper"]
            current_rsi = data.at[index, "rsi"]
            current_bandwidth = data.at[index, "bb_bandwidth"]

            if pd.isna(previous_lower) or pd.isna(current_lower) or pd.isna(previous_upper) or pd.isna(current_upper):
                continue
            if pd.isna(current_rsi) or pd.isna(current_bandwidth):
                continue

            crossed_below_lower = previous_close >= previous_lower and current_close < current_lower
            crossed_above_upper = previous_close <= previous_upper and current_close > current_upper

            buy_without_bandwidth = crossed_below_lower and current_rsi < 35
            if buy_without_bandwidth:
                data.at[index, "buy_cross_no_bandwidth"] = True

            buy_signal = buy_without_bandwidth and current_bandwidth < 0.1
            sell_signal = crossed_above_upper and current_rsi > 65

            signal = "HOLD"
            if buy_signal and not in_position and last_signal != "BUY":
                signal = "BUY"
                in_position = True
                last_signal = "BUY"
            elif sell_signal and in_position and last_signal != "SELL":
                signal = "SELL"
                in_position = False
                last_signal = "SELL"

            data.at[index, "signal"] = signal

            if signal != "HOLD":
                self.logger.info(
                    "%s | %s | %s | close=%.4f | rsi=%.2f | upper=%.4f | lower=%.4f | bandwidth=%.4f",
                    data.at[index, "timestamp"],
                    self.symbol,
                    signal,
                    current_close,
                    current_rsi,
                    current_upper,
                    current_lower,
                    current_bandwidth,
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

        total_entries = int((df["signal"] == "BUY").sum())
        print(f"Total trade entries: {total_entries}")

        entry_rsi = df.loc[df["signal"] == "BUY", "rsi"]
        exit_rsi = df.loc[df["signal"] == "SELL", "rsi"]
        print(f"Average RSI at entry: {entry_rsi.mean():.2f}" if not entry_rsi.empty else "Average RSI at entry: N/A")
        print(f"Average RSI at exit: {exit_rsi.mean():.2f}" if not exit_rsi.empty else "Average RSI at exit: N/A")

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
