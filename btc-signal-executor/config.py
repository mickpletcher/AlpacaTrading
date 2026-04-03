from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    webhook_passphrase: str
    port: int


def get_settings() -> Settings:
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").strip()
    passphrase = os.getenv("WEBHOOK_PASSPHRASE", "").strip()
    port_raw = os.getenv("PORT", "8080").strip()

    if not api_key or not secret_key:
        raise RuntimeError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY in environment.")
    if not passphrase:
        raise RuntimeError("Missing WEBHOOK_PASSPHRASE in environment.")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError("PORT must be a valid integer.") from exc

    return Settings(
        alpaca_api_key=api_key,
        alpaca_secret_key=secret_key,
        alpaca_base_url=base_url,
        webhook_passphrase=passphrase,
        port=port,
    )
