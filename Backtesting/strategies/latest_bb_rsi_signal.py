"""
Filename: latest_bb_rsi_signal.py
Purpose: Evaluate the latest Bollinger Bands plus RSI signal from Alpaca Market Data.
Author: TODO
"""

from __future__ import annotations

import argparse

import pandas as pd

from bb_rsi_strategy import fetch_alpaca_daily_bars


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Get latest Bollinger plus RSI signal from Alpaca bars.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--lookback-days", type=int, default=180)
    parser.add_argument("--bb-period", type=int, default=20)
    parser.add_argument("--bb-dev", type=float, default=2.0)
    parser.add_argument("--rsi-period", type=int, default=14)
    parser.add_argument("--rsi-overbought", type=float, default=70)
    parser.add_argument("--rsi-oversold", type=float, default=30)
    return parser.parse_args()


def calculate_rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def latest_signal(args: argparse.Namespace) -> int:
    bars = fetch_alpaca_daily_bars(symbol=args.symbol, lookback_days=args.lookback_days)
    if len(bars) < max(args.bb_period, args.rsi_period) + 2:
        print("Not enough bars to evaluate signal.")
        return 1

    data = bars.copy()
    data["mid"] = data["close"].rolling(args.bb_period).mean()
    data["std"] = data["close"].rolling(args.bb_period).std()
    data["upper"] = data["mid"] + args.bb_dev * data["std"]
    data["lower"] = data["mid"] - args.bb_dev * data["std"]
    data["rsi"] = calculate_rsi(data["close"], args.rsi_period)

    previous = data.iloc[-2]
    current = data.iloc[-1]

    crossed_above_upper = previous["close"] <= previous["upper"] and current["close"] > current["upper"]
    crossed_below_lower = previous["close"] >= previous["lower"] and current["close"] < current["lower"]

    signal = "HOLD"
    if crossed_above_upper and current["rsi"] > args.rsi_overbought:
        signal = "SELL"
    elif crossed_below_lower and current["rsi"] < args.rsi_oversold:
        signal = "BUY"

    print("Latest Bollinger plus RSI signal")
    print("=" * 50)
    print(f"Symbol:      {args.symbol.upper()}")
    print(f"Timestamp:   {current.name}")
    print(f"Close:       {current['close']:.2f}")
    print(f"Upper band:  {current['upper']:.2f}")
    print(f"Lower band:  {current['lower']:.2f}")
    print(f"RSI:         {current['rsi']:.2f}")
    print(f"Signal:      {signal}")
    print("=" * 50)
    return 0


def main() -> int:
    args = parse_args()
    try:
        return latest_signal(args)
    except Exception as exc:
        print(f"Signal check failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
