<!-- markdownlint-disable MD013 -->

# Tests Module

This folder contains automated checks for strategy logic and Alpaca connectivity.

If you are new to testing, the short version is simple:

- a passed test means the check succeeded
- a failed test means the code or environment needs attention
- a skipped test means the test intentionally did not run because a required condition was missing

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

<!-- markdownlint-enable MD013 -->