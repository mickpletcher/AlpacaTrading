"""
=============================================================
  Day Trading Journal — Backend (Flask + SQLite)
  
  Usage:
    pip install flask --break-system-packages
    python journal_server.py
    Open http://localhost:5000 in your browser

  Features:
    - Log trades with full details
    - Track P&L automatically
    - Win rate, avg R:R, streak tracking
    - AI analysis prompt generator
    - Export to CSV
=============================================================
"""

from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import csv
import io
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder=".")
DB_PATH = "trades.db"


# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            direction   TEXT NOT NULL,   -- LONG or SHORT
            entry       REAL NOT NULL,
            exit        REAL,
            qty         INTEGER NOT NULL,
            stop_loss   REAL,
            target      REAL,
            pnl         REAL,
            result      TEXT,            -- WIN / LOSS / BREAKEVEN / OPEN
            setup       TEXT,            -- EMA Cross, VWAP, ORB, etc.
            timeframe   TEXT,            -- 1m, 5m, 15m, etc.
            emotion     TEXT,            -- Calm, Anxious, FOMO, Revenge, etc.
            mistake     TEXT,            -- What went wrong (if anything)
            lesson      TEXT,            -- What you learned
            notes       TEXT,
            screenshot  TEXT,            -- File path or URL
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def calc_pnl(direction, entry, exit_price, qty):
    if not exit_price:
        return None
    mult = 1 if direction == "LONG" else -1
    return round(mult * (exit_price - entry) * qty, 2)


def calc_result(pnl):
    if pnl is None:
        return "OPEN"
    if pnl > 0:
        return "WIN"
    elif pnl < 0:
        return "LOSS"
    return "BREAKEVEN"


def calc_rr(entry, stop_loss, target, direction):
    """Calculate Risk:Reward ratio."""
    if not stop_loss or not target:
        return None
    mult = 1 if direction == "LONG" else -1
    risk   = abs(entry - stop_loss)
    reward = mult * (target - entry)
    if risk == 0:
        return None
    return round(reward / risk, 2)


# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route("/api/trades", methods=["GET"])
def get_trades():
    conn = get_db()
    trades = conn.execute(
        "SELECT * FROM trades ORDER BY date DESC, created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(t) for t in trades])


@app.route("/api/trades", methods=["POST"])
def add_trade():
    data = request.json
    entry      = float(data["entry"])
    exit_price = float(data["exit"]) if data.get("exit") else None
    qty        = int(data["qty"])
    direction  = data["direction"]
    stop_loss  = float(data["stop_loss"]) if data.get("stop_loss") else None
    target     = float(data["target"]) if data.get("target") else None

    pnl    = calc_pnl(direction, entry, exit_price, qty)
    result = calc_result(pnl)

    conn = get_db()
    conn.execute("""
        INSERT INTO trades
          (date, ticker, direction, entry, exit, qty, stop_loss, target,
           pnl, result, setup, timeframe, emotion, mistake, lesson, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("date", datetime.now().strftime("%Y-%m-%d")),
        data["ticker"].upper(),
        direction,
        entry,
        exit_price,
        qty,
        stop_loss,
        target,
        pnl,
        result,
        data.get("setup", ""),
        data.get("timeframe", ""),
        data.get("emotion", ""),
        data.get("mistake", ""),
        data.get("lesson", ""),
        data.get("notes", "")
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "pnl": pnl, "result": result}), 201


@app.route("/api/trades/<int:trade_id>", methods=["PUT"])
def update_trade(trade_id):
    """Close an open trade by adding exit price."""
    data       = request.json
    exit_price = float(data["exit"])

    conn  = get_db()
    trade = conn.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
    if not trade:
        return jsonify({"error": "Not found"}), 404

    pnl    = calc_pnl(trade["direction"], trade["entry"], exit_price, trade["qty"])
    result = calc_result(pnl)

    conn.execute("""
        UPDATE trades SET exit=?, pnl=?, result=?, mistake=?, lesson=?, notes=?
        WHERE id=?
    """, (
        exit_price, pnl, result,
        data.get("mistake", trade["mistake"]),
        data.get("lesson", trade["lesson"]),
        data.get("notes", trade["notes"]),
        trade_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "pnl": pnl, "result": result})


@app.route("/api/trades/<int:trade_id>", methods=["DELETE"])
def delete_trade(trade_id):
    conn = get_db()
    conn.execute("DELETE FROM trades WHERE id=?", (trade_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn   = get_db()
    trades = conn.execute("SELECT * FROM trades WHERE result != 'OPEN'").fetchall()
    conn.close()

    if not trades:
        return jsonify({"message": "No closed trades yet."})

    trades    = [dict(t) for t in trades]
    total     = len(trades)
    wins      = [t for t in trades if t["result"] == "WIN"]
    losses    = [t for t in trades if t["result"] == "LOSS"]
    total_pnl = sum(t["pnl"] for t in trades if t["pnl"] is not None)
    win_rate  = len(wins) / total * 100 if total else 0

    avg_win  = sum(t["pnl"] for t in wins)  / len(wins)  if wins   else 0
    avg_loss = sum(t["pnl"] for t in losses)/ len(losses) if losses else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else None

    # Streak
    streak = 0
    streak_type = None
    for t in reversed(trades):
        if streak_type is None:
            streak_type = t["result"]
            streak = 1
        elif t["result"] == streak_type:
            streak += 1
        else:
            break

    # Common mistakes
    mistakes = [t["mistake"] for t in trades if t.get("mistake")]
    emotion_map = {}
    for t in trades:
        e = t.get("emotion", "") or "Unknown"
        emotion_map[e] = emotion_map.get(e, 0) + 1

    # Setup performance
    setup_map = {}
    for t in trades:
        s = t.get("setup", "Unknown") or "Unknown"
        if s not in setup_map:
            setup_map[s] = {"wins": 0, "losses": 0, "pnl": 0}
        setup_map[s]["pnl"] += t["pnl"] or 0
        if t["result"] == "WIN":
            setup_map[s]["wins"] += 1
        elif t["result"] == "LOSS":
            setup_map[s]["losses"] += 1

    return jsonify({
        "total_trades":   total,
        "win_rate":       round(win_rate, 1),
        "total_pnl":      round(total_pnl, 2),
        "avg_win":        round(avg_win, 2),
        "avg_loss":       round(avg_loss, 2),
        "profit_factor":  round(profit_factor, 2) if profit_factor else "N/A",
        "current_streak": {"type": streak_type, "count": streak},
        "emotion_breakdown": emotion_map,
        "setup_performance": setup_map,
    })


@app.route("/api/export", methods=["GET"])
def export_csv():
    conn   = get_db()
    trades = conn.execute("SELECT * FROM trades ORDER BY date").fetchall()
    conn.close()

    output = io.StringIO()
    if trades:
        writer = csv.DictWriter(output, fieldnames=dict(trades[0]).keys())
        writer.writeheader()
        writer.writerows([dict(t) for t in trades])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=trade_journal.csv"}
    )


@app.route("/api/ai_prompt", methods=["GET"])
def ai_analysis_prompt():
    """Generate a prompt you can paste into Claude to analyze your trading."""
    conn   = get_db()
    trades = conn.execute(
        "SELECT * FROM trades WHERE result != 'OPEN' ORDER BY date DESC LIMIT 30"
    ).fetchall()
    conn.close()

    trades = [dict(t) for t in trades]
    if not trades:
        return jsonify({"prompt": "No trades to analyze yet."})

    total_pnl = sum(t["pnl"] for t in trades if t["pnl"])
    wins      = len([t for t in trades if t["result"] == "WIN"])
    losses    = len([t for t in trades if t["result"] == "LOSS"])

    prompt = f"""You are a professional trading coach analyzing my recent trade journal.

Here are my last {len(trades)} trades:

{chr(10).join([
    f"Date: {t['date']} | {t['ticker']} {t['direction']} | Setup: {t['setup']} | "
    f"Entry: ${t['entry']} | Exit: ${t['exit'] or 'OPEN'} | P&L: ${t['pnl']} | "
    f"Result: {t['result']} | Emotion: {t['emotion']} | Mistake: {t['mistake']}"
    for t in trades
])}

Summary:
- Total P&L: ${total_pnl:.2f}
- Win/Loss: {wins}W / {losses}L
- Win Rate: {wins/(wins+losses)*100:.1f}% if wins+losses > 0 else N/A

Please analyze:
1. What patterns do you see in my winning vs losing trades?
2. Which setups are working best and worst?
3. What emotional patterns are hurting my performance?
4. What are my top 3 mistakes and how do I fix them?
5. What is ONE specific rule I should add to my trading plan this week?
"""

    return jsonify({"prompt": prompt})


@app.route("/")
def index():
    return send_from_directory(".", "journal.html")


if __name__ == "__main__":
    init_db()
    print("\n📓 Trade Journal running at http://localhost:5000")
    print("   Press Ctrl+C to stop.\n")
    app.run(debug=False, port=5000)
