from __future__ import annotations

import csv
import hashlib
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
JOURNAL_DIR = ROOT_DIR / "Journal"
CSV_PATH = JOURNAL_DIR / "trades.csv"
DB_PATH = JOURNAL_DIR / "trades.db"
CSV_COLUMNS = ["date", "symbol", "side", "qty", "entry_price", "exit_price", "pnl", "notes"]


def ensure_csv_file() -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists():
        return
    with CSV_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()


def get_db_connection() -> sqlite3.Connection:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_trade_table(conn)
    return conn


def ensure_trade_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            direction   TEXT NOT NULL,
            entry       REAL NOT NULL,
            exit        REAL,
            qty         INTEGER NOT NULL,
            stop_loss   REAL,
            target      REAL,
            pnl         REAL,
            result      TEXT,
            setup       TEXT,
            timeframe   TEXT,
            emotion     TEXT,
            mistake     TEXT,
            lesson      TEXT,
            notes       TEXT,
            screenshot  TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            source      TEXT DEFAULT 'app',
            sync_key    TEXT
        )
        """
    )

    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(trades)").fetchall()}
    if "source" not in existing_columns:
        conn.execute("ALTER TABLE trades ADD COLUMN source TEXT DEFAULT 'app'")
    if "sync_key" not in existing_columns:
        conn.execute("ALTER TABLE trades ADD COLUMN sync_key TEXT")

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_trades_sync_key ON trades(sync_key) WHERE sync_key IS NOT NULL"
    )
    conn.commit()


def _format_decimal(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "0.0000"
    return f"{float(text):.4f}"


def _to_float(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    return float(text)


def _to_optional_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    return float(text)


def _to_int(value: object) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return int(float(text))


def normalize_csv_row(row: dict[str, object]) -> dict[str, str]:
    return {
        "date": str(row.get("date") or "").strip(),
        "symbol": str(row.get("symbol") or "").strip().upper(),
        "side": str(row.get("side") or "").strip().upper(),
        "qty": str(_to_int(row.get("qty"))),
        "entry_price": _format_decimal(row.get("entry_price")),
        "exit_price": _format_decimal(row.get("exit_price")),
        "pnl": _format_decimal(row.get("pnl")),
        "notes": str(row.get("notes") or "").strip(),
    }


def _build_sync_key(row: dict[str, str]) -> str:
    payload = "|".join(row[column] for column in CSV_COLUMNS)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _csv_row_to_trade_values(row: dict[str, str]) -> tuple[object, ...]:
    side = row["side"]
    exit_price = _to_float(row["exit_price"])
    pnl = _to_float(row["pnl"])
    is_open = side == "BUY" and exit_price == 0.0 and pnl == 0.0
    result = "OPEN" if is_open else ("WIN" if pnl > 0 else "LOSS" if pnl < 0 else "BREAKEVEN")
    notes = row["notes"]
    return (
        row["date"],
        row["symbol"],
        "LONG",
        _to_float(row["entry_price"]),
        None if is_open else _to_optional_float(row["exit_price"]),
        _to_int(row["qty"]),
        None,
        None,
        None if is_open else _to_optional_float(row["pnl"]),
        result,
        notes or "csv_sync",
        "imported_csv",
        "",
        "",
        "",
        notes,
        "",
        "csv",
        _build_sync_key(row),
    )


def sync_csv_to_sqlite(conn: sqlite3.Connection) -> None:
    ensure_csv_file()
    ensure_trade_table(conn)

    with CSV_PATH.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            return

        for raw_row in reader:
            row = normalize_csv_row(raw_row)
            if not row["date"] or not row["symbol"]:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO trades (
                    date, ticker, direction, entry, exit, qty, stop_loss, target,
                    pnl, result, setup, timeframe, emotion, mistake, lesson, notes,
                    screenshot, source, sync_key
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                _csv_row_to_trade_values(row),
            )

    conn.commit()


def sync_sqlite_to_csv(conn: sqlite3.Connection) -> None:
    ensure_csv_file()
    ensure_trade_table(conn)
    trades = conn.execute(
        "SELECT date, ticker, entry, exit, qty, pnl, result, notes, created_at, id FROM trades ORDER BY date, created_at, id"
    ).fetchall()

    with CSV_PATH.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for trade in trades:
            side = "BUY" if trade["result"] == "OPEN" or trade["exit"] is None else "SELL"
            writer.writerow(
                {
                    "date": trade["date"],
                    "symbol": trade["ticker"],
                    "side": side,
                    "qty": str(trade["qty"] or 0),
                    "entry_price": _format_decimal(trade["entry"]),
                    "exit_price": _format_decimal(trade["exit"]),
                    "pnl": _format_decimal(trade["pnl"]),
                    "notes": str(trade["notes"] or "").strip(),
                }
            )