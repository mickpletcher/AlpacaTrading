<!-- markdownlint-disable MD013 -->

# Tests Module

This folder contains automated checks for strategy logic and Alpaca connectivity.

If you are new to testing, the short version is simple:

- a passed test means the check succeeded
- a failed test means the code or environment needs attention
- a skipped test means the test intentionally did not run because a required condition was missing

## Related Repo Guides

- [Root README](../README.md)
- [Backtesting Guide](../Backtesting/README.md)
- [Journal Guide](../Journal/README.md)
- [Scheduler Guide](../Scheduler/README.md)
- [Learning Roadmap](../Learning%20Roadmap/README.md)
- [RSI Plus MACD Bot Guide](../rsi_macd_bot/README.md)
- [BTC Signal Executor Guide](../btc-signal-executor/README.md)
- [Applied Upgrades](../upgrades/README.md)
- [Core Trading Foundation Spec](../specs/001-core-trading-foundation/spec.md)

## Suggested Tutorials

### Tutorial 1: First Safe Verification

1. Complete root setup in [README.md](../README.md).
2. Run `.\.venv\Scripts\python.exe -m pytest .\Tests -q`.
3. Read the skip behavior notes in this file before assuming failure.

### Tutorial 2: Strategy Change Validation

1. Update a strategy under [Backtesting](../Backtesting/README.md).
2. Run the targeted Python tests from this guide.
3. Review downstream effects in the [Journal Guide](../Journal/README.md).

### Tutorial 3: Automation Validation Path

1. Validate strategy logic here first.
2. Then move to [Scheduler/README.md](../Scheduler/README.md) or [rsi_macd_bot/README.md](../rsi_macd_bot/README.md).
3. Review [Applied Upgrades](../upgrades/README.md) before proposing repo-level validation changes.

## What This Folder Is For

Use this folder when you want to:

- confirm the strategy rules behave as expected on synthetic data
- check that Alpaca paper credentials and basic endpoints work
- validate the repo before making changes

Do not use this folder when you only need:

- a one off manual script run
- scheduler setup
- browser journal usage

## Files and What They Validate

| File | What It Checks | Requires Alpaca? |
| --- | --- | --- |
| `test_connection.py` | credentials present, account endpoint, market clock endpoint | Yes |
| `test_ema_crossover.py` | EMA buy and sell signals, gating, no double signal behavior | No |
| `test_bollinger_rsi.py` | Bollinger plus RSI indicator columns, signal rules, position gating | No |
| `test_gap_momentum.py` | gap detection, momentum confirmation, volume checks, stop loss, take profit, end of day exit | No |
| `test_rsi_stack.py` | multi timeframe RSI calculation, alignment, stack score, signal gating | No |

## Prerequisites

- Python virtual environment activated
- dependencies installed from `requirements.txt`

Additional requirement for `test_connection.py`:

- `.env` file with valid Alpaca paper trading credentials

## Setup Steps

1. activate `.venv`
2. install dependencies from `requirements.txt`
3. if you want live Alpaca connectivity tests, create `.env`

## Run Commands

### Run all tests

```powershell
pytest .\Tests -v
```

### Run the PowerShell Pester suite

```powershell
pwsh -NoProfile -Command "Import-Module Pester -MinimumVersion 5.5.0 -Force; Invoke-Pester -Path .\Tests -CI"
```

### Run only the synthetic logic tests

```powershell
pytest .\Tests\test_ema_crossover.py -v
pytest .\Tests\test_bollinger_rsi.py -v
pytest .\Tests\test_gap_momentum.py -v
pytest .\Tests\test_rsi_stack.py -v
```

### Run only the Alpaca connectivity test

```powershell
pytest .\Tests\test_connection.py -v
```

## Manual Validation for RSI Plus MACD Bot

Automated tests for `rsi_macd_bot` are not in this repo yet, so use this manual checklist after any bot logic changes.

### Quick environment check

```powershell
python -c "import importlib.util as u;mods=['alpaca','pandas','schedule','dotenv','pandas_ta'];print({m: bool(u.find_spec(m)) for m in mods})"
```

Expected output:

```text
{'alpaca': True, 'pandas': True, 'schedule': True, 'dotenv': True, 'pandas_ta': True}
```

### Syntax check

```powershell
python -m compileall .\rsi_macd_bot
```

Expected output:

```text
Compiling '.\\rsi_macd_bot\\bot.py'...
...
```

### Dry startup check in paper mode

1. ensure `.env` has valid paper credentials and `PAPER=true`
2. run `python .\rsi_macd_bot\bot.py`
3. let it run for one or two scan cycles
4. stop with `Ctrl+C`

Expected behavior:

- bot starts without crashing
- market closed cycles log as skip events outside market hours
- open positions summary is logged on shutdown
- no unhandled traceback appears

### Log verification

Check `rsi_macd_bot/trades.log` for rows matching the expected format:

```text
[TIMESTAMP] SYMBOL | SIGNAL | ACTION | QTY | PRICE | RSI | MACD_HIST
```

Confirm at least these action patterns appear during test runs:

- `NO_ACTION`
- `SKIP_ALREADY_OPEN` or `SKIP_NO_POSITION`
- `ORDER_PLACED` when signal conditions and account state permit orders

### Risk guard verification

Before unattended runs, confirm:

1. `PAPER=true`
2. `POSITION_SIZE_PCT` is small enough for safe paper testing
3. `MAX_OPEN_TRADES` is set to a conservative value
4. stop loss submissions are present in logs after buy fills

## Example Usage

### Example 1: Safe first test run without Alpaca credentials

```powershell
pytest .\Tests\test_ema_crossover.py -v
```

Expected output:

```text
... PASSED
```

### Example 2: Connectivity test with `.env`

```powershell
pytest .\Tests\test_connection.py -v
```

Expected output when configured correctly:

```text
test_credentials_present PASSED
test_account_endpoint_returns_200 PASSED
test_clock_endpoint_contains_is_open PASSED
```

## What a Skipped Test Means

In this repo, a skipped test most often means:

- you ran `test_connection.py`
- `ALPACA_API_KEY` or `ALPACA_SECRET_KEY` was not set
- pytest intentionally did not call Alpaca

That is normal behavior when credentials are missing.

It is not the same as a failing test.

## Common Mistakes

- assuming all tests require live API access
- treating a skip as a failure
- forgetting to activate `.venv`
- running the connectivity test with live keys when you meant to use paper keys

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| tests fail to import modules | dependencies are missing | reinstall with `python -m pip install -r requirements.txt` |
| `test_connection.py` is skipped | credentials are not set | create `.env` and add Alpaca paper keys |
| connectivity test fails with `401` or `403` | wrong keys or wrong URL | confirm paper keys and paper base URL |
| strategy tests fail after code changes | logic or expected behavior changed | inspect the specific failing test and the related strategy file |

## When to Use This Module

Use it when:

- you changed code
- you want a confidence check before scheduling or paper trading
- you want fast feedback on strategy behavior

Do not use it when:

- you expect tests alone to prove profitability
- you have not completed basic setup

## TODO and Known Gaps

1. The connectivity tests cover basic Alpaca reachability, not complete trade lifecycle validation.
2. The current tests focus on logic and safety, not full end to end scheduler automation.
3. The PowerShell suite is standardized on Pester 5.x and should be run with that version in local and CI environments.

<!-- markdownlint-enable MD013 -->
