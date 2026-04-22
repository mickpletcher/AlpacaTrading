# Regression Test Trading Repo Change

Run or define the most relevant regression checks for the implemented change.

## Baseline Checks

Prefer these when applicable:

- `python -m compileall Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor`
- `.\.venv\Scripts\python.exe -m pytest .\Tests -q`
- PowerShell module manifest validation under `src/`
- targeted script or entry-point smoke tests related to the change

## Instructions

1. Select checks based on the changed files.
2. Distinguish executed checks from recommended-but-not-run checks.
3. Note skipped checks and why they were skipped.
4. Highlight any failures with actionable follow-up.

## Output Format

- checks run
- results
- skipped checks
- regression risk summary
