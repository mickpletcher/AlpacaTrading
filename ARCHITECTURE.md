<!-- markdownlint-disable MD013 MD024 MD060 -->

# Architecture

## System Overview

AlpacaTrading is a repository of related but independently executable trading tools. It is not one deployable service. PowerShell modules provide a paper-only Alpaca client. Python applications provide strategy research, paper-only execution, journaling, scheduling, and webhook-triggered paper orders.

For a beginner, think of the repository as a toolbox. Each top-level folder is a different tool. Installing the repository does not start every tool, and running one tool does not automatically start the others.

Evidence: `src/Alpaca.*`, `Alpaca/`, `Backtesting/`, `Journal/`, `Scheduler/`, `rsi_macd_bot/`, `btc-signal-executor/`.

## Major Components

| Component | Responsibility | Evidence |
|---|---|---|
| PowerShell modules | Configuration, authentication, market data, orders, positions, streams, and risk | `src/Alpaca.*/*.psm1` |
| Alpaca scripts | Direct paper account commands and an EMA bot entry point | `Alpaca/alpaca_paper.py`, `Alpaca/alpaca_paper.ps1`, `Alpaca/paper_trade.py` |
| Backtesting | Fixed-data reproducible evaluation, online historical exploration, and one-shot execution runners | `Backtesting/reproducible_backtest.py`, `Backtesting/evaluation-config.json`, `Backtesting/strategies/` |
| Journal | Local Flask UI, SQLite trade storage, explicit CSV interchange, and HTML reporting | `Journal/journal_server.py`, `Journal/journal_store.py`, `Journal/analyze_journal.py` |
| Scheduler | Windows and shell launchers around existing scripts | `Scheduler/run_strategy.ps1`, `Scheduler/run_strategy.sh` |
| Operations | Local health evaluation for stale data, rejected orders, missing stops, circuit-breaker state, and scheduler failures | `Operations/health.py`, `Operations/health-config.example.json` |
| RSI and MACD bot | Scheduled multi-symbol Python bot with position sizing and stop orders | `rsi_macd_bot/bot.py`, `rsi_macd_bot/order_manager.py` |
| BTC executor | FastAPI webhook that converts inbound signals into Alpaca orders | `btc-signal-executor/main.py`, `btc-signal-executor/executor.py` |
| Validation | Python pytest and PowerShell Pester suites | `Tests/test_*.py`, `Tests/*.Tests.ps1` |
| Release | Locked validation, changelog consolidation, tagging, pushing, and GitHub release creation | `requirements.lock.txt`, `scripts/Invoke-ReleaseValidation.ps1`, `scripts/New-Release.ps1` |
| Repository delivery | Protected pull requests, required CI and CodeQL, squash-only merges, and protected release tags | `.github/workflows/ci.yml`, `SECURITY.md`, `docs/decisions/002-github-repository-hardening.md` |

## Application Entry Points

- `Backtesting/reproducible_backtest.py` runs the fixed-data comparison baseline. `Backtesting/backtest.py` remains an online Yahoo Finance exploration path.
- `Operations/health.py` creates local JSON and HTML status reports without mutating the paper account.
- `Alpaca/paper_trade.py` starts the command-oriented Alpaca helper and defaults to its bot mode when no argument is supplied.
- `Journal/journal_server.py` starts the local journal on Flask's default loopback interface.
- `rsi_macd_bot/bot.py` starts a five-minute scanning loop.
- `btc-signal-executor/main.py` exposes `/health` and `/webhook` through FastAPI.
- `Scheduler/run_strategy.ps1` and `Scheduler/run_strategy.sh` launch `Alpaca/paper_trade.py`.

Evidence: the `if __name__ == "__main__"` blocks in the named Python files and the process launch commands in `Scheduler/`.

## Data Flow

Historical data comes from a checksum-protected local dataset, Yahoo Finance, or Alpaca and feeds strategy logic. The reproducible evaluator selects parameters on training data and reports fixed out-of-sample and walk-forward results after configured costs. A backtest stops after calculating historical results. A paper execution runner can submit an order through `Alpaca/trading_safety.py`. SQLite is authoritative for the browser journal. CSV remains an explicit import and generated export format. The BTC webhook also uses a separate SQLite database to remember accepted signal identifiers and reject replays. Strategy and journal workflows write local HTML, JSON, log, and text artifacts.

