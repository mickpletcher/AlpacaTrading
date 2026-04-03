from __future__ import annotations

import logging
from dataclasses import dataclass

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    message: str
    order_id: str | None = None


def normalize_symbol(raw_ticker: str) -> str:
    ticker = raw_ticker.strip().upper()
    if ticker == "BTCUSD":
        return "BTC/USD"
    return ticker


class AlpacaExecutor:
    def __init__(self, api_key: str, secret_key: str, paper: bool, logger: logging.Logger) -> None:
        self.logger = logger
        self.trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)

    def execute_signal(self, action: str, ticker: str, quantity: float) -> ExecutionResult:
        symbol = normalize_symbol(ticker)
        normalized_action = action.strip().lower()

        try:
            if normalized_action == "buy":
                return self._buy(symbol, quantity)
            if normalized_action == "sell":
                return self._sell(symbol, quantity)
            if normalized_action == "close":
                return self._close(symbol)

            message = f"Unknown action value '{action}'. Signal skipped."
            self.logger.warning(message)
            return ExecutionResult(success=False, message=message)
        except APIError as exc:
            error_text = f"Alpaca API error | symbol={symbol} action={normalized_action} code={getattr(exc, 'status_code', 'unknown')} message={exc}"
            self.logger.error(error_text)
            return ExecutionResult(success=False, message=error_text)
        except Exception as exc:  # noqa: BLE001
            error_text = f"Unhandled execution error | symbol={symbol} action={normalized_action} message={exc}"
            self.logger.error(error_text)
            return ExecutionResult(success=False, message=error_text)

    def _buy(self, symbol: str, quantity: float) -> ExecutionResult:
        order = self.trading_client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
        )
        order_id = str(order.id)
        self.logger.info("ORDER_SUBMITTED | symbol=%s action=buy qty=%.8f order_id=%s status=%s", symbol, quantity, order_id, getattr(order, "status", "unknown"))
        return ExecutionResult(success=True, message="buy submitted", order_id=order_id)

    def _sell(self, symbol: str, quantity: float) -> ExecutionResult:
        account = self.trading_client.get_account()
        shorting_enabled = bool(getattr(account, "shorting_enabled", False))

        if shorting_enabled:
            order = self.trading_client.submit_order(
                MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                )
            )
            order_id = str(order.id)
            self.logger.info("ORDER_SUBMITTED | symbol=%s action=sell qty=%.8f order_id=%s status=%s", symbol, quantity, order_id, getattr(order, "status", "unknown"))
            return ExecutionResult(success=True, message="sell submitted", order_id=order_id)

        close_order = self.trading_client.close_position(symbol)
        order_id = str(getattr(close_order, "id", "")) or None
        self.logger.info("ORDER_SUBMITTED | symbol=%s action=sell_close_long qty=%.8f order_id=%s status=%s", symbol, quantity, order_id or "n/a", getattr(close_order, "status", "unknown"))
        return ExecutionResult(success=True, message="sell handled by closing long", order_id=order_id)

    def _close(self, symbol: str) -> ExecutionResult:
        close_order = self.trading_client.close_position(symbol)
        order_id = str(getattr(close_order, "id", "")) or None
        self.logger.info("ORDER_SUBMITTED | symbol=%s action=close qty=all order_id=%s status=%s", symbol, order_id or "n/a", getattr(close_order, "status", "unknown"))
        return ExecutionResult(success=True, message="position close submitted", order_id=order_id)
