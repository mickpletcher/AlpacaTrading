"""
Filename: backtest_bb_rsi.py
Purpose: Backtest Bollinger Bands plus RSI strategy with Alpaca Market Data and Backtrader.
Author: TODO
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import backtrader as bt

from bb_rsi_strategy import BollingerRSIStrategy, fetch_alpaca_daily_bars

ROOT_DIR = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest Bollinger Bands plus RSI strategy.")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--lookback-days", type=int, default=540)
    parser.add_argument("--cash", type=float, default=25000)
    parser.add_argument("--commission", type=float, default=0.001)
    parser.add_argument("--bb-period", type=int, default=20)
    parser.add_argument("--bb-dev", type=float, default=2.0)
    parser.add_argument("--rsi-period", type=int, default=14)
    parser.add_argument("--rsi-overbought", type=float, default=70)
    parser.add_argument("--rsi-oversold", type=float, default=30)
    return parser.parse_args()


def run_backtest(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    symbol = args.symbol.upper()
    now = datetime.now(timezone.utc).isoformat()
    print(f"{now} | Starting Bollinger plus RSI backtest for {symbol}")

    bars = fetch_alpaca_daily_bars(symbol=symbol, lookback_days=args.lookback_days)
    if bars.empty:
        print("No bars returned. Exiting.")
        return 1

    cerebro = bt.Cerebro()
    data_feed = bt.feeds.PandasData(dataname=bars)
    cerebro.adddata(data_feed)
    cerebro.addstrategy(
        BollingerRSIStrategy,
        bb_period=args.bb_period,
        bb_devfactor=args.bb_dev,
        rsi_period=args.rsi_period,
        rsi_overbought=args.rsi_overbought,
        rsi_oversold=args.rsi_oversold,
        printlog=True,
    )
    cerebro.broker.setcash(args.cash)
    cerebro.broker.setcommission(commission=args.commission)

    print("Backtest configuration")
    print("=" * 50)
    print(f"Symbol:        {symbol}")
    print(f"Bars:          {len(bars)}")
    print(f"Start cash:    ${args.cash:,.2f}")
    print(f"Commission:    {args.commission:.4f}")
    print(f"BB period:     {args.bb_period}")
    print(f"BB devfactor:  {args.bb_dev}")
    print(f"RSI period:    {args.rsi_period}")
    print(f"RSI overbought:{args.rsi_overbought}")
    print(f"RSI oversold:  {args.rsi_oversold}")
    print("=" * 50)

    starting_value = cerebro.broker.getvalue()
    cerebro.run()
    ending_value = cerebro.broker.getvalue()
    pnl = ending_value - starting_value
    pnl_pct = (pnl / starting_value * 100) if starting_value else 0
    runtime = time.perf_counter() - started

    print("\nBacktest result")
    print("=" * 50)
    print(f"Starting equity: ${starting_value:,.2f}")
    print(f"Ending equity:   ${ending_value:,.2f}")
    print(f"Net PnL:         ${pnl:,.2f}")
    print(f"Net PnL %:       {pnl_pct:.2f}%")
    print(f"Runtime:         {runtime:.2f} seconds")
    print("=" * 50)
    return 0


def main() -> int:
    args = parse_args()
    try:
        return run_backtest(args)
    except Exception as exc:
        print(f"Backtest failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
