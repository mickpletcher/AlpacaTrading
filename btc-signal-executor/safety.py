from __future__ import annotations

import threading
import time
import sqlite3
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


class ReplayGuard:
    def __init__(self, retention_seconds: int, db_path: Path) -> None:
        self.retention_seconds = retention_seconds
        self.db_path = db_path
        self._lock = threading.Lock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS accepted_signals (signal_id TEXT PRIMARY KEY, accepted_at REAL NOT NULL)"
            )

    def accept(self, signal_id: str) -> bool:
        now = time.time()
        with self._lock:
            cutoff = now - self.retention_seconds
            with sqlite3.connect(self.db_path) as connection:
                connection.execute("DELETE FROM accepted_signals WHERE accepted_at < ?", (cutoff,))
                try:
                    connection.execute(
                        "INSERT INTO accepted_signals (signal_id, accepted_at) VALUES (?, ?)",
                        (signal_id, now),
                    )
                except sqlite3.IntegrityError:
                    return False
                return True


class RateLimiter:
    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            requests = self._requests[client_id]
            while requests and requests[0] < now - 60:
                requests.popleft()
            if len(requests) >= self.requests_per_minute:
                return False
            requests.append(now)
            return True


class FailureCircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: int) -> None:
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.opened_at: float | None = None
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            if self.opened_at is None:
                return True
            if time.monotonic() - self.opened_at >= self.reset_seconds:
                self.failures = 0
                self.opened_at = None
                return True
            return False

    def record(self, success: bool) -> None:
        with self._lock:
            if success:
                self.failures = 0
                self.opened_at = None
                return
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = time.monotonic()


def is_fresh(timestamp: datetime, max_age_seconds: int) -> bool:
    if timestamp.tzinfo is None:
        return False
    age = (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds()
    return 0 <= age <= max_age_seconds
