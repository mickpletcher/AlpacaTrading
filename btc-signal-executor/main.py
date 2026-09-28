from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config import Settings, get_settings
from executor import AlpacaExecutor, ExecutionResult
from safety import FailureCircuitBreaker, RateLimiter, ReplayGuard, is_fresh
from validator import (
    parse_payload,
    validate_order_limits,
    validate_passphrase,
    validation_error_to_text,
)


class SignalExecutor(Protocol):
    def execute_signal(
        self, action: str, ticker: str, quantity: float, signal_id: str
    ) -> ExecutionResult: ...


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("btc_signal_executor")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler("executor.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def create_app(
    settings: Settings | None = None,
    executor: SignalExecutor | None = None,
    logger: logging.Logger | None = None,
) -> FastAPI:
    active_settings = settings or get_settings()
    active_logger = logger or configure_logging()
    active_executor = executor or AlpacaExecutor(
        api_key=active_settings.alpaca_api_key,
        secret_key=active_settings.alpaca_secret_key,
        max_daily_loss=active_settings.max_daily_loss,
        logger=active_logger,
    )
    replay_guard = ReplayGuard(
        active_settings.max_signal_age_seconds * 2,
        active_settings.replay_db_path,
    )
    rate_limiter = RateLimiter(active_settings.rate_limit_per_minute)
    circuit_breaker = FailureCircuitBreaker(
        active_settings.failure_threshold, active_settings.failure_reset_seconds
    )
    application = FastAPI(title="BTC Signal Executor")

    @application.get("/health")
    def health() -> dict:
        return {"status": "ok", "paper": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    @application.post("/webhook")
    async def webhook(request: Request):
        client_id = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        try:
            raw_payload = await request.json()
        except Exception as exc:
            active_logger.warning("WEBHOOK_REJECTED | reason=invalid_json")
            raise HTTPException(status_code=422, detail="Invalid JSON payload") from exc

        try:
            payload = parse_payload(raw_payload)
        except ValidationError as exc:
            reason = validation_error_to_text(exc)
            active_logger.warning("WEBHOOK_REJECTED | reason=validation_error | details=%s", reason)
            raise HTTPException(status_code=422, detail=reason) from exc

        if not validate_passphrase(payload.passphrase, active_settings.webhook_passphrase):
            active_logger.warning("WEBHOOK_REJECTED | reason=invalid_passphrase")
            raise HTTPException(status_code=401, detail="Unauthorized")
        if payload.ticker not in active_settings.allowed_tickers:
            raise HTTPException(status_code=422, detail="Ticker is not allowed")
        if payload.action == "buy" and not circuit_breaker.allow():
            raise HTTPException(status_code=503, detail="Execution circuit breaker is open")
        if not is_fresh(payload.timestamp, active_settings.max_signal_age_seconds):
            raise HTTPException(status_code=422, detail="Signal timestamp is stale or invalid")
        try:
            validate_order_limits(payload, active_settings.max_quantity, active_settings.max_notional)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not replay_guard.accept(payload.signal_id):
            raise HTTPException(status_code=409, detail="Duplicate signal_id")

        active_logger.info(
            "WEBHOOK_ACCEPTED | signal_id=%s ticker=%s action=%s quantity=%.8f price=%.2f",
            payload.signal_id,
            payload.ticker,
            payload.action,
            payload.quantity,
            payload.price,
        )
        result = active_executor.execute_signal(
            action=payload.action,
            ticker=payload.ticker,
            quantity=payload.quantity,
            signal_id=payload.signal_id,
        )
        if payload.action == "buy":
            circuit_breaker.record(result.success)
        return JSONResponse(
            status_code=200,
            content={
                "accepted": True,
                "success": result.success,
                "message": result.message,
                "order_id": result.order_id,
            },
        )

    return application


app = create_app()
