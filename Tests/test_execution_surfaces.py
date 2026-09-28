from __future__ import annotations

import importlib.util
import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "relative_path",
    [
        "Backtesting/strategies/live_bollinger_rsi.py",
        "Backtesting/strategies/live_ema.py",
        "Backtesting/strategies/live_gap_momentum.py",
        "Backtesting/strategies/live_rsi_stack.py",
        "rsi_macd_bot/bot.py",
        "btc-signal-executor/executor.py",
    ],
)
def test_execution_surface_uses_shared_paper_client(relative_path):
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    assert "PaperTradingClient(" in source
    assert re.search(r"(?<!Paper)TradingClient\(", source) is None


def test_rsi_market_order_construction_and_account_failure():
    path = ROOT / "rsi_macd_bot" / "order_manager.py"
    spec = importlib.util.spec_from_file_location("rsi_order_manager", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    class FakeClient:
        request = None

        def submit_order(self, request):
            self.request = request
            return SimpleNamespace(id="order-1", filled_avg_price=None)

        def get_all_positions(self):
            raise RuntimeError("account unavailable")

    client = FakeClient()
    module.place_market_order(client, logging.getLogger("rsi-order"), "SPY", 1, "buy")

    assert client.request.symbol == "SPY"
    assert client.request.side.value == "buy"
    assert client.request.time_in_force.value == "day"
    with pytest.raises(RuntimeError, match="account unavailable"):
        module.get_open_trades_count(client)
