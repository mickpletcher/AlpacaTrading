from __future__ import annotations

import os
import signal
import time
from typing import Optional

import schedule
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient
from dotenv import load_dotenv

from config import get_config
from data_fetcher import get_bars
from indicators import calculate_macd, calculate_rsi, get_signal
from logger import get_logger, log_event
from order_manager import (
    calculate_qty,
    get_last_price,
    get_open_position,
    get_open_trades_count,
    log_api_error,
    place_market_order,
    place_stop_loss,
    wait_for_fill_price,
)

load_dotenv()


class BotRuntime:
    def __init__(self) -> None:
        self.running = True
        self.config = get_config()
        self.logger = get_logger()

        api_key = os.getenv("ALPACA_API_KEY", "").strip()
        secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
        if not api_key or not secret_key:
            raise RuntimeError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in .env")

        self.trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=self.config.paper)
        self.data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

    def _market_is_open(self) -> bool:
        clock = self.trading_client.get_clock()
        return bool(clock.is_open)

    def _account_equity(self) -> float:
        account = self.trading_client.get_account()
        return float(account.equity)

    def _scan_symbol(self, symbol: str) -> None:
        try:
            bars = get_bars(self.data_client, symbol, self.config.bar_timeframe, limit=150)
            if bars is None or bars.empty:
                self.logger.info("%s | NO_DATA | SKIP | 0 | 0 | 0 | 0", symbol)
                return

            calc = calculate_rsi(bars, period=self.config.rsi_period)
            calc = calculate_macd(
                calc,
                fast=self.config.macd_fast,
                slow=self.config.macd_slow,
                signal=self.config.macd_signal,
            )

            latest = calc.iloc[-1]
            rsi_value = float(latest.get("rsi") or 0)
            macd_hist = float(latest.get("macd_hist") or 0)
            close_price = float(latest.get("close") or 0)
            signal_value = get_signal(
                calc,
                window=self.config.signal_window,
                rsi_oversold=self.config.rsi_oversold,
                rsi_overbought=self.config.rsi_overbought,
            )

            position = get_open_position(self.trading_client, symbol)
            open_trades = get_open_trades_count(self.trading_client)

            if signal_value == "BUY":
                if position is not None:
                    log_event(self.logger, symbol, "BUY", "SKIP_ALREADY_OPEN", 0.0, close_price, rsi_value, macd_hist)
                    return

                if open_trades >= self.config.max_open_trades:
                    log_event(self.logger, symbol, "BUY", "SKIP_MAX_OPEN_TRADES", 0.0, close_price, rsi_value, macd_hist)
                    return

                equity = self._account_equity()
                last_price = get_last_price(self.data_client, symbol)
                qty = calculate_qty(symbol, equity, self.config.position_size_pct, last_price)
                if qty <= 0:
                    log_event(self.logger, symbol, "BUY", "SKIP_QTY_ZERO", 0.0, last_price, rsi_value, macd_hist)
                    return

                buy_order = place_market_order(self.trading_client, self.logger, symbol, qty, "buy")
                fill_price = wait_for_fill_price(self.trading_client, str(buy_order.id))
                if fill_price is None:
                    fill_price = last_price

                place_stop_loss(
                    self.trading_client,
                    self.logger,
                    symbol,
                    qty,
                    fill_price,
                    self.config.risk_per_trade,
                )
                log_event(self.logger, symbol, "BUY", "ORDER_PLACED", qty, fill_price, rsi_value, macd_hist)
                return

            if signal_value == "SELL":
                if position is None:
                    log_event(self.logger, symbol, "SELL", "SKIP_NO_POSITION", 0.0, close_price, rsi_value, macd_hist)
                    return

                qty = float(position.qty)
                sell_order = place_market_order(self.trading_client, self.logger, symbol, qty, "sell")
                fill_price = wait_for_fill_price(self.trading_client, str(sell_order.id))
                if fill_price is None:
                    fill_price = close_price
                log_event(self.logger, symbol, "SELL", "ORDER_PLACED", qty, fill_price, rsi_value, macd_hist)
                return

            log_event(self.logger, symbol, "NONE", "NO_ACTION", 0.0, close_price, rsi_value, macd_hist)
        except Exception as exc:
            log_api_error(self.logger, symbol, "SCAN", exc)

    def scan_once(self) -> None:
        try:
            if not self._market_is_open():
                self.logger.info("MARKET_CLOSED | SKIP_CYCLE")
                return

            for symbol in self.config.watchlist:
                self._scan_symbol(symbol)
        except Exception as exc:
            log_api_error(self.logger, "GLOBAL", "CYCLE", exc)

    def log_open_positions_summary(self) -> None:
        try:
            positions = self.trading_client.get_all_positions()
            if not positions:
                self.logger.info("SHUTDOWN_SUMMARY | NO_OPEN_POSITIONS")
                return
            for position in positions:
                self.logger.info(
                    "SHUTDOWN_SUMMARY | %s | qty=%s | avg_entry=%s | unrealized_pl=%s",
                    position.symbol,
                    position.qty,
                    position.avg_entry_price,
                    position.unrealized_pl,
                )
        except Exception as exc:
            log_api_error(self.logger, "GLOBAL", "SHUTDOWN_SUMMARY", exc)

    def run(self) -> None:
        schedule.every(5).minutes.do(self.scan_once)
        self.logger.info("BOT_START | paper=%s | timeframe=%s", self.config.paper, self.config.bar_timeframe)

        def _stop(_sig: Optional[int] = None, _frame: Optional[object] = None) -> None:
            self.running = False

        signal.signal(signal.SIGINT, _stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _stop)

        while self.running:
            schedule.run_pending()
            time.sleep(1)

        self.log_open_positions_summary()
        self.logger.info("BOT_STOP")


def main() -> int:
    runtime = BotRuntime()
    try:
        runtime.run()
        return 0
    except KeyboardInterrupt:
        runtime.log_open_positions_summary()
        return 0
    except Exception as exc:
        runtime.logger.error("FATAL | %s", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
