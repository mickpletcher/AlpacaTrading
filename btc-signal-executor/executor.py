from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

ALPACA_DIR = Path(__file__).resolve().parent.parent / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

from trading_safety import PaperTradingClient


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
    def __init__(self, api_key: str, secret_key: str, max_daily_loss: float, logger: logging.Logger) -> None:
        self.logger = logger
        self.max_daily_loss = max_daily_loss
        self.trading_client = PaperTradingClient(api_key=api_key, secret_key=secret_key)

    def execute_signal(self, action: str, ticker: str, quantity: float, signal_id: str) -> ExecutionResult:
        symbol = normalize_symbol(ticker)
        normalized_action = action.strip().lower()

        try:
            if normalized_action == "buy":
                daily_loss = self._daily_loss()
                if daily_loss >= self.max_daily_loss:
                    message = f"Daily loss limit reached ({daily_loss:.2f}). Signal skipped."
                    self.logger.error(message)
                    return ExecutionResult(success=False, message=message)
                return self._submit(symbol, quantity, OrderSide.BUY, signal_id)
            if normalized_action == "sell":
                return self._submit(symbol, quantity, OrderSide.SELL, signal_id)
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

    def _daily_loss(self) -> float:
        account = self.trading_client.get_account()
        equity = float(account.equity)
        last_equity = float(account.last_equity)
        return max(0.0, last_equity - equity)

    def _submit(self, symbol: str, quantity: float, side: OrderSide, signal_id: str) -> ExecutionResult:
        order = self.trading_client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.GTC,
                client_order_id=signal_id,
            )
        )
        order_id = str(order.id)
        action = "buy" if side == OrderSide.BUY else "sell"
        self.logger.info("ORDER_SUBMITTED | symbol=%s action=%s qty=%.8f order_id=%s status=%s", symbol, action, quantity, order_id, getattr(order, "status", "unknown"))
        return ExecutionResult(success=True, message=f"{action} submitted", order_id=order_id)

    def _close(self, symbol: str) -> ExecutionResult:
        close_order = self.trading_client.close_position(symbol)
        order_id = str(getattr(close_order, "id", "")) or None
        self.logger.info("ORDER_SUBMITTED | symbol=%s action=close qty=all order_id=%s status=%s", symbol, order_id or "n/a", getattr(close_order, "status", "unknown"))
        return ExecutionResult(success=True, message="position close submitted", order_id=order_id)
