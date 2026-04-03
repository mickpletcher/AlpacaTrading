from __future__ import annotations

import pandas as pd
import pandas_ta as ta

from config import RSI_OVERBOUGHT, RSI_OVERSOLD, SIGNAL_WINDOW


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["rsi"] = ta.rsi(out["close"], length=period)
    return out


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    out = df.copy()
    macd = ta.macd(out["close"], fast=fast, slow=slow, signal=signal)
    if macd is None or macd.empty:
        out["macd"] = pd.NA
        out["macd_signal"] = pd.NA
        out["macd_hist"] = pd.NA
        return out

    out["macd"] = macd.iloc[:, 0]
    out["macd_hist"] = macd.iloc[:, 1]
    out["macd_signal"] = macd.iloc[:, 2]
    return out


def _find_recent_index(mask: pd.Series, window: int) -> int | None:
    indexes = mask[mask].index.tolist()
    if not indexes:
        return None
    last_index = indexes[-1]
    return int(last_index) if int(mask.index[-1]) - int(last_index) <= window else None


def get_signal(
    df: pd.DataFrame,
    window: int = SIGNAL_WINDOW,
    rsi_oversold: float = RSI_OVERSOLD,
    rsi_overbought: float = RSI_OVERBOUGHT,
) -> str | None:
    if len(df) < 3:
        return None

    calc = df.copy().reset_index(drop=True)
    calc["rsi_cross_under"] = (calc["rsi"].shift(1) >= rsi_oversold) & (calc["rsi"] < rsi_oversold)
    calc["rsi_cross_over"] = (calc["rsi"].shift(1) <= rsi_overbought) & (calc["rsi"] > rsi_overbought)
    calc["macd_hist_pos_turn"] = (calc["macd_hist"].shift(1) <= 0) & (calc["macd_hist"] > 0)
    calc["macd_hist_neg_turn"] = (calc["macd_hist"].shift(1) >= 0) & (calc["macd_hist"] < 0)

    last = int(calc.index[-1])
    recent_rsi_buy = _find_recent_index(calc["rsi_cross_under"], window)
    recent_macd_buy = _find_recent_index(calc["macd_hist_pos_turn"], window)
    if recent_rsi_buy is not None and recent_macd_buy is not None:
        if abs(recent_rsi_buy - recent_macd_buy) <= window and max(recent_rsi_buy, recent_macd_buy) <= last:
            return "BUY"

    recent_rsi_sell = _find_recent_index(calc["rsi_cross_over"], window)
    recent_macd_sell = _find_recent_index(calc["macd_hist_neg_turn"], window)
    if recent_rsi_sell is not None and recent_macd_sell is not None:
        if abs(recent_rsi_sell - recent_macd_sell) <= window and max(recent_rsi_sell, recent_macd_sell) <= last:
            return "SELL"

    return None
