from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config import get_settings
from executor import AlpacaExecutor
from validator import parse_payload, validate_passphrase, validation_error_to_text


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


logger = configure_logging()
settings = get_settings()
executor = AlpacaExecutor(
    api_key=settings.alpaca_api_key,
    secret_key=settings.alpaca_secret_key,
    paper=("paper-api" in settings.alpaca_base_url),
    logger=logger,
)

app = FastAPI(title="BTC Signal Executor")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        raw_payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("WEBHOOK_REJECTED | reason=invalid_json | details=%s", exc)
        raise HTTPException(status_code=422, detail="Invalid JSON payload") from exc

    try:
        payload = parse_payload(raw_payload)
    except ValidationError as exc:
        reason = validation_error_to_text(exc)
        logger.warning("WEBHOOK_REJECTED | reason=validation_error | details=%s | payload=%s", reason, raw_payload)
        raise HTTPException(status_code=422, detail=reason) from exc

    logger.info(
        "WEBHOOK_RECEIVED | ticker=%s action=%s quantity=%.8f price=%.2f",
        payload.ticker,
        payload.action,
        payload.quantity,
        payload.price,
    )

    if not validate_passphrase(payload.passphrase, settings.webhook_passphrase):
        logger.warning(
            "WEBHOOK_REJECTED | reason=invalid_passphrase | ticker=%s action=%s quantity=%.8f",
            payload.ticker,
            payload.action,
            payload.quantity,
        )
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = executor.execute_signal(action=payload.action, ticker=payload.ticker, quantity=payload.quantity)

    # Always return 200 for execution stage outcomes to avoid TradingView retry storms.
    return JSONResponse(
        status_code=200,
        content={
            "accepted": True,
            "success": result.success,
            "message": result.message,
            "order_id": result.order_id,
        },
    )
