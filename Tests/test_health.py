from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from Operations.health import (
    check_circuit_breaker,
    check_rejected_orders,
    check_scheduler,
    check_stale_file,
    missing_stop_symbols,
    write_report,
)


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)


def test_stale_data_reports_pass_fail_and_unknown(tmp_path: Path) -> None:
    data_path = tmp_path / "fresh.log"
    data_path.write_text("ok", encoding="utf-8")
    timestamp = (NOW - timedelta(minutes=5)).timestamp()
    os.utime(data_path, (timestamp, timestamp))

    fresh = check_stale_file(tmp_path, {"name": "Feed", "path": "fresh.log", "max_age_minutes": 10}, NOW)
    stale = check_stale_file(tmp_path, {"name": "Feed", "path": "fresh.log", "max_age_minutes": 1}, NOW)
    missing = check_stale_file(tmp_path, {"name": "Optional", "path": "missing.log", "max_age_minutes": 1}, NOW)

    assert fresh.status == "PASS"
    assert stale.status == "FAIL"
    assert missing.status == "UNKNOWN"


def test_rejected_order_scheduler_and_circuit_failures(tmp_path: Path) -> None:
    log_path = tmp_path / "orders.log"
    log_path.write_text("SPY | BUY | ORDER_REJECTED | buying power\n", encoding="utf-8")
    os.utime(log_path, (NOW.timestamp(), NOW.timestamp()))
    config = {
        "rejected_order_logs": ["orders.log"],
        "rejected_order_patterns": ["ORDER_REJECTED"],
        "rejected_order_lookback_minutes": 60,
        "scheduler_status_path": "scheduler.json",
        "scheduler_max_age_minutes": 60,
        "circuit_state_path": "circuit.json",
    }
    (tmp_path / "scheduler.json").write_text(json.dumps({"finished_at": NOW.isoformat(), "exit_code": 3, "error": "failed"}), encoding="utf-8")
    (tmp_path / "circuit.json").write_text(json.dumps({"pause_until": (NOW + timedelta(minutes=5)).isoformat(), "pause_reason": "api failure"}), encoding="utf-8")

    assert check_rejected_orders(tmp_path, config, NOW).status == "FAIL"
    assert check_scheduler(tmp_path, config, NOW).status == "FAIL"
    assert check_circuit_breaker(tmp_path, config, NOW).status == "FAIL"


def test_missing_stop_detection_compares_quantity() -> None:
    positions = [SimpleNamespace(symbol="SPY", qty="2"), SimpleNamespace(symbol="QQQ", qty="1")]
    orders = [SimpleNamespace(symbol="SPY", qty="1", type="stop", side="sell"), SimpleNamespace(symbol="QQQ", qty="1", type="stop_limit", side="sell")]

    assert missing_stop_symbols(positions, orders) == ["SPY"]


def test_health_report_is_machine_and_human_readable(tmp_path: Path) -> None:
    results = [
        check_stale_file(tmp_path, {"name": "Optional", "path": "missing.log", "max_age_minutes": 1}, NOW)
    ]
    write_report(results, tmp_path, NOW)

    payload = json.loads((tmp_path / "health-status.json").read_text(encoding="utf-8"))
    assert payload["overall"] == "ATTENTION"
    assert "Local Trading Health" in (tmp_path / "health-report.html").read_text(encoding="utf-8")
    assert "UNKNOWN" in (tmp_path / "health-alerts.log").read_text(encoding="utf-8")
