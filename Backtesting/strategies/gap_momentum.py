"""
Filename: gap_momentum.py
Purpose: Shared Gap Up Momentum strategy logic for intraday backtest and live runners.
Author: TODO
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

ET_TZ = ZoneInfo("America/New_York")

GAP_THRESHOLD = 0.02
MOMENTUM_BARS = 3
STOP_LOSS_PCT = 0.015
TAKE_PROFIT_PCT = 0.04
MAX_HOLD_MINUTES = 390
VOLUME_MULTIPLIER = 1.5
SCAN_START = "09:30"
SCAN_END = "09:45"
EOD_EXIT = "15:45"


@dataclass
class PositionState:
    entry_price: float
    entry_time: pd.Timestamp
    shares_held: int
    stop_loss_price: float
    take_profit_price: float


class GapMomentum:
    def __init__(
        self,
        gap_threshold: float = GAP_THRESHOLD,
        momentum_bars: int = MOMENTUM_BARS,
        stop_loss_pct: float = STOP_LOSS_PCT,
        take_profit_pct: float = TAKE_PROFIT_PCT,
        volume_multiplier: float = VOLUME_MULTIPLIER,
        symbol: str = "SPY",
    ) -> None:
        self.gap_threshold = gap_threshold
        self.momentum_bars = momentum_bars
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.volume_multiplier = volume_multiplier
        self.symbol = symbol
        self.max_hold_minutes = MAX_HOLD_MINUTES
        self.scan_start = self._parse_time(SCAN_START)
        self.scan_end = self._parse_time(SCAN_END)
        self.eod_exit = self._parse_time(EOD_EXIT)

    @staticmethod
    def _parse_time(value: str) -> time:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.time()

    @staticmethod
    def _normalize_intraday_frame(intraday_df: pd.DataFrame) -> pd.DataFrame:
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [column for column in required if column not in intraday_df.columns]
        if missing:
            raise ValueError(f"intraday_df missing required columns: {', '.join(missing)}")

        data = intraday_df.copy()
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
        data = data.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        data["timestamp_et"] = data["timestamp"].dt.tz_convert(ET_TZ)
        return data

    def detect_gap(self, today_open: float, prior_close: float) -> float | None:
        if prior_close <= 0:
            return None
        gap_pct = (today_open - prior_close) / prior_close
        if gap_pct >= self.gap_threshold:
            return gap_pct
        return None

    def confirm_momentum(self, bars_df: pd.DataFrame) -> bool:
        if len(bars_df) < self.momentum_bars:
            return False
        checks = bars_df.iloc[: self.momentum_bars]
        return bool((checks["close"] > checks["open"]).all())

    def confirm_volume(self, first_bar_volume: float, avg_daily_volume: float) -> bool:
        if avg_daily_volume <= 0:
            return False
        expected_per_minute = avg_daily_volume / 390
        required_volume = expected_per_minute * self.volume_multiplier
        return first_bar_volume >= required_volume

    def _within_scan_window(self, ts_et: pd.Timestamp) -> bool:
        bar_time = ts_et.time()
        return self.scan_start <= bar_time <= self.scan_end

    def _is_eod_exit_time(self, ts_et: pd.Timestamp) -> bool:
        return ts_et.time() >= self.eod_exit

    def get_exit_price(self, row: pd.Series, signal: str) -> float:
        if signal == "STOP_LOSS":
            return float(row.get("stop_loss_price", row["close"]))
        if signal == "TAKE_PROFIT":
            return float(row.get("take_profit_price", row["close"]))
        return float(row["close"])

    def calculate_signals(self, intraday_df: pd.DataFrame, prior_close: float, avg_daily_volume: float) -> pd.DataFrame:
        data = self._normalize_intraday_frame(intraday_df)
        if data.empty:
            return data

        data["signal"] = "HOLD"
        data["gap_pct"] = 0.0
        data["volume_ratio"] = 0.0
        data["entry_price"] = 0.0
        data["entry_time"] = pd.NaT
        data["shares_held"] = 0
        data["stop_loss_price"] = 0.0
        data["take_profit_price"] = 0.0
        data["unrealized_pnl"] = 0.0
        data["unrealized_pnl_pct"] = 0.0
        data["hold_minutes"] = 0
        data["exit_reason"] = ""
        data["exit_time"] = None
        data["day_status"] = "no_gap"
        data["scan_log"] = ""
        data["entry_time"] = None

        first_bar = data.iloc[0]
        first_open = float(first_bar["open"])
        first_volume = float(first_bar["volume"])

        gap_pct = (first_open - prior_close) / prior_close if prior_close > 0 else 0.0
        volume_ratio = 0.0
        if avg_daily_volume > 0:
            expected_per_minute = avg_daily_volume / 390
            if expected_per_minute > 0:
                volume_ratio = first_volume / expected_per_minute

        data["gap_pct"] = gap_pct
        data["volume_ratio"] = volume_ratio
        data.at[0, "scan_log"] = (
            f"prior_close={prior_close:.4f} today_open={first_open:.4f} gap_pct={gap_pct:.4%} "
            f"first_volume={first_volume:.0f} volume_ratio={volume_ratio:.2f}"
        )

        detected_gap = self.detect_gap(first_open, prior_close)
        if detected_gap is None:
            data["day_status"] = "no_gap"
            data.at[0, "scan_log"] = str(data.at[0, "scan_log"]) + " | no qualifying gap"
            return data

        data["day_status"] = "gap_qualified"
        momentum_slice = data.iloc[1 : 1 + self.momentum_bars].copy()
        if not self.confirm_momentum(momentum_slice):
            data["day_status"] = "momentum_fail"
            data.at[0, "scan_log"] = str(data.at[0, "scan_log"]) + " | momentum confirmation failed"
            return data

        if not self.confirm_volume(first_volume, avg_daily_volume):
            data["day_status"] = "volume_fail"
            data.at[0, "scan_log"] = str(data.at[0, "scan_log"]) + " | volume confirmation failed"
            return data

        buy_index = self.momentum_bars
        if buy_index >= len(data):
            data["day_status"] = "momentum_fail"
            data.at[0, "scan_log"] = str(data.at[0, "scan_log"]) + " | not enough bars for entry"
            return data

        buy_ts_et = pd.Timestamp(data.at[buy_index, "timestamp_et"])
        if not self._within_scan_window(buy_ts_et):
            data["day_status"] = "outside_scan_window"
            data.at[0, "scan_log"] = str(data.at[0, "scan_log"]) + " | qualifying setup occurred outside scan window"
            return data

        entry_price = float(data.at[buy_index, "close"])
        entry_time = pd.Timestamp(data.at[buy_index, "timestamp"])
        position = PositionState(
            entry_price=entry_price,
            entry_time=entry_time,
            shares_held=1,
            stop_loss_price=entry_price * (1 - self.stop_loss_pct),
            take_profit_price=entry_price * (1 + self.take_profit_pct),
        )

        data["day_status"] = "entry"
        data.at[buy_index, "signal"] = "BUY"
        data.at[buy_index, "entry_price"] = position.entry_price
        data.at[buy_index, "entry_time"] = position.entry_time
        data.at[buy_index, "shares_held"] = position.shares_held
        data.at[buy_index, "stop_loss_price"] = position.stop_loss_price
        data.at[buy_index, "take_profit_price"] = position.take_profit_price

        in_position = True
        for idx in range(buy_index, len(data)):
            ts = pd.Timestamp(data.at[idx, "timestamp"])
            ts_et = pd.Timestamp(data.at[idx, "timestamp_et"])
            close_price = float(data.at[idx, "close"])

            if in_position:
                hold_minutes = int((ts - position.entry_time).total_seconds() // 60)
                unrealized = close_price - position.entry_price
                unrealized_pct = (unrealized / position.entry_price) * 100 if position.entry_price else 0.0
                data.at[idx, "entry_price"] = position.entry_price
                data.at[idx, "entry_time"] = position.entry_time
                data.at[idx, "shares_held"] = position.shares_held
                data.at[idx, "stop_loss_price"] = position.stop_loss_price
                data.at[idx, "take_profit_price"] = position.take_profit_price
                data.at[idx, "hold_minutes"] = hold_minutes
                data.at[idx, "unrealized_pnl"] = unrealized
                data.at[idx, "unrealized_pnl_pct"] = unrealized_pct

                exit_signal = ""
                if close_price <= position.stop_loss_price:
                    exit_signal = "STOP_LOSS"
                elif close_price >= position.take_profit_price:
                    exit_signal = "TAKE_PROFIT"
                elif self._is_eod_exit_time(ts_et) or hold_minutes >= self.max_hold_minutes:
                    exit_signal = "EOD_EXIT"

                if exit_signal:
                    data.at[idx, "signal"] = exit_signal
                    data.at[idx, "exit_reason"] = exit_signal.lower()
                    data.at[idx, "exit_time"] = ts
                    data.at[idx, "unrealized_pnl"] = self.get_exit_price(data.iloc[idx], exit_signal) - position.entry_price
                    data.at[idx, "unrealized_pnl_pct"] = (
                        (data.at[idx, "unrealized_pnl"] / position.entry_price) * 100 if position.entry_price else 0.0
                    )
                    in_position = False
                    break

        if in_position and len(data) > 0:
            last_idx = len(data) - 1
            data.at[last_idx, "signal"] = "EOD_EXIT"
            data.at[last_idx, "exit_reason"] = "eod_exit"
            data.at[last_idx, "exit_time"] = data.at[last_idx, "timestamp"]
            data.at[last_idx, "entry_price"] = position.entry_price
            data.at[last_idx, "entry_time"] = position.entry_time
            data.at[last_idx, "shares_held"] = position.shares_held
            data.at[last_idx, "stop_loss_price"] = position.stop_loss_price
            data.at[last_idx, "take_profit_price"] = position.take_profit_price
            exit_price = self.get_exit_price(data.iloc[last_idx], "EOD_EXIT")
            data.at[last_idx, "unrealized_pnl"] = exit_price - position.entry_price
            data.at[last_idx, "unrealized_pnl_pct"] = (
                (data.at[last_idx, "unrealized_pnl"] / position.entry_price) * 100 if position.entry_price else 0.0
            )

        return data

    def summarize(self, df: pd.DataFrame) -> None:
        if df.empty:
            print("No data to summarize.")
            return

        buy_rows = df[df["signal"] == "BUY"]
        exit_rows = df[df["signal"].isin(["STOP_LOSS", "TAKE_PROFIT", "EOD_EXIT"])]

        print("Gap Momentum Summary")
        print("=" * 60)
        print(f"Symbol: {self.symbol}")
        print(f"Gap %: {df['gap_pct'].iloc[0]:.4%}")

        if buy_rows.empty:
            print("No entry signal on this day.")
            print(f"Day status: {df['day_status'].iloc[0]}")
            print("=" * 60)
            return

        entry_row = buy_rows.iloc[0]
        print(f"Entry time ET: {entry_row['timestamp_et']}")
        print(f"Entry price: {float(entry_row['close']):.4f}")

        if exit_rows.empty:
            print("No exit signal found.")
            print("=" * 60)
            return

        exit_row = exit_rows.iloc[0]
        exit_signal = str(exit_row["signal"])
        exit_price = self.get_exit_price(exit_row, exit_signal)
        entry_price = float(entry_row["close"])
        pnl = exit_price - entry_price
        pnl_pct = (pnl / entry_price) * 100 if entry_price else 0.0
        hold_minutes = int((exit_row["timestamp"] - entry_row["timestamp"]).total_seconds() // 60)

        print(f"Exit time ET: {exit_row['timestamp_et']}")
        print(f"Exit reason: {exit_signal.lower()}")
        print(f"Exit price: {exit_price:.4f}")
        print(f"P&L ($): {pnl:.4f}")
        print(f"P&L (%): {pnl_pct:.4f}%")
        print(f"Hold duration: {hold_minutes} minutes")
        print("=" * 60)
