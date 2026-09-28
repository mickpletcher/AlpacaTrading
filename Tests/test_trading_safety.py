from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ALPACA_DIR = ROOT / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

import trading_safety


@pytest.mark.parametrize(
    "url",
    [
        "https://api.alpaca.markets",
        "https://paper-api.alpaca.markets.example.com",
        "https://paper-api.alpaca.market",
    ],
)
def test_paper_gate_rejects_nonpaper_endpoints(url):
    with pytest.raises(RuntimeError, match="Live trading is disabled"):
        trading_safety.require_paper_mode(url)


def test_paper_gate_accepts_exact_endpoint_with_trailing_slash():
    assert (
        trading_safety.require_paper_mode("https://paper-api.alpaca.markets/")
        == trading_safety.PAPER_BASE_URL
    )


def test_mutation_wrapper_rechecks_route_before_submit(monkeypatch):
    class FakeClient:
        called = False

        def submit_order(self, *_args, **_kwargs):
            self.called = True

    client = trading_safety.PaperTradingClient.__new__(trading_safety.PaperTradingClient)
    client._client = FakeClient()
    monkeypatch.setattr(
        trading_safety,
        "require_paper_mode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("blocked")),
    )

    with pytest.raises(RuntimeError, match="blocked"):
        client.submit_order(object())
    assert client._client.called is False


def test_rsi_bot_mode_typo_fails_closed(monkeypatch):
    bot_dir = ROOT / "rsi_macd_bot"
    if str(bot_dir) not in sys.path:
        sys.path.insert(0, str(bot_dir))
    monkeypatch.setenv("PAPER", "treu")
    sys.modules.pop("config", None)
    config = importlib.import_module("config")
    with pytest.raises(RuntimeError, match="Live trading is disabled"):
        config.get_config()
