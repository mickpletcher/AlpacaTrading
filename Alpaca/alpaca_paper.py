"""
=============================================================
  Alpaca Paper Trading Environment
  Paper trading = real market data, fake money. No risk.

  SETUP:
  1. Create a FREE account at https://alpaca.markets
  2. Go to Paper Trading section → generate API keys
  3. Add your keys to config.py (never hardcode them here)
  4. pip install alpaca-trade-api pandas --break-system-packages

  Usage:
    python alpaca_paper.py status          # Account info
    python alpaca_paper.py quote AAPL      # Get a quote
    python alpaca_paper.py buy AAPL 1      # Buy 1 share
    python alpaca_paper.py sell AAPL 1     # Sell 1 share
    python alpaca_paper.py positions       # View open positions
    python alpaca_paper.py orders          # View open orders
    python alpaca_paper.py bot             # Run EMA crossover bot (paper)
=============================================================
"""

import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION — fill in your Alpaca paper keys
# Get them free at https://alpaca.markets (Paper Trading section)
# ─────────────────────────────────────────────
ALPACA_API_KEY    = "YOUR_PAPER_API_KEY"      # Replace this
ALPACA_SECRET_KEY = "YOUR_PAPER_SECRET_KEY"   # Replace this
BASE_URL          = "https://paper-api.alpaca.markets"  # Paper trading URL — NOT real money
# ─────────────────────────────────────────────

# Bot settings
BOT_TICKER    = "SPY"
BOT_INTERVAL  = 60       # seconds between checks
BOT_QTY       = 1        # shares per trade
EMA_FAST      = 9
EMA_SLOW      = 21
PRICE_HISTORY = []       # in-memory price buffer


def get_client():
    """Return Alpaca REST client. Fails clearly if keys not set."""
    try:
        import alpaca_trade_api as tradeapi
    except ImportError:
        print("❌ Run: pip install alpaca-trade-api --break-system-packages")
        sys.exit(1)

    if "YOUR_PAPER" in ALPACA_API_KEY:
        print("⚠️  API keys not configured.")
        print("   1. Sign up at https://alpaca.markets (free)")
        print("   2. Go to Paper Trading → generate API keys")
        print(f"   3. Edit this file and replace ALPACA_API_KEY and ALPACA_SECRET_KEY")
        sys.exit(1)

    return tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL, api_version="v2")


def cmd_status(api):
    """Print account summary."""
    acct = api.get_account()
    print("\n📊 PAPER ACCOUNT STATUS")
    print("=" * 40)
    print(f"  Status:          {acct.status}")
    print(f"  Portfolio Value: ${float(acct.portfolio_value):>12,.2f}")
    print(f"  Cash:            ${float(acct.cash):>12,.2f}")
    print(f"  Buying Power:    ${float(acct.buying_power):>12,.2f}")
    print(f"  Day Trades Used: {acct.daytrade_count} / 3 (PDT rule)")
    print(f"  Equity:          ${float(acct.equity):>12,.2f}")
    pnl = float(acct.equity) - float(acct.last_equity)
    emoji = "📈" if pnl >= 0 else "📉"
    print(f"  Today's P&L:     {emoji} ${pnl:>+,.2f}")
    print("=" * 40)


def cmd_quote(api, ticker: str):
    """Get latest quote for a ticker."""
    try:
        quote = api.get_latest_quote(ticker)
        trade = api.get_latest_trade(ticker)
        print(f"\n📌 {ticker}")
        print(f"   Bid:   ${float(quote.bp):>10.2f}  (x{quote.bs})")
        print(f"   Ask:   ${float(quote.ap):>10.2f}  (x{quote.as_})")
        print(f"   Last:  ${float(trade.p):>10.2f}  @ {trade.t}")
        spread = float(quote.ap) - float(quote.bp)
        print(f"   Spread: ${spread:.4f}  ({spread/float(trade.p)*100:.3f}%)")
    except Exception as e:
        print(f"❌ Quote error: {e}")


def cmd_buy(api, ticker: str, qty: int):
    """Submit a market buy order."""
    print(f"\n🛒 Buying {qty} share(s) of {ticker} at market...")
    try:
        order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="day"
        )
        print(f"   ✅ Order submitted: {order.id}")
        print(f"   Status: {order.status}")
    except Exception as e:
        print(f"   ❌ Order failed: {e}")


def cmd_sell(api, ticker: str, qty: int):
    """Submit a market sell order."""
    print(f"\n💰 Selling {qty} share(s) of {ticker} at market...")
    try:
        order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side="sell",
            type="market",
            time_in_force="day"
        )
        print(f"   ✅ Order submitted: {order.id}")
        print(f"   Status: {order.status}")
    except Exception as e:
        print(f"   ❌ Order failed: {e}")


