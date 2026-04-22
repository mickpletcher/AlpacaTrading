# Generate Requirements For Trading Repo

You are working in the `Trading` repository, which is an existing mixed Python and PowerShell codebase for Alpaca paper trading, backtesting, journaling, scheduling, and automation.

## Goal

Create or update a numbered spec package requirement document that reflects a real change needed in this repository.

## Instructions

1. Inspect the current repo before writing requirements.
2. Anchor requirements to existing folders, modules, and entry points.
3. Preserve current working behavior unless the requested change explicitly replaces it.
4. Distinguish current-state facts from proposed behavior.
5. Write concrete, testable requirements.
6. Include non-goals when the request could accidentally expand scope.
7. Call out impacts on:
   - `src/` PowerShell modules
   - Python entry points in `Alpaca/`, `Backtesting/`, `Journal/`, `rsi_macd_bot/`, or `btc-signal-executor/`
   - tests in `Tests/`
   - docs and README updates

## Output Format

- Update `specs/<NNN-name>/requirements.md`
- Include:
  - change summary
  - current baseline
  - numbered functional requirements
  - numbered non-functional requirements
  - non-goals
  - acceptance signals

Do not write implementation details here. Save those for `spec.md` and `plan.md`.
