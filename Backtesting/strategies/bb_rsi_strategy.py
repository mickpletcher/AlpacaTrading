"""
Filename: bb_rsi_strategy.py
Purpose: Backtrader strategy and Alpaca data helpers for a Bollinger Bands plus RSI combo.
Author: TODO
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import backtrader as bt
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]


def get_data_client() -> StockHistoricalDataClient:
    load_dotenv(ROOT_DIR / ".env")
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise RuntimeError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")
    return StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)


def fetch_alpaca_daily_bars(symbol: str, lookback_days: int = 365) -> pd.DataFrame:
    client = get_data_client()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    request = StockBarsRequest(
        symbol_or_symbols=symbol.upper(),
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    response = client.get_stock_bars(request)
    bars = response.df
    if bars.empty:
        raise RuntimeError("No Alpaca bars returned for Bollinger plus RSI strategy.")

    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.reset_index()
        bars = bars[bars["symbol"] == symbol.upper()]
    else:
        bars = bars.reset_index()

    bars = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").reset_index(drop=True)
    bars = bars.set_index("timestamp")
    return bars


class BollingerRSIStrategy(bt.Strategy):
    params = (
        ("bb_period", 20),
        ("bb_devfactor", 2.0),
        ("rsi_period", 14),
        ("rsi_overbought", 70),
        ("rsi_oversold", 30),
        ("printlog", True),
    )

    def __init__(self) -> None:
        self.close = self.datas[0].close
        self.bbands = bt.indicators.BollingerBands(
            self.datas[0],
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor,
        )
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.params.rsi_period)
        self.cross_upper = bt.indicators.CrossOver(self.close, self.bbands.top)
        self.cross_lower = bt.indicators.CrossOver(self.close, self.bbands.bot)
        self.order = None

    def log(self, message: str) -> None:
        if self.params.printlog:
            dt = self.datas[0].datetime.datetime(0)
            print(f"{dt.isoformat()} | {message}")

    def next(self) -> None:
        if self.order:
            return

        overbought_cross = self.cross_upper[0] > 0 and self.rsi[0] > self.params.rsi_overbought
        oversold_cross = self.cross_lower[0] < 0 and self.rsi[0] < self.params.rsi_oversold

        if not self.position and oversold_cross:
            self.log(
                f"BUY signal | close={self.close[0]:.2f} | lower={self.bbands.bot[0]:.2f} | rsi={self.rsi[0]:.2f}"
            )
            self.order = self.buy(size=1)
        elif self.position and overbought_cross:
            self.log(
                f"SELL signal | close={self.close[0]:.2f} | upper={self.bbands.top[0]:.2f} | rsi={self.rsi[0]:.2f}"
            )
            self.order = self.sell(size=1)

    def notify_order(self, order) -> None:
        if order.status in [order.Completed]:
            side = "BUY" if order.isbuy() else "SELL"
            self.log(f"{side} filled at {order.executed.price:.2f}")
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order cancelled or rejected")

        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None

    def stop(self) -> None:
        self.log(
            "Stop summary | bb_period=%s bb_dev=%.2f rsi_period=%s"
            % (self.params.bb_period, self.params.bb_devfactor, self.params.rsi_period)
        )