def cmd_positions(api):
    """Show all open positions."""
    positions = api.list_positions()
    if not positions:
        print("\n📭 No open positions.")
        return
    print(f"\n📂 OPEN POSITIONS ({len(positions)})")
    print("=" * 55)
    print(f"  {'Symbol':<8} {'Qty':>5} {'Entry':>10} {'Current':>10} {'P&L':>10}")
    print("-" * 55)
    for p in positions:
        pnl = float(p.unrealized_pl)
        emoji = "▲" if pnl >= 0 else "▼"
        print(f"  {p.symbol:<8} {p.qty:>5} ${float(p.avg_entry_price):>9.2f} "
              f"${float(p.current_price):>9.2f} {emoji}${pnl:>+9.2f}")
    print("=" * 55)


def cmd_orders(api):
    """Show open orders."""
    orders = api.list_orders(status="open")
    if not orders:
        print("\n📭 No open orders.")
        return
    print(f"\n📋 OPEN ORDERS ({len(orders)})")
    print("=" * 55)
    for o in orders:
        print(f"  {o.symbol} | {o.side.upper()} {o.qty} | {o.type} | {o.status}")
    print("=" * 55)


def ema(prices: list, period: int) -> float:
    """Calculate EMA from a list of prices."""
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema_val = sum(prices[:period]) / period
    for price in prices[period:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val


def is_market_open(api) -> bool:
    clock = api.get_clock()
    return clock.is_open


def run_bot(api):
    """
    Simple EMA crossover paper trading bot.
    Runs in a loop, checks price every BOT_INTERVAL seconds.
    Only trades during market hours.
    """
    print(f"\n🤖 EMA CROSSOVER BOT — {BOT_TICKER}")
    print(f"   Fast EMA: {EMA_FAST} | Slow EMA: {EMA_SLOW}")
    print(f"   Qty per trade: {BOT_QTY} share(s)")
    print(f"   Check interval: {BOT_INTERVAL}s")
    print("   Press Ctrl+C to stop.\n")

    in_position = False

    # Check if we already have a position
    try:
        pos = api.get_position(BOT_TICKER)
        in_position = True
        print(f"   📂 Existing position found: {pos.qty} shares")
    except:
        pass

    while True:
        try:
            if not is_market_open(api):
                print(f"   ⏰ Market closed. Waiting... ({datetime.now().strftime('%H:%M:%S')})")
                time.sleep(60)
                continue

            # Get latest price
            trade = api.get_latest_trade(BOT_TICKER)
            price = float(trade.p)
            PRICE_HISTORY.append(price)

            # Keep buffer manageable
            if len(PRICE_HISTORY) > 100:
                PRICE_HISTORY.pop(0)

            fast = ema(PRICE_HISTORY, EMA_FAST)
            slow = ema(PRICE_HISTORY, EMA_SLOW)

            ts = datetime.now().strftime("%H:%M:%S")

            if fast is None or slow is None:
                bars_needed = max(EMA_FAST, EMA_SLOW)
                print(f"   [{ts}] ${price:.2f} | Collecting data... ({len(PRICE_HISTORY)}/{bars_needed})")
            else:
                signal = "▲ BULL" if fast > slow else "▼ BEAR"
                print(f"   [{ts}] ${price:.2f} | EMA9={fast:.2f} EMA21={slow:.2f} | {signal}", end="")

                # Buy signal: fast crosses above slow and not in position
                if fast > slow and not in_position:
                    print(" → 🛒 BUY")
                    cmd_buy(api, BOT_TICKER, BOT_QTY)
                    in_position = True

                # Sell signal: fast crosses below slow and in position
                elif fast < slow and in_position:
                    print(" → 💰 SELL")
                    cmd_sell(api, BOT_TICKER, BOT_QTY)
                    in_position = False
                else:
                    print(" → HOLD")

            time.sleep(BOT_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped.")
            cmd_status(api)
            break
        except Exception as e:
            print(f"\n   ⚠️  Error: {e}")
            time.sleep(30)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    api  = get_client()

    if not args or args[0] == "status":
        cmd_status(api)

    elif args[0] == "quote" and len(args) >= 2:
        cmd_quote(api, args[1].upper())

    elif args[0] == "buy" and len(args) >= 3:
        cmd_buy(api, args[1].upper(), int(args[2]))

    elif args[0] == "sell" and len(args) >= 3:
        cmd_sell(api, args[1].upper(), int(args[2]))

    elif args[0] == "positions":
        cmd_positions(api)

    elif args[0] == "orders":
        cmd_orders(api)

    elif args[0] == "bot":
        run_bot(api)

    else:
        print("\nUsage:")
        print("  python alpaca_paper.py status")
        print("  python alpaca_paper.py quote AAPL")
        print("  python alpaca_paper.py buy AAPL 1")
        print("  python alpaca_paper.py sell AAPL 1")
        print("  python alpaca_paper.py positions")
        print("  python alpaca_paper.py orders")
        print("  python alpaca_paper.py bot")


if __name__ == "__main__":
    main()
