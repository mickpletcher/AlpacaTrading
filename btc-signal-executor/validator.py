from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError, field_validator


class TradingViewPayload(BaseModel):
    passphrase: str
    ticker: str = Field(min_length=1)
    action: str
    price: float = Field(gt=0)
    quantity: float = Field(gt=0)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"buy", "sell", "close"}:
            return normalized
        return normalized

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


def parse_payload(payload: dict) -> TradingViewPayload:
    return TradingViewPayload.model_validate(payload)


def validate_passphrase(inbound_passphrase: str, expected_passphrase: str) -> bool:
    return inbound_passphrase == expected_passphrase


def validation_error_to_text(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors())
