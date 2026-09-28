<!-- markdownlint-disable MD013 MD024 MD060 -->

# Operations

## Operating Boundary

Treat every execution surface as paper trading only. Python and PowerShell execution now fail closed unless the exact Alpaca paper boundary is active. Live operation is not implemented or approved.

## Runtime Environment

- Windows 11 and PowerShell 7 are the primary local environment.
- CI uses Windows and Python 3.13.
- Root Python dependencies support the shared backtesting, journal, and test workflows.
- `rsi_macd_bot/` and `btc-signal-executor/` have separate requirement files.

Setup and first-run commands remain in `README.md`. Component-specific commands remain in each component README.

## Configuration and Secrets

Copy `.env.example` to an ignored `.env` file. Keep Alpaca paper credentials and webhook passphrases out of Git. Use separate paper credentials for testing. Rotate a secret immediately if it appears in logs, a commit, or terminal output shared outside the machine.

The PowerShell modules use environment variables and a paper-only configuration object. Python applications load credentials independently but share `Alpaca/trading_safety.py` for the execution boundary.

Evidence: `.env.example`, `.gitignore`, `src/Alpaca.Config/Alpaca.Config.psm1`, `btc-signal-executor/config.py`, `rsi_macd_bot/bot.py`.

## Manual Startup

### Backtesting

```powershell
python .\Backtesting\backtest.py
```

See `Backtesting/README.md` for strategy-specific runs.

### Journal

```powershell
python .\Journal\journal_server.py
```

Open `http://localhost:5000`. Do not expose the journal outside the local machine.

### Generic paper bot

```powershell
python .\Alpaca\paper_trade.py
```

### RSI and MACD bot

```powershell
python -m pip install -r .\rsi_macd_bot\requirements.txt
python .\rsi_macd_bot\bot.py
```

Keep `PAPER=true`.

### BTC webhook executor

Install `btc-signal-executor/requirements.txt`, configure the documented quantity, notional, loss, freshness, rate, failure, and replay settings, then start the service through the component README. Keep it on a paper account and behind controlled TLS ingress. Do not publish the Uvicorn port directly.

## Scheduling and Triggers

The scheduler scripts launch `Alpaca/paper_trade.py` and load the root `.env` file. Windows Task Scheduler and cron examples are maintained in `Scheduler/README.md`.

Before registering a task:

1. Run the exact command manually under the intended account.
2. Confirm paper credentials.
3. Confirm the log location is writable.
4. Confirm the machine time zone against the intended market schedule.

## Monitoring

There is no centralized monitoring or alerting.

Review these local outputs:

- `Journal/scheduler_log.txt`
- `Journal/circuit_log.txt`
- strategy-specific `Journal/live_*_log.txt` files
- `rsi_macd_bot/trades.log`
- `btc-signal-executor/executor.log`
- the Alpaca paper account order and position views

Runtime artifacts are ignored by Git and remain local.

## Safe Stop and Recovery

1. Stop the local process or scheduled task.
2. Disable its scheduler trigger before debugging.
3. Review open orders and positions in the Alpaca paper dashboard.
4. Cancel unexpected paper orders from the dashboard or the paper-only PowerShell functions.
5. Preserve logs and state files before attempting repair.
6. Do not clear a kill switch until the trigger is understood and positions have been reviewed.

## Rollback

Runtime scripts are not deployed through an automated release system. Roll back code through Git to a previously validated commit, reinstall the matching dependencies in a clean virtual environment, rerun the applicable validation, and only then restart paper execution.

Do not restore `Journal/trades.db` or risk-state files from another checkout without understanding the data loss and safety implications.

## Common Failure Modes

| Symptom | Likely cause | Response |
|---|---|---|
| Missing credential error | `.env` absent or task account cannot read it | Stop, verify the ignored file and task account |
| Authentication 401 or 403 | Wrong credential set or account permissions | Stop retries, rotate or correct paper credentials |
| Circuit breaker blocks execution | Market closed, loss threshold, API failure, or saved pause | Inspect `Journal/circuit_log.txt` and state before reset |
| Scheduler reports success but no trade | No qualifying signal or bot waiting for market open | Review stdout, strategy logs, and paper account activity |
| Journal CSV row is absent from the app | CSV import is explicit | Stop the server and run `python .\Journal\journal_server.py --import-csv` |
| BTC webhook returns execution failure | Risk control or Alpaca paper rejection | Review the redacted executor log, paper account, and configured limit |

## Maintenance

Run the validation authority before restarting changed automation. Run `scripts/docs-check.ps1` during monthly maintenance. Review active defects, debt, and future upgrades quarterly.

<!-- markdownlint-enable MD013 MD024 MD060 -->
