<!-- markdownlint-disable MD013 -->

# Backtesting Module

This folder is where you test ideas before sending any order to Alpaca.

If you are new to trading, a backtest is a replay of a strategy on historical market data. It helps you see how a rule set would have behaved in the past.

> [!IMPORTANT]
> A backtest can help you learn, but it is not proof that a strategy will work in the future.

## Related Repo Guides

- [Root README](../README.md)
- [Learning Roadmap](../Learning%20Roadmap/README.md)
- [Journal Guide](../Journal/README.md)
- [Scheduler Guide](../Scheduler/README.md)
- [Tests Guide](../Tests/README.md)
- [Applied Upgrades](../upgrades/upgrades.md)
- [Core Trading Foundation Spec](../specs/001-core-trading-foundation/spec.md)

## Suggested Tutorials

### Tutorial 1: First Historical Run

1. Follow the root setup in [README.md](../README.md).
2. Run `python .\Backtesting\backtest.py`.
3. Review output expectations in this guide.

### Tutorial 2: Strategy Backtest To Journal Review

1. Run one strategy-specific backtest from this guide.
2. Open the [Journal Guide](../Journal/README.md).
3. Review how `Journal/trades.csv` and `report.html` fit into the workflow.

### Tutorial 3: From Backtest To Scheduled Paper Workflow

1. Validate strategy logic here first.
2. Run the matching tests from [Tests/README.md](../Tests/README.md).
3. Use the [Scheduler Guide](../Scheduler/README.md) only after manual runs succeed.

## What This Folder Is For

Use this folder when you want to:

- compare strategy behavior on historical data
- learn how indicators such as EMA, RSI, and Bollinger Bands are used in code
- generate CSV journal rows from completed backtest trades
- run strategy specific live paper workflows after testing first

Do not use this folder when you only need:

- a simple account status check
- the journal web app
- scheduler setup without understanding the strategy you plan to launch

## Files and What They Do

### Top level files

| File | Purpose |
| --- | --- |
| `backtest.py` | Simple multi strategy backtester using Yahoo Finance data and the `backtesting.py` library |
| `README.md` | This module guide |

### Strategy files under `strategies/`

| File | Purpose |
| --- | --- |
| `ema_crossover.py` | Shared EMA strategy logic |
| `backtest_ema.py` | EMA backtest using Alpaca historical bars |
| `live_ema.py` | EMA live or paper runner |
| `bollinger_rsi.py` | Shared Bollinger plus RSI strategy logic |
| `backtest_bollinger_rsi.py` | Bollinger plus RSI backtest using Alpaca daily bars |
| `live_bollinger_rsi.py` | Bollinger plus RSI live or paper runner |
| `bb_rsi_strategy.py` | Backtrader based Bollinger plus RSI workflow |
| `backtest_bb_rsi.py` | Backtrader runner using Alpaca market data |
| `latest_bb_rsi_signal.py` | One shot signal check for the latest Bollinger plus RSI setup |
| `gap_momentum.py` | Shared intraday gap up momentum strategy logic |
| `backtest_gap_momentum.py` | Gap momentum backtest using Alpaca minute and daily bars |
| `live_gap_momentum.py` | Gap momentum live or paper runner |
| `rsi_stack.py` | Shared multi timeframe RSI stack strategy logic |
| `backtest_rsi_stack.py` | RSI stack backtest using Alpaca bars |
| `live_rsi_stack.py` | RSI stack live or paper runner |
| `run_ema.ps1` | PowerShell wrapper for EMA workflows |
| `run_bollinger_rsi.ps1` | PowerShell wrapper for Bollinger plus RSI workflows |
| `run_gap_momentum.ps1` | PowerShell wrapper for gap momentum workflows |
| `run_rsi_stack.ps1` | PowerShell wrapper for RSI stack workflows |

## Prerequisites

- Python virtual environment activated
- dependencies installed from `requirements.txt`
- `.env` created if you plan to use Alpaca based strategy scripts
- valid Alpaca paper keys for all Alpaca based backtests and live runners

`Backtesting/backtest.py` is the main exception. It uses Yahoo Finance and does not need Alpaca keys.

## Setup Steps

1. Start with `backtest.py` if you want the simplest first run.
2. Move to strategy specific runners only after the simple backtest works.
3. Use paper trading only after you understand the backtest output and expected behavior.

## Beginner Strategy Overview

| Strategy | Plain English Idea | Better For | Caution |
| --- | --- | --- | --- |
| EMA crossover | Buy when short term trend crosses above longer term trend | trending markets | can give false signals in choppy markets |
| Bollinger plus RSI | Buy weakness in a range and sell strength when price stretches | sideways markets | can underperform during strong trends |
| RSI stack | Require agreement across multiple timeframes | filtering weaker signals | fewer trades |
| Gap momentum | Trade strong opening gaps with confirmation | intraday momentum days | time sensitive and more advanced |

## Run Commands

### Easiest first backtest

```powershell
python .\Backtesting\backtest.py
```

This tests:

- EMA crossover
- RSI mean reversion
- EMA plus RSI filter

Expected output:

- download message for the selected symbol
- per strategy metrics such as return, Sharpe ratio, win rate, and trade count
- `backtest_results.html` created in the current working directory

### Strategy specific Alpaca backtests

