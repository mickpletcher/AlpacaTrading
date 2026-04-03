from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from alpaca.common.exceptions import APIError
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest, StopOrderRequest


def get_open_position(trading_client: TradingClient, symbol: str):
    try:
        return trading_client.get_open_position(symbol)
    except APIError as exc:
        if getattr(exc, "status_code", None) == 404:
            return None
        raise


def get_open_trades_count(trading_client: TradingClient) -> int:
    try:
        positions = trading_client.get_all_positions()
        return len(positions)
    except Exception:
        return 0


def calculate_qty(symbol: str, equity: float, pct: float, last_price: float) -> float:
    if equity <= 0 or pct <= 0 or last_price <= 0:
        return 0.0
    order_value = equity * pct
    raw_qty = order_value / last_price
    return round(raw_qty, 6)


def get_last_price(data_client: StockHistoricalDataClient, symbol: str) -> float:
    quote = data_client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=[symbol]))
    payload: Any = quote[symbol]
    ask = float(payload.ask_price or 0)
    bid = float(payload.bid_price or 0)
    return ask if ask > 0 else bid


def _submit_market_request(trading_client: TradingClient, request_kwargs: dict[str, Any]):
    try:
        request = MarketOrderRequest(**request_kwargs)
        return trading_client.submit_order(request)
    except TypeError:
        request_kwargs.pop("fractional", None)
        request = MarketOrderRequest(**request_kwargs)
        return trading_client.submit_order(request)


def place_market_order(
    trading_client: TradingClient,
    logger: logging.Logger,
    symbol: str,
    qty: float,
    side: str,
):
    side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    request_kwargs: dict[str, Any] = {
        "symbol": symbol,
        "qty": qty,
        "side": side_enum,
        "time_in_force": TimeInForce.DAY,
    }
    if qty < 1:
        request_kwargs["fractional"] = True

    order = _submit_market_request(trading_client, request_kwargs)
    logger.info(
        "%s | %s | ORDER_SUBMIT | %.6f | %.4f",
        datetime.now(timezone.utc).isoformat(),
        symbol,
        qty,
        float(getattr(order, "filled_avg_price", 0) or 0),
    )
    return order


def wait_for_fill_price(trading_client: TradingClient, order_id: str, retries: int = 6, sleep_seconds: int = 2) -> Optional[float]:
    import time

    for _ in range(retries):
        try:
            order = trading_client.get_order_by_id(order_id)
            fill_price = getattr(order, "filled_avg_price", None)
            if fill_price is not None:
                return float(fill_price)
        except Exception:
            pass
        time.sleep(sleep_seconds)
    return None


def place_stop_loss(
    trading_client: TradingClient,
    logger: logging.Logger,
    symbol: str,
    qty: float,
    entry_price: float,
    risk_pct: float,
):
    stop_price = round(entry_price * (1 - risk_pct), 4)
    request = StopOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        stop_price=stop_price,
    )
    order = trading_client.submit_order(request)
    logger.info(
        "%s | %s | STOP_SUBMIT | %.6f | %.4f",
        datetime.now(timezone.utc).isoformat(),
        symbol,
        qty,
        stop_price,
    )
    return order


def log_api_error(logger: logging.Logger, symbol: str, context: str, exc: Exception) -> None:
    if isinstance(exc, APIError):
        code = getattr(exc, "status_code", "unknown")
        logger.error("%s | %s | API_ERROR | code=%s message=%s", symbol, context, code, str(exc))
        return
    logger.error("%s | %s | ERROR | %s", symbol, context, str(exc))


def get_open_orders(trading_client: TradingClient):
    return trading_client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
