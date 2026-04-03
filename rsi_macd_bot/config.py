from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class BotConfig:
    watchlist: list[str]
    bar_timeframe: str
    rsi_period: int
    rsi_oversold: float
    rsi_overbought: float
    macd_fast: int
    macd_slow: int
    macd_signal: int
    signal_window: int
    position_size_pct: float
    max_open_trades: int
    risk_per_trade: float
    paper: bool


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


WATCHLIST = ["AAPL", "TSLA", "SPY"]
BAR_TIMEFRAME = "5Min"
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
SIGNAL_WINDOW = 3
POSITION_SIZE_PCT = 0.05
MAX_OPEN_TRADES = 5
RISK_PER_TRADE = 0.02


def get_config() -> BotConfig:
    return BotConfig(
        watchlist=WATCHLIST,
        bar_timeframe=BAR_TIMEFRAME,
        rsi_period=RSI_PERIOD,
        rsi_oversold=RSI_OVERSOLD,
        rsi_overbought=RSI_OVERBOUGHT,
        macd_fast=MACD_FAST,
        macd_slow=MACD_SLOW,
        macd_signal=MACD_SIGNAL,
        signal_window=SIGNAL_WINDOW,
        position_size_pct=POSITION_SIZE_PCT,
        max_open_trades=MAX_OPEN_TRADES,
        risk_per_trade=RISK_PER_TRADE,
        paper=_env_bool("PAPER", True),
    )
