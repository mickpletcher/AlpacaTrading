from __future__ import annotations

import os
from typing import Any

from alpaca.trading.client import TradingClient

PAPER_BASE_URL = "https://paper-api.alpaca.markets"


def require_paper_mode(base_url: str | None = None, paper: bool | None = None) -> str:
    configured_url = (base_url or os.getenv("ALPACA_BASE_URL", PAPER_BASE_URL)).strip().rstrip("/")
    if paper is False or configured_url != PAPER_BASE_URL:
        raise RuntimeError(
            "Live trading is disabled. Set ALPACA_BASE_URL=https://paper-api.alpaca.markets."
        )
    return PAPER_BASE_URL


class PaperTradingClient:
    def __init__(self, api_key: str, secret_key: str) -> None:
        require_paper_mode()
        self._client = TradingClient(api_key=api_key, secret_key=secret_key, paper=True)

    def submit_order(self, *args: Any, **kwargs: Any) -> Any:
        require_paper_mode()
        return self._client.submit_order(*args, **kwargs)

    def close_position(self, *args: Any, **kwargs: Any) -> Any:
        require_paper_mode()
        return self._client.close_position(*args, **kwargs)

    def cancel_order_by_id(self, *args: Any, **kwargs: Any) -> Any:
        require_paper_mode()
        return self._client.cancel_order_by_id(*args, **kwargs)

    def cancel_orders(self, *args: Any, **kwargs: Any) -> Any:
        require_paper_mode()
        return self._client.cancel_orders(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)
