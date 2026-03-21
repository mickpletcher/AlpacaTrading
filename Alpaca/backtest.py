"""
=============================================================
  Day Trading Backtester
  Strategies: VWAP Reversion, EMA Crossover, Opening Range Breakout
  Data: yfinance (free, no API key needed)
  Usage: python backtest.py
=============================================================
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import yfinance as yf
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURATION  — edit these values
# ─────────────────────────────────────────────
TICKER      = "SPY"          # Stock/ETF to test
PERIOD      = "6mo"          # Data period: 1mo, 3mo, 6mo, 1y, 2y
INTERVAL    = "1h"           # Bar size: 1m, 5m, 15m, 30m, 1h, 1d
CASH        = 25_000         # Starting capital ($25k PDT minimum)
COMMISSION  = 0.001          # 0.1% per trade (realistic for retail)
# ─────────────────────────────────────────────


def get_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance."""
    print(f"\n📥 Downloading {ticker} | {interval} bars | {period} period...")
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.DatetimeIndex(df.index)
    print(f"   ✅ {len(df)} bars loaded  ({df.index[0].date()} → {df.index[-1].date()})")
    return df


# ─────────────────────────────────────────────
# STRATEGY 1 — EMA Crossover
#   Buy when fast EMA crosses above slow EMA
#   Sell when fast EMA crosses below slow EMA
# ─────────────────────────────────────────────
class EMACrossover(Strategy):
    fast = 9
    slow = 21

    def init(self):
        close = self.data.Close
        self.fast_ema = self.I(lambda x: pd.Series(x).ewm(span=self.fast).mean(), close)
        self.slow_ema = self.I(lambda x: pd.Series(x).ewm(span=self.slow).mean(), close)

    def next(self):
        if crossover(self.fast_ema, self.slow_ema):
            self.buy()
        elif crossover(self.slow_ema, self.fast_ema):
            self.sell()


# ─────────────────────────────────────────────
# STRATEGY 2 — RSI Mean Reversion
#   Buy oversold (RSI < 30), sell overbought (RSI > 70)
#   Classic retail strategy — good to understand its limits
# ─────────────────────────────────────────────
class RSIMeanReversion(Strategy):
    rsi_period = 14
    oversold   = 30
    overbought = 70

    def init(self):
        close = self.data.Close

        def calc_rsi(prices, period):
            prices = pd.Series(prices)
            delta  = prices.diff()
            gain   = delta.clip(lower=0).rolling(period).mean()
            loss   = (-delta.clip(upper=0)).rolling(period).mean()
            rs     = gain / loss.replace(0, np.nan)
            return (100 - 100 / (1 + rs)).fillna(50)

        self.rsi = self.I(calc_rsi, close, self.rsi_period)

    def next(self):
        if self.rsi[-1] < self.oversold and not self.position:
            self.buy()
        elif self.rsi[-1] > self.overbought and self.position:
            self.position.close()


# ─────────────────────────────────────────────
# STRATEGY 3 — EMA + RSI Combined (Filtered)
#   Trend confirmation (EMA) + momentum filter (RSI)
#   Reduces false signals — a common improvement
# ─────────────────────────────────────────────
class EMAWithRSIFilter(Strategy):
    fast       = 9
    slow       = 21
    rsi_period = 14
    rsi_min    = 40   # Only buy if RSI > 40 (not in downtrend)
    rsi_max    = 65   # Don't buy into overbought

    def init(self):
        close = self.data.Close
        self.fast_ema = self.I(lambda x: pd.Series(x).ewm(span=self.fast).mean(), close)
        self.slow_ema = self.I(lambda x: pd.Series(x).ewm(span=self.slow).mean(), close)

        def calc_rsi(prices, period):
            prices = pd.Series(prices)
            delta  = prices.diff()
            gain   = delta.clip(lower=0).rolling(period).mean()
            loss   = (-delta.clip(upper=0)).rolling(period).mean()
            rs     = gain / loss.replace(0, np.nan)
            return (100 - 100 / (1 + rs)).fillna(50)

        self.rsi = self.I(calc_rsi, close, self.rsi_period)

    def next(self):
        bullish_cross = crossover(self.fast_ema, self.slow_ema)
        bearish_cross = crossover(self.slow_ema, self.fast_ema)
        rsi_ok        = self.rsi_min < self.rsi[-1] < self.rsi_max

        if bullish_cross and rsi_ok and not self.position:
            self.buy()
        elif bearish_cross and self.position:
            self.position.close()


# ─────────────────────────────────────────────
# RUN ALL STRATEGIES AND COMPARE
# ─────────────────────────────────────────────
def run_all(ticker=TICKER, period=PERIOD, interval=INTERVAL, cash=CASH):
    data = get_data(ticker, period, interval)

    strategies = [
        ("EMA Crossover (9/21)",       EMACrossover),
        ("RSI Mean Reversion",         RSIMeanReversion),
        ("EMA + RSI Filter",           EMAWithRSIFilter),
    ]

    results = {}

    for name, strat in strategies:
        print(f"\n🔬 Running: {name}")
        bt = Backtest(data, strat, cash=cash, commission=COMMISSION, exclusive_orders=True)
        stats = bt.run()
        results[name] = stats

        print(f"   Return:        {stats['Return [%]']:>8.2f}%")
        print(f"   Buy & Hold:    {stats['Buy & Hold Return [%]']:>8.2f}%")
        print(f"   Sharpe Ratio:  {stats['Sharpe Ratio']:>8.2f}")
        print(f"   Max Drawdown:  {stats['Max. Drawdown [%]']:>8.2f}%")
        print(f"   Win Rate:      {stats['Win Rate [%]']:>8.2f}%")
        print(f"   # Trades:      {stats['# Trades']:>8}")

    # Summary table
    print("\n" + "="*60)
    print(f"  SUMMARY — {ticker} | {interval} bars | {period}")
    print("="*60)
    print(f"{'Strategy':<30} {'Return':>8} {'Sharpe':>8} {'Win%':>7} {'Trades':>7}")
    print("-"*60)
    for name, stats in results.items():
        print(f"{name:<30} {stats['Return [%]']:>7.1f}% {stats['Sharpe Ratio']:>8.2f} "
              f"{stats['Win Rate [%]']:>6.1f}% {stats['# Trades']:>7}")
    print("="*60)

    # Save best strategy chart
    best_name = max(results, key=lambda k: results[k]["Sharpe Ratio"])
    print(f"\n🏆 Best Sharpe Ratio: {best_name}")
    print("   Saving chart → backtest_results.html")

    bt_best = Backtest(data, dict(strategies)[best_name], cash=cash,
                       commission=COMMISSION, exclusive_orders=True)
    bt_best.run()
    bt_best.plot(filename="backtest_results.html", open_browser=False)

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("  DAY TRADING BACKTESTER")
    print("=" * 60)
    results = run_all()
    print("\n✅ Done. Open backtest_results.html to view the best strategy chart.")
    print("\nTIP: Edit TICKER, PERIOD, INTERVAL at the top of this file to test")
    print("     different stocks or timeframes. Try TSLA, QQQ, AAPL, or ES=F.\n")