#### EMA crossover

```powershell
python .\Backtesting\strategies\backtest_ema.py --symbol SPY --start 2023-01-01 --end 2026-01-01 --fast 9 --slow 21
```

#### Bollinger plus RSI

```powershell
python .\Backtesting\strategies\backtest_bollinger_rsi.py --symbol SPY --start 2022-01-01 --end 2026-01-01 --bb-period 20 --bb-std 2.0 --rsi-period 14
```

#### Backtrader Bollinger plus RSI variant

```powershell
python .\Backtesting\strategies\backtest_bb_rsi.py --symbol SPY --lookback-days 540 --cash 25000 --commission 0.001 --bb-period 20 --bb-dev 2.0 --rsi-period 14 --rsi-overbought 70 --rsi-oversold 30
```

#### Latest Bollinger plus RSI signal check

```powershell
python .\Backtesting\strategies\latest_bb_rsi_signal.py --symbol SPY --lookback-days 180 --bb-period 20 --bb-dev 2.0 --rsi-period 14 --rsi-overbought 70 --rsi-oversold 30
```

#### RSI stack

```powershell
python .\Backtesting\strategies\backtest_rsi_stack.py --symbol SPY --start 2023-01-01 --end 2026-01-01 --fast-tf 1Hour --slow-tf 1Day --oversold 35 --overbought 65
```

#### Gap momentum

```powershell
python .\Backtesting\strategies\backtest_gap_momentum.py --symbol SPY --start 2024-01-01 --end 2026-01-01 --gap-threshold 0.02 --momentum-bars 3 --stop-loss 0.015 --take-profit 0.04 --volume-multiplier 1.5
```

### Live paper runners

Run these only after the matching backtest makes sense to you.

```powershell
python .\Backtesting\strategies\live_ema.py --symbol SPY --fast 9 --slow 21
python .\Backtesting\strategies\live_bollinger_rsi.py --symbol SPY --bb-period 20 --bb-std 2.0 --rsi-period 14
python .\Backtesting\strategies\live_rsi_stack.py
python .\Backtesting\strategies\live_gap_momentum.py
```

### PowerShell wrappers

These are useful if you prefer Windows first workflows.

```powershell
pwsh -NoProfile -File .\Backtesting\strategies\run_ema.ps1 -Mode backtest -Symbol SPY
pwsh -NoProfile -File .\Backtesting\strategies\run_bollinger_rsi.ps1 -Mode backtest -Symbol SPY -Start 2022-01-01
pwsh -NoProfile -File .\Backtesting\strategies\run_rsi_stack.ps1 -Mode backtest -Symbol SPY -Start 2023-01-01 -FastTF 1Hour -SlowTF 1Day
pwsh -NoProfile -File .\Backtesting\strategies\run_gap_momentum.ps1 -Mode backtest -Symbol SPY -Start 2024-01-01
```

## Example Usage

### Example 1: Beginner first run

```powershell
python .\Backtesting\backtest.py
```

Use this first if you want to see a complete backtest without needing Alpaca credentials.

### Example 2: Strategy specific EMA run with Alpaca data

```powershell
python .\Backtesting\strategies\backtest_ema.py --symbol QQQ --start 2024-01-01 --end 2026-01-01 --fast 9 --slow 21
```

Expected output:

- total trades
- winning and losing trades
- win rate
- total P and L
- trade table

## Expected Output Files

Depending on which script you run, this module may update:

- `backtest_results.html`
- `Journal/trades.csv`
- `Journal/live_ema_log.txt`
- `Journal/live_bollinger_rsi_log.txt`
- `Journal/live_gap_momentum_log.txt`
- `Journal/live_rsi_stack_log.txt`
- `Journal/scheduler_log.txt`

## Common Mistakes

- treating a profitable backtest as proof of a good live strategy
- forgetting that `backtest.py` and the Alpaca strategy scripts use different data sources
- using a date range that returns too little data
- moving to live paper runners before reading the strategy logic and output
- forgetting that the intraday gap strategy is time sensitive

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| `No historical bars were returned` | date range or symbol is invalid | widen the date range or try a more liquid symbol |
| `Missing ALPACA_API_KEY or ALPACA_SECRET_KEY` | `.env` is not set up | create `.env` from `.env.example` |
| backtest creates no trades | strategy conditions were never met | try a different symbol, time range, or parameter set |
| live runner blocks a trade | circuit breaker paused trading | inspect `Journal/circuit_log.txt` |
| gap momentum seems idle | market is closed or the scan window was missed | launch near market open and review the Scheduler guide |

## When to Use This Module

Use it when:

- you are deciding whether a strategy is worth deeper study
- you want historical evidence before paper trading
- you want to understand how the strategy rules are coded

Do not use it when:

- you only need the journal web app
- you only need account status or quote checks
- you want to skip learning and jump straight to unsupervised automation

## TODO and Known Gaps

1. `backtest.py` uses Yahoo Finance, while most strategy specific scripts use Alpaca data. The output will not always match across those paths.
2. Some live runners are less configurable from the command line than their matching backtest scripts.
3. Completed strategy trades are written to `Journal/trades.csv`, and the journal app now syncs those rows into SQLite when the journal is opened or refreshed.

<!-- markdownlint-enable MD013 -->
