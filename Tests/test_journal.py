from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JOURNAL_DIR = ROOT / "Journal"
if str(JOURNAL_DIR) not in sys.path:
    sys.path.insert(0, str(JOURNAL_DIR))

import journal_server
import journal_store


def configure_temp_store(monkeypatch, tmp_path):
    csv_path = tmp_path / "trades.csv"
    db_path = tmp_path / "trades.db"
    monkeypatch.setattr(journal_store, "JOURNAL_DIR", tmp_path)
    monkeypatch.setattr(journal_store, "CSV_PATH", csv_path)
    monkeypatch.setattr(journal_store, "DB_PATH", db_path)
    monkeypatch.setattr(journal_server, "CSV_PATH", csv_path)
    return journal_server.app.test_client()


def add_trade(client, date, ticker, entry, exit_price, qty=1):
    return client.post(
        "/api/trades",
        json={
            "date": date,
            "ticker": ticker,
            "direction": "LONG",
            "entry": entry,
            "exit": exit_price,
            "qty": qty,
        },
    )


def test_sqlite_is_authoritative_and_explicit_import_is_idempotent(monkeypatch, tmp_path):
    client = configure_temp_store(monkeypatch, tmp_path)
    assert add_trade(client, "2026-09-26", "AAA", 100, 120).status_code == 201
    assert add_trade(client, "2026-09-27", "BBB", 100, 90, qty=2).status_code == 201

    assert client.get("/api/export").status_code == 200
    connection = journal_store.get_db_connection()
    assert journal_store.import_csv_to_sqlite(connection) == 0
    assert connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 2
    connection.close()


def test_statistics_use_gross_profit_and_deterministic_latest_streak(monkeypatch, tmp_path):
    client = configure_temp_store(monkeypatch, tmp_path)
    add_trade(client, "2026-09-25", "AAA", 100, 120)
    add_trade(client, "2026-09-26", "BBB", 100, 90, qty=2)
    add_trade(client, "2026-09-27", "CCC", 100, 90)

    stats = client.get("/api/stats").get_json()
    assert stats["profit_factor"] == 0.67
    assert stats["current_streak"] == {"type": "LOSS", "count": 2}


def test_journal_rejects_invalid_writes_and_nonloopback_clients(monkeypatch, tmp_path):
    client = configure_temp_store(monkeypatch, tmp_path)
    assert client.post("/api/trades", json={"ticker": "AAPL"}).status_code == 400
    response = client.get("/api/trades", environ_base={"REMOTE_ADDR": "10.0.0.5"})
    assert response.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        ["DO-NOT-REFLECT"],
        {
            "ticker": "AAPL",
            "direction": "LONG",
            "entry": "DO-NOT-REFLECT",
            "qty": 1,
        },
        {
            "ticker": "AAPL",
            "direction": "LONG",
            "entry": 100,
            "qty": 1,
            "stop_loss": "DO-NOT-REFLECT",
        },
        {
            "ticker": "AAPL",
            "direction": "LONG",
            "entry": float("nan"),
            "qty": 1,
        },
        {
            "ticker": "AAPL",
            "direction": "LONG",
            "entry": 100,
            "qty": float("inf"),
        },
        {
            "ticker": "AAPL",
            "direction": "LONG",
            "entry": 100,
            "qty": 1,
            "target": float("inf"),
        },
    ],
)
def test_add_trade_does_not_return_conversion_errors(monkeypatch, tmp_path, payload):
    client = configure_temp_store(monkeypatch, tmp_path)

    response = client.post("/api/trades", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid trade payload."}
    assert b"DO-NOT-REFLECT" not in response.data


@pytest.mark.parametrize(
    "payload",
    [{}, None, {"exit": "DO-NOT-REFLECT"}, {"exit": float("nan")}, {"exit": float("inf")}],
)
def test_update_trade_does_not_return_conversion_errors(monkeypatch, tmp_path, payload):
    client = configure_temp_store(monkeypatch, tmp_path)
    assert add_trade(client, "2026-09-28", "AAPL", 100, None).status_code == 201
    trade_id = client.get("/api/trades").get_json()[0]["id"]

    response = client.put(f"/api/trades/{trade_id}", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid exit payload."}
    assert b"DO-NOT-REFLECT" not in response.data


def test_valid_trade_create_and_update_remain_available(monkeypatch, tmp_path):
    client = configure_temp_store(monkeypatch, tmp_path)
    create_response = add_trade(client, "2026-09-28", "AAPL", 100, None)
    trade_id = client.get("/api/trades").get_json()[0]["id"]

    update_response = client.put(
        f"/api/trades/{trade_id}",
        json={"exit": 110, "notes": "closed normally"},
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.get_json() == {"status": "ok", "pnl": 10.0, "result": "WIN"}
