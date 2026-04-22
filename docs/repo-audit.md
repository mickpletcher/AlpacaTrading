<!-- markdownlint-disable MD013 -->

# Repository Audit

## Summary

This repository is an existing mixed-stack trading toolkit centered on Alpaca paper-trading workflows. It is not a single deployable service. Instead, it is a collection of cooperating utilities for:

- strategy research and backtesting
- paper-trading execution
- journaling and trade review
- PowerShell module-based Alpaca automation
- scheduling and webhook-triggered execution

## Folder Structure

| Path | Purpose |
| --- | --- |
| `src/` | PowerShell Alpaca modules for reusable API and risk functionality |
| `Alpaca/` | Python and PowerShell paper-trading scripts and helpers |
| `Backtesting/` | Strategy definitions, historical replay, and live-paper runners |
| `Journal/` | Flask journal app, SQLite/CSV storage, report generation, logs |
| `Scheduler/` | PowerShell and shell launchers for scheduled runs |
| `rsi_macd_bot/` | Standalone RSI plus MACD paper-trading bot |
| `btc-signal-executor/` | FastAPI webhook receiver that routes BTC signals to Alpaca |
| `examples/` | PowerShell module usage examples |
| `Tests/` | Python `pytest` tests and PowerShell Pester tests |
| `docs/` | Screenshot placeholders and now audit/spec support docs |

## Languages And Frameworks

- Python
- PowerShell
- Flask
- FastAPI
- Alpaca SDK (`alpaca-py`)
- `pytest`
- Pester
- `backtesting.py`
- Backtrader
- Yahoo Finance client (`yfinance`)

## Current Entry Points

| Entry Point | Purpose |
| --- | --- |
| `Backtesting/backtest.py` | Simplest top-level historical strategy runner |
| `Alpaca/paper_trade.py` | Python paper-trading launcher |
| `Alpaca/alpaca_paper.py` | Python Alpaca helper and trading flow |
| `Alpaca/alpaca_paper.ps1` | PowerShell paper-trading helper |
| `Journal/journal_server.py` | Flask journal application |
| `Journal/analyze_journal.py` | HTML report generation from CSV trades |
| `Scheduler/run_strategy.ps1` | Windows scheduler entry point |
| `Scheduler/run_strategy.sh` | Shell scheduler entry point |
| `rsi_macd_bot/bot.py` | Standalone bot loop |
| `btc-signal-executor/main.py` | FastAPI webhook service |

## Tests

### Python

- Located in `Tests/test_*.py`
- Current result in local `.venv`: `36 passed, 3 skipped`
- Coverage focuses on strategy logic and Alpaca connectivity

### PowerShell

- Located in `Tests/*.Tests.ps1`
- Covers config, auth, risk, market data parsing, and trade update parsing
- Current issues:
  - local machine Pester 3.4 is too old for some test constructs
  - installed Pester 5 exposes legacy assertion syntax debt
  - some failing expectations also suggest follow-up fixes may be needed after test modernization

## Build And Automation

- No existing GitHub Actions CI workflow was present
- No top-level packaging workflow was present
- Python compile checks pass with `python -m compileall`
- PowerShell modules have manifest files under `src/`

## Documentation Quality

Strengths:

- Root `README.md` already explains the project and modules in plain language
- Submodule docs exist for `Backtesting/`, `Journal/`, `Scheduler/`, `Tests/`, `rsi_macd_bot/`, and `btc-signal-executor/`
- The repo is approachable for learners

Gaps before retrofit:

- No GitHub Spec workflow documentation
- No `.github/copilot-instructions.md`
- No reusable prompt library for agentic work
- No CI workflow
- No canonical spec history under `specs/`
- Repo guidance did not explicitly route future work through requirements/spec/plan/tasks

## Architectural Strengths

- Clear separation between reusable PowerShell modules and script entry points
- Multiple strategy implementations already separated under `Backtesting/strategies/`
- Journal subsystem is isolated from strategy logic
- Standalone services and bots are grouped into dedicated folders

## Architectural Problems

1. The repository serves multiple related products, so ownership boundaries are documented but not enforced.
2. The top-level test directory uses `Tests/`, which can cause convention drift in cross-platform tooling.
3. CI was absent, so local workflows were the only quality gate.
4. PowerShell tests mix older and newer Pester styles, making them unreliable as-is for modern automation.
5. Generated artifacts and source-like files live close together, which increases the need for explicit developer rules.

## Retrofit Outcome

This retrofit keeps the current codebase intact and adds:

- GitHub Spec workflow scaffolding
- repo-specific Copilot and agent instructions
- reusable prompts for requirements through release-readiness
- a baseline core-trading-foundation spec package
- CI aligned to the stable parts of the current repo

## Recommended Next Technical Follow-Up

1. Modernize PowerShell tests to a single supported Pester version.
2. Decide whether generated journal artifacts should remain tracked long-term.
3. Add module-level ownership and change boundaries for larger future features.

<!-- markdownlint-enable MD013 -->
