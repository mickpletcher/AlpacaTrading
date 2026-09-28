from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "btc-signal-executor"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

_test_environment = {
    "ALPACA_API_KEY": "test-key",
    "ALPACA_SECRET_KEY": "test-secret",
    "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
    "WEBHOOK_PASSPHRASE": "test-passphrase",
}
_original_environment = {name: os.environ.get(name) for name in _test_environment}
os.environ.update(_test_environment)

from config import Settings
from config import get_settings
from executor import AlpacaExecutor, ExecutionResult
from main import create_app

for _name, _value in _original_environment.items():
    if _value is None:
        os.environ.pop(_name, None)
    else:
        os.environ[_name] = _value


class FakeExecutor:
    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.calls = []

    def execute_signal(self, **kwargs):
        self.calls.append(kwargs)
        return ExecutionResult(self.success, "handled", "order-1" if self.success else None)


def settings(**overrides):
    values = {
        "alpaca_api_key": "key",
        "alpaca_secret_key": "secret",
        "alpaca_base_url": "https://paper-api.alpaca.markets",
        "webhook_passphrase": "expected-secret",
        "port": 8080,
        "allowed_tickers": frozenset({"BTCUSD", "BTC/USD"}),
        "max_quantity": 0.01,
        "max_notional": 1000.0,
        "max_daily_loss": 250.0,
        "max_signal_age_seconds": 300,
        "rate_limit_per_minute": 20,
        "failure_threshold": 3,
        "failure_reset_seconds": 300,
        "replay_db_path": Path(tempfile.mkdtemp()) / "replay.db",
    }
    values.update(overrides)
    return Settings(**values)


def payload(**overrides):
    values = {
        "passphrase": "expected-secret",
        "signal_id": "signal-12345",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticker": "BTCUSD",
        "action": "buy",
        "price": 65000,
        "quantity": 0.001,
    }
    values.update(overrides)
    return values


def test_valid_signal_executes_once_and_replay_is_rejected():
    executor = FakeExecutor()
    client = TestClient(create_app(settings(), executor, logging.getLogger("btc-test")))

    first = client.post("/webhook", json=payload())
    second = client.post("/webhook", json=payload())

    assert first.status_code == 200
    assert first.json()["success"] is True
    assert second.status_code == 409
    assert len(executor.calls) == 1


def test_replay_is_rejected_after_application_restart():
    active_settings = settings()
    body = payload(signal_id="persistent-signal-1")
    first = TestClient(
        create_app(active_settings, FakeExecutor(), logging.getLogger("btc-replay-first"))
    )
    second = TestClient(
        create_app(active_settings, FakeExecutor(), logging.getLogger("btc-replay-second"))
    )

    assert first.post("/webhook", json=body).status_code == 200
    assert second.post("/webhook", json=body).status_code == 409


def test_invalid_action_secret_symbol_limits_and_timestamp_are_rejected():
    client = TestClient(create_app(settings(), FakeExecutor(), logging.getLogger("btc-invalid")))
    cases = [
        (payload(action="launch", signal_id="invalid-action"), 422),
        (payload(passphrase="wrong", signal_id="invalid-secret"), 401),
        (payload(ticker="ETHUSD", signal_id="invalid-symbol"), 422),
        (payload(quantity=0.02, signal_id="invalid-quantity"), 422),
        (
            payload(
                timestamp=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
                signal_id="invalid-stale",
            ),
            422,
        ),
        (
            payload(
                timestamp=(datetime.now(timezone.utc) + timedelta(seconds=10)).isoformat(),
                signal_id="invalid-future",
            ),
            422,
        ),
    ]
    for body, expected in cases:
        assert client.post("/webhook", json=body).status_code == expected


def test_validation_log_does_not_contain_passphrase(caplog):
    logger = logging.getLogger("btc-redaction")
    client = TestClient(create_app(settings(), FakeExecutor(), logger))
    secret = "do-not-log-this-value"
    with caplog.at_level(logging.WARNING, logger=logger.name):
        response = client.post("/webhook", json={"passphrase": secret, "action": "bad"})
    assert response.status_code == 422
    assert secret not in caplog.text


def test_rate_limit_and_buy_circuit_breaker_do_not_block_close():
    limited = TestClient(
        create_app(
            settings(rate_limit_per_minute=1),
            FakeExecutor(),
            logging.getLogger("btc-rate"),
        )
    )
    assert limited.post("/webhook", json=payload(signal_id="rate-first-1")).status_code == 200
    assert limited.post("/webhook", json=payload(signal_id="rate-second-1")).status_code == 429

    class ActionExecutor:
        def execute_signal(self, **kwargs):
            success = kwargs["action"] == "close"
            return ExecutionResult(success, "handled", "order-1" if success else None)

    failing = TestClient(
        create_app(
            settings(failure_threshold=1),
            ActionExecutor(),
            logging.getLogger("btc-circuit"),
        )
    )
    assert failing.post("/webhook", json=payload(signal_id="failure-first-1")).status_code == 200
    assert failing.post("/webhook", json=payload(signal_id="failure-buy-2")).status_code == 503
    assert failing.post(
        "/webhook", json=payload(signal_id="failure-close-1", action="close")
    ).status_code == 200
    assert failing.post("/webhook", json=payload(signal_id="failure-buy-3")).status_code == 503


def test_nonfinite_environment_limits_are_rejected(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secret")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    monkeypatch.setenv("WEBHOOK_PASSPHRASE", "secret")
    for name, value in [
        ("WEBHOOK_MAX_QUANTITY", "nan"),
        ("WEBHOOK_MAX_NOTIONAL", "inf"),
        ("WEBHOOK_MAX_DAILY_LOSS", "-inf"),
    ]:
        monkeypatch.setenv(name, value)
        with pytest.raises(RuntimeError, match="greater than zero"):
            get_settings()
        monkeypatch.delenv(name)


def test_crypto_order_uses_gtc_and_signal_id():
    class FakeTradingClient:
        def __init__(self):
            self.request = None

        def get_account(self):
            return SimpleNamespace(equity="10000", last_equity="10000")

        def submit_order(self, order_data):
            self.request = order_data
            return SimpleNamespace(id="order-1", status="accepted")

    fake = FakeTradingClient()
    executor = AlpacaExecutor.__new__(AlpacaExecutor)
    executor.logger = logging.getLogger("btc-order")
    executor.max_daily_loss = 250
    executor.trading_client = fake

    result = executor.execute_signal("buy", "BTCUSD", 0.001, "signal-order-1")

    assert result.success is True
    assert fake.request.time_in_force.value == "gtc"
    assert fake.request.client_order_id == "signal-order-1"
    assert fake.request.symbol == "BTC/USD"
