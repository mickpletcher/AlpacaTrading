<!-- markdownlint-disable MD013 -->

# Journal Module

This folder helps you review what happened after a trade or a strategy run.

It includes a browser based journal, CSV exports, logs, and an HTML summary report.

> [!CAUTION]
> BUG-009 is open. Keep the journal on `127.0.0.1` and do not import CSV files from an untrusted source. Stored text is not yet rendered safely in every table.

## Related Repo Guides

- [Root README](../README.md)
- [Backtesting Guide](../Backtesting/README.md)
- [Scheduler Guide](../Scheduler/README.md)
- [Tests Guide](../Tests/README.md)
- [Learning Roadmap](../Learning%20Roadmap/README.md)
- [Applied Upgrades](../upgrades/README.md)
- [Core Trading Foundation Spec](../specs/001-core-trading-foundation/spec.md)

## Suggested Tutorials

### Tutorial 1: First Journal Launch

1. Complete the root setup in [README.md](../README.md).
2. Run `python .\Journal\journal_server.py`.
3. Add one manual sample trade and inspect the SQLite data and CSV export.

### Tutorial 2: Backtest To Report

1. Run a workflow from the [Backtesting Guide](../Backtesting/README.md).
2. Confirm `Journal/trades.csv` was updated.
3. Run `python .\Journal\analyze_journal.py`.

### Tutorial 3: Review Before Automation

1. Use this module to inspect outcomes after paper-trading or strategy runs.
2. Read the [Scheduler Guide](../Scheduler/README.md) only after you understand the journal output.
3. Use the [Applied Upgrades](../upgrades/README.md) log before changing repo structure.

## What This Folder Is For

Use this folder when you want to:

- manually log trades in a browser
- review win rate, average win, average loss, and setup performance
- export journal data to CSV
- generate a simple HTML report from the CSV journal used by strategy scripts
- inspect scheduler and circuit breaker logs

Do not use this folder when you want to:

- place orders directly
- backtest strategy logic
- configure the Windows scheduler itself

## Files and What They Do

| File | Purpose |
| --- | --- |
| `journal_server.py` | Flask backend for the browser based trade journal |
| `journal.html` | Front end for the trade journal app |
| `analyze_journal.py` | Reads `trades.csv`, prints summary stats, and writes `report.html` |
| `trades.csv` | CSV journal written by several strategy scripts |
| `report.html` | Generated HTML summary report from `analyze_journal.py` |
| `trades.db` | SQLite database used by the browser based journal app |
| `scheduler_log.txt` | Log of scheduled launches and exit codes |
| `circuit_log.txt` | Safety log written by the circuit breaker |

## Beginner Data Explanation

### What SQLite means here

SQLite is a small local database stored in a single file. You do not need a database server to use it.

In this repo, the browser journal app stores trades in `trades.db`.

### What CSV means here

CSV means comma separated values. It is a plain text table file that opens easily in Excel and other tools.

In this repo, several strategy scripts write trade rows to `trades.csv`. SQLite is authoritative for the browser journal. CSV data is imported only through the explicit import command.

### What report generation means here

`analyze_journal.py` reads the CSV journal, calculates basic summary statistics, and writes a static HTML file called `report.html`.

## Prerequisites

- Python virtual environment activated
- dependencies installed from `requirements.lock.txt`
- web browser available on your machine

## Setup Steps

1. Decide whether you want the SQLite browser journal, the separate CSV report flow, or both.
2. Launch `journal_server.py` from the repo root or from inside `Journal`. The database path is now anchored automatically.
3. If you want the CSV report flow, make sure `Journal/trades.csv` exists or let `analyze_journal.py` create a starter file.

## Run Commands

### Browser based journal app

```powershell
python .\Journal\journal_server.py
```

Then open:

```text
http://localhost:5000
```

Only use the journal from the same computer. Do not change the server to listen on every network interface.

For isolated testing, set `JOURNAL_DB_PATH`, `JOURNAL_CSV_PATH`, and `JOURNAL_PORT` before startup. This keeps test or demonstration records out of the normal journal files.

### CSV journal analysis report

```powershell
python .\Journal\analyze_journal.py
```

## Example Usage

### Example 1: Launch the journal app

```powershell
python .\Journal\journal_server.py
```

Expected output:

- Flask starts listening locally
- your browser loads the journal page
- adding a trade returns a success response and updates the visible table
- browser entries are written to SQLite and the current database is exported to `trades.csv`

### Example 2: Generate an HTML report from CSV data

```powershell
Set-Location ..
python .\Journal\analyze_journal.py
```

Expected output:

```text
Total trades: ...
Win rate: ...
Total P&L: ...
HTML report written to ...\Journal\report.html
```

## What the Browser Journal Tracks

The journal app supports fields such as:

- date
- ticker
- direction
- entry and exit
- quantity
- stop loss and target
- P and L
- result
- setup
- timeframe
- emotion
- mistake
- lesson
- notes

It also exposes routes for:

- listing trades
- adding trades
- updating an open trade with an exit price
- deleting a trade
- exporting CSV
- generating a prompt for external AI review

## SQLite and CSV flow

The journal uses both storage formats, but they no longer drift as easily.

Current behavior:

1. The browser app writes trades into `trades.db`.
2. After browser adds, edits, or deletes, the app rewrites `trades.csv` as an export.
3. Strategy CSV rows do not enter SQLite automatically.
4. Stop the server and run `python .\Journal\journal_server.py --import-csv` to import CSV rows explicitly and idempotently.

This avoids two active data authorities and prevents an exported database row from being imported as a duplicate.

## AI Prompt Workflow

The current journal app does not call an AI model directly.

Instead it builds a prompt from your recent trades so you can paste it into your preferred model manually.

Typical flow:

1. log several trades
2. use the AI prompt feature in the journal UI
3. copy the generated prompt
4. paste it into your external AI tool
5. review the suggested coaching ideas critically, not blindly

## Common Mistakes

- assuming strategy CSV rows are imported automatically
- expecting the AI prompt feature to call Anthropic directly
- treating journal stats as enough evidence to trade live
- importing a CSV received from an untrusted person or website while BUG-009 is open

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| browser journal starts but no file appears in `Journal/` | the app has not written any data yet | add a trade or open the export route |
| `report.html` looks stale | `analyze_journal.py` was not rerun | rerun the analysis script after updating `trades.csv` |
| strategy trade appears in CSV but not in the app | CSV imports are explicit | stop the server and run `python .\Journal\journal_server.py --import-csv` |
| no stats appear in the app | all trades are still open or there are no closed trades | close a trade or add completed sample data |

## When to Use This Module

Use it when:

- you want to review and learn from trades
- you want a browser based trade log
- you want a quick HTML report from the CSV journal

Do not use it when:

- you need order placement
- you need historical strategy testing
- you want to skip reviewing trade quality and jump straight to automation

## TODO and Known Gaps

1. CSV import uses the compact strategy schema, while the browser app supports richer fields such as emotion, lesson, and stop loss.
2. Strategy scripts still write CSV rows directly. Import those rows explicitly when they should enter the browser journal.
3. `ANTHROPIC_API_KEY` is optional and is not used by `journal_server.py` today.

<!-- markdownlint-enable MD013 -->
