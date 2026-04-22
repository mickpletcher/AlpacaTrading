# Publish Or Promote A Module In Trading Repo

Prepare a module or feature area in this repository for publication, handoff, or isolated promotion without breaking the rest of the repo.

## Applicable Areas

- PowerShell modules under `src/`
- Python feature folders such as `rsi_macd_bot/` or `btc-signal-executor/`
- documentation packages for `Backtesting/`, `Journal/`, or `Scheduler/`

## Instructions

1. Identify the exact module or feature boundary.
2. Inventory its runtime dependencies, docs, entry points, and tests.
3. Check whether it depends on repo-root files such as `.env.example`, `requirements.txt`, or shared strategy modules.
4. Define what must be copied, documented, or versioned for standalone use.
5. Do not separate code that still has implicit cross-folder coupling without documenting that dependency.

## Output Format

- publication target
- required files
- dependency notes
- verification steps
- release or handoff checklist
