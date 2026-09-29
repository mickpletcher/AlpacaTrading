<!-- markdownlint-disable MD013 MD024 MD060 -->

# Operations

This guide explains how to start, watch, stop, and recover the repository's tools. Use the root `README.md` for first-time installation.

## Non-Negotiable Boundary

Every order path is paper-only. Paper orders use simulated money, but they still create positions and open orders in the Alpaca paper account.

Live trading is unavailable. Do not change URLs, flags, or code to work around that boundary.

## Before Starting Any Tool

1. Open PowerShell in the repository root.
2. Activate `.venv` or use `.venv\Scripts\python.exe` directly.
3. Read `ISSUES.md` for the tool you plan to run.
4. Confirm `.env` contains paper credentials only.
5. Confirm `ALPACA_BASE_URL=https://paper-api.alpaca.markets` and `PAPER=true`.
6. Run the tool manually before adding a schedule.
7. Open the Alpaca paper dashboard so you can inspect orders and positions.

## Secrets and Local Data

Copy `.env.example` to `.env`. Git ignores `.env`.

Never commit or share:

- API keys or webhook passphrases
- real account identifiers
- `Journal/trades.db` or journal CSV exports
- webhook replay databases
- logs, risk state, or lock files

If a secret appears in Git, a screenshot, a shared terminal log, or an issue, rotate it immediately. Deleting the visible text is not enough because Git history may retain it.

## Start the Read-Only Tools First

### Historical backtest

```powershell
.\.venv\Scripts\python.exe .\Backtesting\reproducible_backtest.py
```

This validates a fixed local dataset and calculates repeatable results. It does not use credentials, make a network request, or submit an order.

### Local journal

```powershell
.\.venv\Scripts\python.exe .\Journal\journal_server.py
```

Open `http://127.0.0.1:5000`. Keep the service local. While BUG-009 is open, do not import CSV data from an untrusted source.

## Paper-Order Tools

These tools can change the Alpaca paper account.

### Generic paper helper

```powershell
.\.venv\Scripts\python.exe .\Alpaca\paper_trade.py
```

Read the command output before leaving it running. With no arguments, this entry point starts its bot mode.

### Strategy paper runners

Use the commands in `Backtesting/README.md`. Files named `live_*.py` are legacy names. The shared safety boundary restricts them to paper trading.

### RSI plus MACD bot

```powershell
.\.venv\Scripts\python.exe .\rsi_macd_bot\bot.py
```

> [!CAUTION]
> BUG-007 is open. Do not run this bot unattended. After each execution test, review both positions and open orders in Alpaca.

### BTC webhook executor

Use `btc-signal-executor/README.md` for configuration and startup.

> [!CAUTION]
> BUG-008 is open. The quantity limit is enforced, but the configured maximum notional is calculated from the signal price rather than a broker quote. Use a conservative quantity cap and supervise paper tests.

Keep Uvicorn behind controlled TLS ingress. Do not publish its port directly to the internet.

## Scheduling

The generic scheduler launches `Alpaca/paper_trade.py` and loads the root `.env` file. Windows Task Scheduler and cron examples are in `Scheduler/README.md`.

Before registering a task:

1. Run the exact command manually under the same user account.
2. Confirm the command exits or stays running as expected.
3. Confirm the account can read `.env` and write the log directory.
4. Confirm the host time zone and the intended market time.
5. Write down how to disable the task.

Do not schedule the RSI plus MACD bot while BUG-007 is open.

## What to Monitor

Run the local health check from the repository root:

```powershell
.\.venv\Scripts\python.exe .\Operations\health.py
```

The command writes `Operations/runtime/health-status.json`, `health-report.html`, and `health-alerts.log`. Open the HTML file in a browser for a local status view. Exit code `0` means all configured checks passed, `1` means at least one warning or unknown result, and `2` means at least one failure. `UNKNOWN` means the required local evidence or optional paper credentials were absent.

The default configuration is `Operations/health-config.example.json`. Copy it to a local ignored file and pass `--config` when you need different paths or age limits.

Review both the local health report and the Alpaca paper account.

