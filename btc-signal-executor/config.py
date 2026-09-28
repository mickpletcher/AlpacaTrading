from __future__ import annotations

import os
import sys
import math
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ALPACA_DIR = Path(__file__).resolve().parent.parent / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

from trading_safety import require_paper_mode


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    webhook_passphrase: str
    port: int
    allowed_tickers: frozenset[str]
    max_quantity: float
    max_notional: float
    max_daily_loss: float
    max_signal_age_seconds: int
    rate_limit_per_minute: int
    failure_threshold: int
    failure_reset_seconds: int
    replay_db_path: Path


def _positive_float(name: str, default: str) -> float:
    try:
        value = float(os.getenv(name, default).strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number.") from exc
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")
    return value


def _positive_int(name: str, default: str) -> int:
    try:
        value = int(os.getenv(name, default).strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")
    return value


def get_settings() -> Settings:
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    base_url = require_paper_mode(os.getenv("ALPACA_BASE_URL"))
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

    allowed_tickers = frozenset(
        ticker.strip().upper()
        for ticker in os.getenv("WEBHOOK_ALLOWED_TICKERS", "BTCUSD,BTC/USD").split(",")
        if ticker.strip()
    )
    if not allowed_tickers:
        raise RuntimeError("WEBHOOK_ALLOWED_TICKERS must contain at least one symbol.")

    return Settings(
        alpaca_api_key=api_key,
        alpaca_secret_key=secret_key,
        alpaca_base_url=base_url,
        webhook_passphrase=passphrase,
        port=port,
        allowed_tickers=allowed_tickers,
        max_quantity=_positive_float("WEBHOOK_MAX_QUANTITY", "0.01"),
        max_notional=_positive_float("WEBHOOK_MAX_NOTIONAL", "1000"),
        max_daily_loss=_positive_float("WEBHOOK_MAX_DAILY_LOSS", "250"),
        max_signal_age_seconds=_positive_int("WEBHOOK_MAX_SIGNAL_AGE_SECONDS", "300"),
        rate_limit_per_minute=_positive_int("WEBHOOK_RATE_LIMIT_PER_MINUTE", "10"),
        failure_threshold=_positive_int("WEBHOOK_FAILURE_THRESHOLD", "3"),
        failure_reset_seconds=_positive_int("WEBHOOK_FAILURE_RESET_SECONDS", "300"),
        replay_db_path=Path(
            os.getenv(
                "WEBHOOK_REPLAY_DB_PATH",
                str(Path(__file__).resolve().parent / "runtime" / "webhook_state.db"),
            )
        ).expanduser().resolve(),
    )
