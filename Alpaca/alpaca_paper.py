"""
Alpaca paper trading helpers.

Usage:
  python alpaca_paper.py status
  python alpaca_paper.py quote AAPL
  python alpaca_paper.py buy AAPL 1
  python alpaca_paper.py sell AAPL 1
  python alpaca_paper.py positions
  python alpaca_paper.py orders
  python alpaca_paper.py bot
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

from circuit_breaker import is_safe_to_trade

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "").strip()
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "").strip()
TRADING_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").strip().rstrip("/")
DATA_BASE_URL = "https://data.alpaca.markets"

BOT_TICKER = os.getenv("ALPACA_BOT_TICKER", "SPY").strip().upper()
BOT_INTERVAL = max(5, int(os.getenv("ALPACA_BOT_INTERVAL_SECONDS", "60")))
BOT_QTY = max(1, int(os.getenv("ALPACA_BOT_QTY", "1")))
EMA_FAST = max(2, int(os.getenv("ALPACA_BOT_EMA_FAST", "9")))
EMA_SLOW = max(EMA_FAST + 1, int(os.getenv("ALPACA_BOT_EMA_SLOW", "21")))
PRICE_HISTORY: list[float] = []


def get_headers() -> dict[str, str]:
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        print("Alpaca credentials are missing. Add ALPACA_API_KEY and ALPACA_SECRET_KEY to .env.")
        sys.exit(1)

    return {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        "accept": "application/json",
    }


def api_request(
    method: str,
    path: str,
    *,
    params: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
    use_data_api: bool = False,
    allow_not_found: bool = False,
) -> dict[str, object] | list[dict[str, object]]:
    base_url = DATA_BASE_URL if use_data_api else TRADING_BASE_URL
    response = requests.request(
        method=method,
        url=f"{base_url}{path}",
        headers=get_headers(),
        params=params,
        json=payload,
        timeout=15,
    )

    if allow_not_found and response.status_code == 404:
        return {}

    response.raise_for_status()
    return response.json()


def cmd_status() -> None:
    acct = api_request("GET", "/v2/account")
    print("\n📊 PAPER ACCOUNT STATUS")
    print("=" * 40)
    print(f"  Status:          {acct['status']}")
    print(f"  Portfolio Value: ${float(acct['portfolio_value']):>12,.2f}")
    print(f"  Cash:            ${float(acct['cash']):>12,.2f}")
    print(f"  Buying Power:    ${float(acct['buying_power']):>12,.2f}")
    print(f"  Day Trades Used: {acct['daytrade_count']} / 3 (PDT rule)")
    print(f"  Equity:          ${float(acct['equity']):>12,.2f}")
    pnl = float(acct["equity"]) - float(acct["last_equity"])
    emoji = "📈" if pnl >= 0 else "📉"
    print(f"  Today's P&L:     {emoji} ${pnl:>+,.2f}")
    print("=" * 40)


def cmd_quote(ticker: str) -> None:
    try:
        quote_response = api_request(
            "GET",
            "/v2/stocks/quotes/latest",
            params={"symbols": ticker},
            use_data_api=True,
        )
        trade_response = api_request(
            "GET",
            "/v2/stocks/trades/latest",
            params={"symbols": ticker},
            use_data_api=True,
        )
        quote = quote_response["quotes"][ticker]
        trade = trade_response["trades"][ticker]
        print(f"\n📌 {ticker}")
        print(f"   Bid:   ${float(quote['bp']):>10.2f}  (x{quote['bs']})")
        print(f"   Ask:   ${float(quote['ap']):>10.2f}  (x{quote['as']})")
        print(f"   Last:  ${float(trade['p']):>10.2f}  @ {trade['t']}")
        spread = float(quote["ap"]) - float(quote["bp"])
        print(f"   Spread: ${spread:.4f}  ({spread/float(trade['p'])*100:.3f}%)")
    except Exception as exc:
        print(f"❌ Quote error: {exc}")


def submit_market_order(ticker: str, qty: int, side: str) -> dict[str, object] | None:
    safe_to_trade, reason = is_safe_to_trade()
    if not safe_to_trade:
        print(f"   Trading blocked: {reason}")
        return None

    try:
        return api_request(
            "POST",
            "/v2/orders",
            payload={
                "symbol": ticker,
                "qty": qty,
                "side": side,
                "type": "market",
                "time_in_force": "day",
            },
        )
    except Exception as exc:
        print(f"   Order failed: {exc}")
        return None


def cmd_buy(ticker: str, qty: int) -> None:
    print(f"\n🛒 Buying {qty} share(s) of {ticker} at market...")
    order = submit_market_order(ticker, qty, "buy")
    if order:
        print(f"   ✅ Order submitted: {order['id']}")
        print(f"   Status: {order['status']}")


def cmd_sell(ticker: str, qty: int) -> None:
    print(f"\n💰 Selling {qty} share(s) of {ticker} at market...")
    order = submit_market_order(ticker, qty, "sell")
    if order:
        print(f"   ✅ Order submitted: {order['id']}")
        print(f"   Status: {order['status']}")


def cmd_positions() -> None:
    positions = api_request("GET", "/v2/positions")
    if not positions:
        print("\n📭 No open positions.")
        return
    print(f"\n📂 OPEN POSITIONS ({len(positions)})")
    print("=" * 55)
    print(f"  {'Symbol':<8} {'Qty':>5} {'Entry':>10} {'Current':>10} {'P&L':>10}")
    print("-" * 55)
    for position in positions:
        pnl = float(position["unrealized_pl"])
        emoji = "▲" if pnl >= 0 else "▼"
        print(
            f"  {position['symbol']:<8} {position['qty']:>5} ${float(position['avg_entry_price']):>9.2f} "
            f"${float(position['current_price']):>9.2f} {emoji}${pnl:>+9.2f}"
        )
    print("=" * 55)


def cmd_orders() -> None:
    orders = api_request("GET", "/v2/orders", params={"status": "open"})
    if not orders:
        print("\n📭 No open orders.")
        return
    print(f"\n📋 OPEN ORDERS ({len(orders)})")
    print("=" * 55)
    for order in orders:
        print(f"  {order['symbol']} | {str(order['side']).upper()} {order['qty']} | {order['type']} | {order['status']}")
    print("=" * 55)


def ema(prices: list[float], period: int) -> float | None:
    if len(prices) < period:
        return None
    smoothing = 2 / (period + 1)
    ema_value = sum(prices[:period]) / period
    for price in prices[period:]:
        ema_value = price * smoothing + ema_value * (1 - smoothing)
    return ema_value


def is_market_open() -> bool:
    clock = api_request("GET", "/v2/clock")
    return bool(clock.get("is_open"))


def run_bot() -> None:
    print(f"\n🤖 EMA CROSSOVER BOT — {BOT_TICKER}")
    print(f"   Fast EMA: {EMA_FAST} | Slow EMA: {EMA_SLOW}")
    print(f"   Qty per trade: {BOT_QTY} share(s)")
    print(f"   Check interval: {BOT_INTERVAL}s")
    print("   Press Ctrl+C to stop.\n")

    in_position = False
    prev_fast = None
    prev_slow = None

    try:
        position = api_request("GET", f"/v2/positions/{BOT_TICKER}", allow_not_found=True)
        if position:
            in_position = True
            print(f"   📂 Existing position found: {position['qty']} shares")
    except Exception:
        pass

    while True:
        try:
            if not is_market_open():
                print(f"   ⏰ Market closed. Waiting... ({datetime.now().strftime('%H:%M:%S')})")
                time.sleep(60)
                continue

            trade_response = api_request(
                "GET",
                "/v2/stocks/trades/latest",
                params={"symbols": BOT_TICKER},
                use_data_api=True,
            )
            price = float(trade_response["trades"][BOT_TICKER]["p"])
            PRICE_HISTORY.append(price)

            if len(PRICE_HISTORY) > 100:
                PRICE_HISTORY.pop(0)

            fast = ema(PRICE_HISTORY, EMA_FAST)
            slow = ema(PRICE_HISTORY, EMA_SLOW)
            timestamp = datetime.now().strftime("%H:%M:%S")

            if fast is None or slow is None:
                bars_needed = max(EMA_FAST, EMA_SLOW)
                print(f"   [{timestamp}] ${price:.2f} | Collecting data... ({len(PRICE_HISTORY)}/{bars_needed})")
            else:
                signal = "▲ BULL" if fast > slow else "▼ BEAR"
                print(f"   [{timestamp}] ${price:.2f} | EMA9={fast:.2f} EMA21={slow:.2f} | {signal}", end="")
                cross_up = prev_fast is not None and prev_slow is not None and prev_fast <= prev_slow and fast > slow
                cross_down = prev_fast is not None and prev_slow is not None and prev_fast >= prev_slow and fast < slow

                if cross_up and not in_position:
                    print(" → 🛒 BUY")
                    order = submit_market_order(BOT_TICKER, BOT_QTY, "buy")
                    if order:
                        in_position = True
                elif cross_down and in_position:
                    print(" → 💰 SELL")
                    order = submit_market_order(BOT_TICKER, BOT_QTY, "sell")
                    if order:
                        in_position = False
                else:
                    print(" → HOLD")

                prev_fast = fast
                prev_slow = slow

            time.sleep(BOT_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped.")
            cmd_status()
            break
        except Exception as exc:
            print(f"\n   ⚠️  Error: {exc}")
            time.sleep(30)


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "status":
        cmd_status()
    elif args[0] == "quote" and len(args) >= 2:
        cmd_quote(args[1].upper())
    elif args[0] == "buy" and len(args) >= 3:
        cmd_buy(args[1].upper(), int(args[2]))
    elif args[0] == "sell" and len(args) >= 3:
        cmd_sell(args[1].upper(), int(args[2]))
    elif args[0] == "positions":
        cmd_positions()
    elif args[0] == "orders":
        cmd_orders()
    elif args[0] == "bot":
        run_bot()
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
