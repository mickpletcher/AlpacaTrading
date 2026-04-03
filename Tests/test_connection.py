"""
Filename: test_connection.py
Purpose: Validate local Alpaca credentials and basic paper trading API connectivity.
Author: TODO

README
Run this file with:
pytest Tests/test_connection.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")


def require_credentials() -> tuple[str, str]:
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        pytest.skip("Skipping Alpaca connection tests because ALPACA_API_KEY and ALPACA_SECRET_KEY are not set.")
    return api_key, secret_key


def alpaca_headers() -> dict[str, str]:
    api_key, secret_key = require_credentials()
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }


def test_credentials_present() -> None:
    api_key, secret_key = require_credentials()
    assert api_key
    assert secret_key


def test_account_endpoint_returns_200() -> None:
    response = requests.get(f"{BASE_URL}/v2/account", headers=alpaca_headers(), timeout=15)
    assert response.status_code == 200, response.text


def test_clock_endpoint_contains_is_open() -> None:
    response = requests.get(f"{BASE_URL}/v2/clock", headers=alpaca_headers(), timeout=15)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "is_open" in payload
    assert isinstance(payload["is_open"], bool)