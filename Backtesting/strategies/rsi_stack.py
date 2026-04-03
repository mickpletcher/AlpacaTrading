"""
Filename: rsi_stack.py
Purpose: Shared RSI stack multi timeframe strategy logic for backtest and live workflows.
Author: TODO
"""

from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd


class RSIStack:
    def __init__(
        self,
        timeframes: list[str] | None = None,
        rsi_periods: dict[str, int] | None = None,
        oversold: float = 35,
        overbought: float = 65,
        symbol: str = "SPY",
    ) -> None:
        self.timeframes = timeframes or ["1Hour", "1Day"]
        self.rsi_periods = rsi_periods or {tf: 14 for tf in self.timeframes}
        self.oversold = oversold
        self.overbought = overbought
        self.symbol = symbol
        self.position_open = False
        self.logger = logging.getLogger("rsi_stack")
        if not self.logger.handlers:
            logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

        allowed = {"1Min", "5Min", "15Min", "1Hour", "1Day"}
        invalid = [tf for tf in self.timeframes if tf not in allowed]
        if invalid:
            raise ValueError(f"Unsupported timeframe label(s): {', '.join(invalid)}")

    @staticmethod
    def _validate_ohlcv(df: pd.DataFrame) -> None:
        required = ["open", "high", "low", "close", "volume"]
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"Missing required OHLCV columns: {', '.join(missing)}")

    @staticmethod
    def _timeframe_to_pandas_freq(label: str) -> str:
        mapping = {
            "1Min": "1min",
            "5Min": "5min",
            "15Min": "15min",
            "1Hour": "1h",
            "1Day": "1D",
        }
        if label not in mapping:
            raise ValueError(f"Unsupported timeframe label: {label}")
        return mapping[label]

    def calculate_rsi(self, df: pd.DataFrame, period: int) -> pd.Series:
        closes = df["close"].astype(float)
        delta = closes.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)

        alpha = 1 / period
        avg_gain = gains.ewm(alpha=alpha, adjust=False, min_periods=period).mean()
        avg_loss = losses.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.where(avg_loss > 0, 100.0)
        rsi = rsi.where(avg_gain > 0, 0.0)
        rsi = rsi.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)
        return rsi.clip(lower=0, upper=100)

    def align_timeframes(self, bars_by_timeframe: dict[str, pd.DataFrame]) -> pd.DataFrame:
        for tf in self.timeframes:
            if tf not in bars_by_timeframe:
                raise ValueError(f"Missing bars for timeframe {tf} in alignment input")

        primary_tf = self.timeframes[0]
        primary_df = bars_by_timeframe[primary_tf].copy()
        self._validate_ohlcv(primary_df)

        if "timestamp" in primary_df.columns:
            primary_df["timestamp"] = pd.to_datetime(primary_df["timestamp"], utc=True, errors="coerce")
            primary_df = primary_df.set_index("timestamp")
        else:
            primary_df.index = pd.to_datetime(primary_df.index, utc=True, errors="coerce")

        primary_df = primary_df.sort_index()
        if primary_df.empty:
            raise ValueError("Primary timeframe bars are empty. Cannot align timeframes.")

        aligned = primary_df[["open", "high", "low", "close", "volume"]].copy()
        primary_index = aligned.index
        primary_freq = self._timeframe_to_pandas_freq(primary_tf)

        for tf in self.timeframes:
            tf_df = bars_by_timeframe[tf].copy()
            self._validate_ohlcv(tf_df)
            if "timestamp" in tf_df.columns:
                tf_df["timestamp"] = pd.to_datetime(tf_df["timestamp"], utc=True, errors="coerce")
                tf_df = tf_df.set_index("timestamp")
            else:
                tf_df.index = pd.to_datetime(tf_df.index, utc=True, errors="coerce")
            tf_df = tf_df.sort_index()

            period = int(self.rsi_periods.get(tf, 14))
            if len(tf_df) < period + 1:
                raise ValueError(
                    f"Alignment failed for {tf}: only {len(tf_df)} bars available, minimum {period + 1} required"
                )

            rsi_series = self.calculate_rsi(tf_df, period)
            tf_freq = self._timeframe_to_pandas_freq(tf)
            resampled = rsi_series.resample(tf_freq).last().resample(primary_freq).ffill()
            aligned[f"rsi_{tf}"] = resampled.reindex(primary_index, method="ffill")

        warmup = max(int(self.rsi_periods[tf]) for tf in self.timeframes)
        post_warmup = aligned.iloc[warmup:]
        rsi_columns = [f"rsi_{tf}" for tf in self.timeframes]
        if post_warmup[rsi_columns].isna().any().any():
            raise ValueError(
                "Alignment failed due to mismatched bar counts across timeframes. "
                "RSI columns still contain NaN values after warmup."
            )

        return aligned.reset_index().rename(columns={"index": "timestamp"})

    def calculate_signals(self, aligned_df: pd.DataFrame) -> pd.DataFrame:
        data = aligned_df.copy()
        data["signal"] = "HOLD"
        data["blocked_buy_unconfirmed"] = False

        rsi_columns = [f"rsi_{tf}" for tf in self.timeframes]
        for column in rsi_columns:
            if column not in data.columns:
                raise ValueError(f"Missing {column} in aligned data. Run align_timeframes first.")

        in_position = self.position_open
        prev_full_buy = False
        prev_full_sell = False
        last_signal = None

        for index in range(len(data)):
            rsi_values = {tf: float(data.at[index, f"rsi_{tf}"]) for tf in self.timeframes}
            oversold_count = sum(1 for tf in self.timeframes if rsi_values[tf] < self.oversold)
            overbought_count = sum(1 for tf in self.timeframes if rsi_values[tf] > self.overbought)
            stack_score = max(oversold_count, overbought_count)

            data.at[index, "rsi_stack_score"] = stack_score
            data.at[index, "rsi_stack_buy_score"] = oversold_count
            data.at[index, "rsi_stack_sell_score"] = overbought_count

            full_buy = oversold_count == len(self.timeframes)
            full_sell = overbought_count == len(self.timeframes)

            primary_tf = self.timeframes[0]
            if rsi_values[primary_tf] < self.oversold and not full_buy:
                data.at[index, "blocked_buy_unconfirmed"] = True

            signal = "HOLD"
            if full_buy and not prev_full_buy and not in_position and last_signal != "BUY":
                signal = "BUY"
                in_position = True
                last_signal = "BUY"
            elif full_sell and not prev_full_sell and in_position and last_signal != "SELL":
                signal = "SELL"
                in_position = False
                last_signal = "SELL"

            data.at[index, "signal"] = signal

            if signal != "HOLD":
                details = " ".join(f"{tf}={rsi_values[tf]:.2f}" for tf in self.timeframes)
                self.logger.info(
                    "%s | %s | %s | close=%.4f | score=%d | %s",
                    data.at[index, "timestamp"],
                    self.symbol,
                    signal,
                    float(data.at[index, "close"]),
                    stack_score,
                    details,
                )

            prev_full_buy = full_buy
            prev_full_sell = full_sell

        self.position_open = in_position
        return data

    def get_latest_signal(self, aligned_df: pd.DataFrame) -> str:
        if "signal" not in aligned_df.columns:
            raise ValueError("Missing signal column. Run calculate_signals first.")
        if aligned_df.empty:
            return "HOLD"
        return str(aligned_df.iloc[-1]["signal"])

    def get_stack_snapshot(self, aligned_df: pd.DataFrame) -> dict[str, float | int | str]:
        if aligned_df.empty:
            return {"signal": "HOLD", "rsi_stack_score": 0}
        row = aligned_df.iloc[-1]
        snapshot: dict[str, float | int | str] = {
            "signal": str(row.get("signal", "HOLD")),
            "rsi_stack_score": int(row.get("rsi_stack_score", 0)),
        }
        for tf in self.timeframes:
            snapshot[f"rsi_{tf}"] = float(row[f"rsi_{tf}"])
        return snapshot

    def summarize(self, aligned_df: pd.DataFrame) -> None:
        if "signal" not in aligned_df.columns:
            raise ValueError("Missing signal column. Run calculate_signals first.")

        total_buy = int((aligned_df["signal"] == "BUY").sum())
        total_sell = int((aligned_df["signal"] == "SELL").sum())
        print(f"Total BUY signals: {total_buy}")
        print(f"Total SELL signals: {total_sell}")

        entry_scores = aligned_df.loc[aligned_df["signal"] == "BUY", "rsi_stack_score"]
        exit_scores = aligned_df.loc[aligned_df["signal"] == "SELL", "rsi_stack_score"]
        print(
            f"Average stack score at entry: {entry_scores.mean():.2f}"
            if not entry_scores.empty
            else "Average stack score at entry: N/A"
        )
        print(
            f"Average stack score at exit: {exit_scores.mean():.2f}"
            if not exit_scores.empty
            else "Average stack score at exit: N/A"
        )

        if "entry_price" in aligned_df.columns and "exit_price" in aligned_df.columns:
            completed = aligned_df[(aligned_df["entry_price"] > 0) & (aligned_df["exit_price"] > 0)].copy()
            if completed.empty:
                print("No completed trades found for win/loss summary.")
                return
            completed["pnl"] = completed["exit_price"] - completed["entry_price"]
            wins = int((completed["pnl"] > 0).sum())
            losses = int((completed["pnl"] <= 0).sum())
            print(f"Completed trades: {len(completed)}")
            print(f"Wins: {wins}")
            print(f"Losses: {losses}")