Evidence: `Backtesting/backtest.py`, `Backtesting/strategies/backtest_*.py`, `Journal/journal_store.py`, `Journal/journal_server.py`.

## External Integrations

- Alpaca Trading and Market Data APIs.
- Yahoo Finance through `yfinance`.
- TradingView-compatible webhook payloads received by the BTC executor.

Evidence: `requirements.txt`, `Alpaca/alpaca_paper.py`, `Backtesting/backtest.py`, `btc-signal-executor/README.md`.

## Data Storage

The repository uses ignored, file-backed local state. `Journal/trades.db` stores browser journal records. `btc-signal-executor/runtime/webhook_state.db` stores accepted webhook identifiers. `Operations/runtime/` holds generated health reports and alert history. `Backtesting/output/` holds generated evaluation reports. CSV is an interchange format and strategy output. JSON and lock files hold safety state. Text and HTML files hold logs and reports. These files contain user or runtime data and do not belong in Git.

Evidence: `Journal/journal_store.py`, `src/Alpaca.Risk/Alpaca.Risk.psm1`, `Alpaca/circuit_breaker.py`.

Resolved storage and runtime-artifact changes are recorded under Upgrade 004 in `upgrades/README.md`.

## Configuration and Safety Boundary

Credentials are loaded from environment variables or ignored `.env` files. The PowerShell modules hard-code paper endpoints and enforce `Assert-PaperMode`. Python SDK execution uses `PaperTradingClient`, which creates an Alpaca paper client and rechecks the exact paper endpoint immediately before mutations. Direct Python REST execution uses the same endpoint assertion.

Evidence: `.env.example`, `src/Alpaca.Config/Alpaca.Config.psm1`, `Alpaca/trading_safety.py`, `Backtesting/strategies/live_*.py`, `rsi_macd_bot/config.py`, `btc-signal-executor/main.py`.

Live Python execution is unavailable. A live boundary would require a separate Class 4 decision.

## Error Handling and Observability

PowerShell REST calls implement bounded retries. Python execution surfaces use a mix of local retry helpers, broad exception handling, and immediate failure. Observability is local console output, file logging, scheduler status JSON, and a local health report. Alerting remains local. There is no hosted monitoring service.

Evidence: `src/Alpaca.Auth/Alpaca.Auth.psm1`, `Alpaca/circuit_breaker.py`, `rsi_macd_bot/logger.py`, `btc-signal-executor/main.py`, `Scheduler/run_strategy.ps1`.

## Significant Dependencies

The primary Python dependencies are `alpaca-py`, pandas, NumPy, requests, Flask, FastAPI, backtesting.py, Backtrader, and yfinance. `requirements.lock.txt` locks the full Python dependency graph for Python 3.13 development, CI, and releases. PowerShell validation uses Pester and PSScriptAnalyzer installed by CI.

Evidence: `requirements.txt`, `rsi_macd_bot/requirements.txt`, `btc-signal-executor/requirements.txt`, `.github/workflows/ci.yml`.

## Architectural Constraints

- The repository intentionally retains separate Python and PowerShell implementations.
- Top-level feature folders are stable boundaries.
- Python and PowerShell order paths are restricted to the exact Alpaca paper endpoint. Live execution is unavailable.
- `Tests/` is the current canonical mixed-language test directory.
- Changes to `main` flow through pull requests with strict required checks and linear squash history. Tags matching `v*` cannot be updated or deleted.

Evidence: `AGENTS.md`, `README.md`, `pytest.ini`, `docs/decisions/002-github-repository-hardening.md`, and the live GitHub readback recorded in `docs/repo-audit.md`.

## Architectural Decisions

See `docs/decisions/README.md`.

## Known Architectural Limitations

- The RSI plus MACD bot does not yet manage entry, protection, and exit orders as one lifecycle. See BUG-007.
- The BTC executor validates notional against the signal price instead of an authoritative execution quote. See BUG-008.
- The local journal renders some stored values as HTML. See BUG-009.
- Reproducible evaluation currently covers only the fixed EMA baseline. PowerShell warning control remains technical debt.

## Planned Evolution

Current proposals are maintained in `FUTURE-UPGRADES.md`. The reproducible evaluation, local health, coverage, dependency-lock, screenshot, and release foundations are recorded under Upgrade 005 in `upgrades/README.md`.

<!-- markdownlint-enable MD013 MD024 MD060 -->
