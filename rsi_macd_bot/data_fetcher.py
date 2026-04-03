from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


def parse_timeframe(label: str) -> TimeFrame:
    mapping = {
        "1Min": TimeFrame(1, TimeFrameUnit.Minute),
        "5Min": TimeFrame(5, TimeFrameUnit.Minute),
        "15Min": TimeFrame(15, TimeFrameUnit.Minute),
        "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
        "1Day": TimeFrame(1, TimeFrameUnit.Day),
    }
    if label not in mapping:
        raise ValueError(f"Unsupported timeframe: {label}")
    return mapping[label]


def get_bars(
    data_client: StockHistoricalDataClient,
    symbol: str,
    timeframe: str,
    limit: int = 100,
) -> Optional[pd.DataFrame]:
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=parse_timeframe(timeframe),
            start=start,
            end=end,
            limit=limit,
        )
        response = data_client.get_stock_bars(request)
        bars = response.df
        if bars.empty:
            return None

        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.reset_index()
            bars = bars[bars["symbol"] == symbol]
        else:
            bars = bars.reset_index()

        frame = bars[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        return frame.sort_values("timestamp").reset_index(drop=True)
    except APIError:
        return None
    except Exception:
        return None
