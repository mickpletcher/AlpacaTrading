from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_PATH = Path(__file__).resolve().parent / "trades.log"


def get_logger() -> logging.Logger:
    logger = logging.getLogger("rsi_macd_bot")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(LOG_PATH, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    symbol: str,
    signal: str,
    action: str,
    qty: float,
    price: float,
    rsi: float,
    macd_hist: float,
) -> None:
    logger.info(
        "%s | %s | %s | %.6f | %.4f | %.2f | %.6f",
        symbol,
        signal,
        action,
        qty,
        price,
        rsi,
        macd_hist,
    )
