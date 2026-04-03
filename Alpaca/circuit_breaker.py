"""
Filename: circuit_breaker.py
Purpose: Central trading safety checks for loss streaks, API failures, and market hours.
Author: TODO
"""

from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
JOURNAL_DIR = ROOT_DIR / "Journal"
LOG_PATH = JOURNAL_DIR / "circuit_log.txt"
STATE_PATH = JOURNAL_DIR / "circuit_state.json"
TRADES_PATH = JOURNAL_DIR / "trades.csv"

load_dotenv(ENV_PATH)

DEFAULT_BASE_URL = "https://paper-api.alpaca.markets"
LOSS_THRESHOLD = max(1, int(os.getenv("CIRCUIT_BREAKER_MAX_CONSECUTIVE_LOSSES", "3")))
RATE_LIMIT_RETRIES = max(1, int(os.getenv("CIRCUIT_BREAKER_RATE_LIMIT_RETRIES", "4")))
RATE_LIMIT_BASE_DELAY = max(1.0, float(os.getenv("CIRCUIT_BREAKER_RATE_LIMIT_BASE_DELAY_SECONDS", "2")))
RATE_LIMIT_PAUSE_SECONDS = max(30, int(os.getenv("CIRCUIT_BREAKER_RATE_LIMIT_PAUSE_SECONDS", "120")))
SERVER_ERROR_PAUSE_SECONDS = max(30, int(os.getenv("CIRCUIT_BREAKER_SERVER_ERROR_PAUSE_SECONDS", "300")))
REQUEST_TIMEOUT_SECONDS = max(5, int(os.getenv("CIRCUIT_BREAKER_TIMEOUT_SECONDS", "15")))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_state() -> dict[str, Any]:
    return {
        "consecutive_losses": 0,
        "pause_until": "",
        "pause_reason": "",
        "auth_blocked": False,
        "auth_reason": "",
        "last_status_code": None,
    }


def _log_event(message: str) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _utc_now().isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{message}\n")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return _default_state()

    try:
        with STATE_PATH.open("r", encoding="utf-8") as state_file:
            data = json.load(state_file)
    except (OSError, json.JSONDecodeError):
        data = _default_state()

    state = _default_state()
    state.update(data)
    return state


def _save_state(state: dict[str, Any]) -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2)


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _get_headers() -> dict[str, str] | None:
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        return None

    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }


def _get_base_url() -> str:
    return os.getenv("ALPACA_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")


