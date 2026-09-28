<!-- markdownlint-disable MD013 MD024 MD060 -->

# Architecture

## System Overview

AlpacaTrading is a repository of related but independently executable trading tools. It is not one deployable service. PowerShell modules provide a paper-only Alpaca client, while Python applications provide strategy research, paper or configurable execution, journaling, scheduling, and webhook-triggered orders.

Evidence: `src/Alpaca.*`, `Alpaca/`, `Backtesting/`, `Journal/`, `Scheduler/`, `rsi_macd_bot/`, `btc-signal-executor/`.

## Major Components

| Component | Responsibility | Evidence |
|---|---|---|
| PowerShell modules | Configuration, authentication, market data, orders, positions, streams, and risk | `src/Alpaca.*/*.psm1` |
| Alpaca scripts | Direct paper account commands and an EMA bot entry point | `Alpaca/alpaca_paper.py`, `Alpaca/alpaca_paper.ps1`, `Alpaca/paper_trade.py` |
| Backtesting | Historical strategy evaluation and one-shot execution runners | `Backtesting/backtest.py`, `Backtesting/strategies/` |
| Journal | Local Flask UI, SQLite storage, CSV interchange, and HTML reporting | `Journal/journal_server.py`, `Journal/journal_store.py`, `Journal/analyze_journal.py` |
| Scheduler | Windows and shell launchers around existing scripts | `Scheduler/run_strategy.ps1`, `Scheduler/run_strategy.sh` |
| RSI and MACD bot | Scheduled multi-symbol Python bot with position sizing and stop orders | `rsi_macd_bot/bot.py`, `rsi_macd_bot/order_manager.py` |
| BTC executor | FastAPI webhook that converts inbound signals into Alpaca orders | `btc-signal-executor/main.py`, `btc-signal-executor/executor.py` |
| Validation | Python pytest and PowerShell Pester suites | `Tests/test_*.py`, `Tests/*.Tests.ps1` |

## Application Entry Points

- `Backtesting/backtest.py` runs a Yahoo Finance based strategy comparison.
- `Alpaca/paper_trade.py` starts the command-oriented Alpaca helper and defaults to its bot mode when no argument is supplied.
- `Journal/journal_server.py` starts the local journal on Flask's default loopback interface.
- `rsi_macd_bot/bot.py` starts a five-minute scanning loop.
- `btc-signal-executor/main.py` exposes `/health` and `/webhook` through FastAPI.
- `Scheduler/run_strategy.ps1` and `Scheduler/run_strategy.sh` launch `Alpaca/paper_trade.py`.

Evidence: the `if __name__ == "__main__"` blocks in the named Python files and the process launch commands in `Scheduler/`.

## Data Flow

Historical data comes from Yahoo Finance or Alpaca and feeds strategy logic. Execution runners submit paper orders through `Alpaca/trading_safety.py`. SQLite is authoritative for the browser journal. CSV remains an explicit import and generated export format. Strategy and journal workflows also write local HTML, JSON, and text artifacts.

Evidence: `Backtesting/backtest.py`, `Backtesting/strategies/backtest_*.py`, `Journal/journal_store.py`, `Journal/journal_server.py`.

## External Integrations

- Alpaca Trading and Market Data APIs.
- Yahoo Finance through `yfinance`.
- TradingView-compatible webhook payloads received by the BTC executor.

Evidence: `requirements.txt`, `Alpaca/alpaca_paper.py`, `Backtesting/backtest.py`, `btc-signal-executor/README.md`.

## Data Storage

The repository uses ignored, file-backed local state. SQLite stores journal records and persistent BTC replay identifiers. CSV is an interchange format and strategy output. JSON and lock files hold safety state. Text and HTML files hold logs and reports.

Evidence: `Journal/journal_store.py`, `src/Alpaca.Risk/Alpaca.Risk.psm1`, `Alpaca/circuit_breaker.py`.

Resolved storage and runtime-artifact changes are recorded under Upgrade 004 in `upgrades/README.md`.

## Configuration and Safety Boundary

Credentials are loaded from environment variables or ignored `.env` files. The PowerShell modules hard-code paper endpoints and enforce `Assert-PaperMode`. Python SDK execution uses `PaperTradingClient`, which creates an Alpaca paper client and rechecks the exact paper endpoint immediately before mutations. Direct Python REST execution uses the same endpoint assertion.

Evidence: `.env.example`, `src/Alpaca.Config/Alpaca.Config.psm1`, `Alpaca/trading_safety.py`, `Backtesting/strategies/live_*.py`, `rsi_macd_bot/config.py`, `btc-signal-executor/main.py`.

Live Python execution is unavailable. A live boundary would require a separate Class 4 decision.

## Error Handling and Observability

PowerShell REST calls implement bounded retries. Python execution surfaces use a mix of local retry helpers, broad exception handling, and immediate failure. Observability is local console output and file logging. There is no centralized monitoring or alerting.

Evidence: `src/Alpaca.Auth/Alpaca.Auth.psm1`, `Alpaca/circuit_breaker.py`, `rsi_macd_bot/logger.py`, `btc-signal-executor/main.py`, `Scheduler/run_strategy.ps1`.

## Significant Dependencies

The primary Python dependencies are `alpaca-py`, pandas, NumPy, requests, Flask, FastAPI, backtesting.py, Backtrader, and yfinance. PowerShell validation uses Pester and PSScriptAnalyzer installed by CI.

Evidence: `requirements.txt`, `rsi_macd_bot/requirements.txt`, `btc-signal-executor/requirements.txt`, `.github/workflows/ci.yml`.

## Architectural Constraints

- The repository intentionally retains separate Python and PowerShell implementations.
- Top-level feature folders are stable boundaries.
- Paper trading is the documented default, but Python live switches remain reachable.
- `Tests/` is the current canonical mixed-language test directory.

Evidence: `AGENTS.md`, `README.md`, `pytest.ini`.

## Architectural Decisions

See `docs/decisions/README.md`.

## Known Architectural Limitations

See `ISSUES.md` and `TECH-DEBT.md`.

## Planned Evolution

- FU-002: reproducible strategy evaluation pipeline.
- FU-003: operational status and alerting.

<!-- markdownlint-enable MD013 MD024 MD060 -->