| Item | Location or check |
| --- | --- |
| Scheduler result | `Journal/scheduler_status.json` and `Journal/scheduler_log.txt` |
| Circuit-breaker events | `Journal/circuit_log.txt` |
| Strategy decisions | `Journal/live_*_log.txt` |
| RSI plus MACD events | `rsi_macd_bot/trades.log` |
| BTC webhook decisions | `btc-signal-executor/executor.log` |
| Actual paper orders | Alpaca paper dashboard, Orders |
| Actual paper holdings | Alpaca paper dashboard, Positions |

An exit code of zero means the process finished without reporting an execution error. It does not prove that a trade occurred or that the strategy behaved correctly.

## Normal Stop

1. Press `Ctrl+C` in the process window.
2. Disable any Windows task, cron entry, service, or tunnel that can restart it.
3. Confirm the process is no longer running.
4. Review open orders and positions in Alpaca.
5. Preserve logs before changing configuration.

Stopping a local process does not automatically cancel an order already accepted by Alpaca.

## Unexpected Order or Position

1. Stop the process.
2. Disable its schedule or service.
3. Open the Alpaca paper dashboard.
4. Cancel unexpected open orders.
5. Review positions separately. Cancelling an order does not close a position.
6. Preserve logs and state files.
7. Identify the trigger before restarting.

Do not clear a kill switch only to make the bot run again. First understand why it activated.

## Rollback

There is no automated deployment package. To roll back safely:

1. Stop the affected process and disable its schedule.
2. Review paper orders and positions.
3. Select a previously validated Git commit.
4. Rebuild the virtual environment from that commit's requirement files.
5. Run the validation in `Tests/README.md`.
6. Restart manually before restoring a schedule.

Do not copy `Journal/trades.db`, replay databases, or risk-state files between checkouts unless you understand which newer records would be lost.

## Common Failures

| Symptom | Likely cause | Response |
| --- | --- | --- |
| Missing credential error | `.env` is absent or unreadable | Stop and correct the local file or task account |
| Authentication 401 or 403 | Wrong credentials or permissions | Stop retries and verify paper credentials |
| Circuit breaker blocks execution | Market closure, loss threshold, API failure, or saved pause | Inspect the circuit log and paper account before reset |
| Scheduler reports success but no trade appears | No signal occurred or the market was closed | Review strategy output and paper account activity |
| Journal CSV row is absent from the browser app | CSV import is explicit | Stop the server and run `journal_server.py --import-csv` |
| BTC webhook returns `success: false` with HTTP 200 | The service intentionally suppresses retries after execution failure | Review the executor log and paper account |
| Old package version is still installed | `.venv` predates a requirements update | Rebuild or refresh the virtual environment |

## Maintenance

Report suspected vulnerabilities through GitHub private vulnerability reporting. Do not open a public issue with exploit details, credentials, account identifiers, or private trading data. Scope, response expectations, and current limitations are defined in `SECURITY.md`.

- Run `Tests/README.md` validation before restarting changed automation.
- Run `scripts/docs-check.ps1 -FailOnGap` during documentation changes.
- Review `ISSUES.md`, `TECH-DEBT.md`, and `FUTURE-UPGRADES.md` before each release snapshot.
- Rebuild local environments from `requirements.lock.txt` after dependency changes are merged.

Regenerate the dependency lock after intentionally changing a direct requirement:

```powershell
pwsh -NoProfile -File .\scripts\Update-PythonLock.ps1
```

Run the complete release validation without publishing:

```powershell
pwsh -NoProfile -File .\scripts\Invoke-ReleaseValidation.ps1
```

Prepare a release only from a clean `main` branch. Omit `-Publish` to consolidate fragments locally for review. Add `-Publish` only when you intend to commit, tag, push, and create the GitHub release:

```powershell
pwsh -NoProfile -File .\scripts\New-Release.ps1 -Version 0.1.0
pwsh -NoProfile -File .\scripts\New-Release.ps1 -Version 0.1.0 -Publish
```

<!-- markdownlint-enable MD013 MD024 MD060 -->
