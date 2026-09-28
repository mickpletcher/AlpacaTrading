from __future__ import annotations

import hmac
import math
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class TradingViewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passphrase: str
    signal_id: str = Field(min_length=8, max_length=48, pattern=r"^[A-Za-z0-9._:-]+$")
    timestamp: datetime
    ticker: str = Field(min_length=1)
    action: str
    price: float = Field(gt=0, allow_inf_nan=False)
    quantity: float = Field(gt=0, allow_inf_nan=False)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"buy", "sell", "close"}:
            raise ValueError("action must be buy, sell, or close")
        return normalized

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


def parse_payload(payload: dict) -> TradingViewPayload:
    return TradingViewPayload.model_validate(payload)


def validate_passphrase(inbound_passphrase: str, expected_passphrase: str) -> bool:
    return hmac.compare_digest(inbound_passphrase, expected_passphrase)


def validate_order_limits(payload: TradingViewPayload, max_quantity: float, max_notional: float) -> None:
    if not math.isfinite(payload.quantity) or payload.quantity > max_quantity:
        raise ValueError("quantity exceeds the configured limit")
    notional = payload.quantity * payload.price
    if not math.isfinite(notional) or notional > max_notional:
        raise ValueError("order notional exceeds the configured limit")


def validation_error_to_text(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors())