def _read_consecutive_losses_from_journal() -> int:
    if not TRADES_PATH.exists():
        return 0

    try:
        with TRADES_PATH.open("r", encoding="utf-8", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
    except OSError:
        return 0

    consecutive_losses = 0
    for row in reversed(rows):
        pnl_text = (row.get("pnl") or "").strip()
        if not pnl_text:
            continue

        try:
            pnl_value = float(pnl_text)
        except ValueError:
            continue

        if pnl_value < 0:
            consecutive_losses += 1
            continue

        break

    return consecutive_losses


def _sync_loss_state(state: dict[str, Any]) -> dict[str, Any]:
    journal_losses = _read_consecutive_losses_from_journal()
    if journal_losses != state.get("consecutive_losses", 0):
        state["consecutive_losses"] = journal_losses
        _save_state(state)
    return state


def _clear_expired_pause(state: dict[str, Any]) -> dict[str, Any]:
    pause_until = _parse_timestamp(str(state.get("pause_until", "")))
    if pause_until and _utc_now() >= pause_until:
        state["pause_until"] = ""
        state["pause_reason"] = ""
        state["last_status_code"] = None
        _save_state(state)
        _log_event("Pause window expired. Trading checks resumed.")
    return state


def _set_pause(state: dict[str, Any], seconds: int, reason: str, status_code: int | None = None) -> str:
    state["pause_until"] = (_utc_now() + timedelta(seconds=seconds)).isoformat()
    state["pause_reason"] = reason
    state["last_status_code"] = status_code
    _save_state(state)
    _log_event(reason)
    return reason


def _set_auth_block(state: dict[str, Any], reason: str, status_code: int) -> str:
    state["auth_blocked"] = True
    state["auth_reason"] = reason
    state["last_status_code"] = status_code
    _save_state(state)
    _log_event(reason)
    return reason


def _alpaca_get(path: str) -> tuple[requests.Response | None, str]:
    state = _clear_expired_pause(_load_state())
    headers = _get_headers()
    if not headers:
        reason = "Missing Alpaca credentials in .env or the current environment."
        _log_event(reason)
        return None, reason

    url = f"{_get_base_url()}{path}"

    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            reason = _set_pause(
                state,
                SERVER_ERROR_PAUSE_SECONDS,
                f"Alpaca request failed: {exc}. Pausing trading for {SERVER_ERROR_PAUSE_SECONDS} seconds.",
            )
            return None, reason

        if response.ok:
            return response, "OK"

        status_code = response.status_code
        detail = response.text.strip() or response.reason

        if status_code in (401, 403):
            reason = _set_auth_block(
                state,
                f"Alpaca API returned {status_code}. Trading halted until credentials or permissions are fixed.",
                status_code,
            )
            return None, reason

        if status_code == 429:
            if attempt < RATE_LIMIT_RETRIES - 1:
                delay_seconds = RATE_LIMIT_BASE_DELAY * (2 ** attempt)
                _log_event(
                    f"Alpaca API rate limit hit. Retry {attempt + 1} of {RATE_LIMIT_RETRIES - 1} in {delay_seconds:.1f} seconds."
                )
                time.sleep(delay_seconds)
                continue

            reason = _set_pause(
                state,
                RATE_LIMIT_PAUSE_SECONDS,
                (
                    f"Alpaca API rate limited requests after {RATE_LIMIT_RETRIES} attempts. "
                    f"Pausing trading for {RATE_LIMIT_PAUSE_SECONDS} seconds."
                ),
                status_code,
            )
            return None, reason

        if 500 <= status_code <= 599:
            reason = _set_pause(
                state,
                SERVER_ERROR_PAUSE_SECONDS,
                (
                    f"Alpaca API server error {status_code}: {detail}. "
                    f"Pausing trading for {SERVER_ERROR_PAUSE_SECONDS} seconds."
                ),
                status_code,
            )
            return None, reason

        reason = f"Alpaca API error {status_code}: {detail}"
        _log_event(reason)
        return None, reason

    return None, "Unexpected circuit breaker state."


def record_trade_result(pnl: float) -> tuple[int, str]:
    state = _load_state()
    consecutive_losses = 0 if pnl >= 0 else state.get("consecutive_losses", 0) + 1
    state["consecutive_losses"] = consecutive_losses
    _save_state(state)

    if pnl < 0:
        message = f"Recorded losing trade with P&L {pnl:.2f}. Consecutive losses: {consecutive_losses}."
    else:
        message = f"Recorded non losing trade with P&L {pnl:.2f}. Loss streak reset."

    _log_event(message)
    return consecutive_losses, message


def is_safe_to_trade() -> tuple[bool, str]:
    state = _clear_expired_pause(_sync_loss_state(_load_state()))
    headers = _get_headers()
    if not headers:
        reason = "Missing Alpaca credentials in .env or the current environment."
        _log_event(reason)
        return False, reason

    if state.get("auth_blocked"):
        return False, str(state.get("auth_reason") or "Trading blocked by a prior Alpaca authentication error.")

    consecutive_losses = int(state.get("consecutive_losses", 0))
    if consecutive_losses >= LOSS_THRESHOLD:
        reason = (
            f"Trading halted after {consecutive_losses} consecutive losses. "
            f"Threshold is {LOSS_THRESHOLD}."
        )
        _log_event(reason)
        return False, reason

    pause_until = _parse_timestamp(str(state.get("pause_until", "")))
    if pause_until and _utc_now() < pause_until:
        reason = str(state.get("pause_reason") or "Trading is temporarily paused.")
        return False, reason

    response, reason = _alpaca_get("/v2/clock")
    if response is None:
        return False, reason

    try:
        payload = response.json()
    except ValueError:
        reason = "Alpaca /v2/clock returned invalid JSON."
        _log_event(reason)
        return False, reason

    is_open = payload.get("is_open")
    if not isinstance(is_open, bool):
        reason = "Alpaca /v2/clock response did not include a valid is_open field."
        _log_event(reason)
        return False, reason

    if not is_open:
        reason = "US market is currently closed."
        _log_event(reason)
        return False, reason

    return True, "Market is open and circuit breaker checks passed."


__all__ = ["is_safe_to_trade", "record_trade_result"]