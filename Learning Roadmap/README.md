<!-- markdownlint-disable MD013 -->

# Learning Roadmap Module

This folder explains how to learn the repo without trying to understand everything at once.

If you are brand new to trading or coding, this is the pace to follow.

## What This Folder Is For

Use this folder when you want to:

- learn the repo in a logical order
- understand which strategy to study first
- avoid skipping straight to automation before you understand the basics
- get practice prompts and milestones

Do not use this folder when you only need:

- a quick command reference
- scheduler setup details
- a file by file architecture map

## Files and What They Do

| File | Purpose |
| --- | --- |
| `README.md` | High level roadmap for beginners |
| `ROADMAP.md` | More detailed phase by phase strategy notes and next steps |

## Prerequisites

- root setup completed
- `.env` created if you want to follow the Alpaca based workflows
- willingness to move slowly and document what you learn

## Recommended Order

### Phase 0: Foundation

Goal: understand the terms before chasing results.

Checklist:

1. read the root README glossary
2. create an Alpaca paper account
3. run the connectivity test
4. run `Backtesting/backtest.py`
5. open the journal app

### Phase 1: EMA crossover

Why first:

- it is easy to explain
- it is one of the simplest trend following ideas
- it appears in both backtest and live paper workflows

Key idea:

- a fast EMA reacts quickly to recent price changes
- a slow EMA reacts more slowly
- when the fast EMA crosses above the slow EMA, the strategy treats that as a bullish signal

Run it:

```powershell
python .\Backtesting\strategies\backtest_ema.py --symbol SPY --start 2023-01-01 --end 2026-01-01 --fast 9 --slow 21
python .\Backtesting\strategies\live_ema.py --symbol SPY --fast 9 --slow 21
```

What success looks like:

- the backtest prints completed trades and summary stats
- the live runner prints a clear startup message and logs decisions
- `Journal/trades.csv` receives rows during strategy workflows

### Phase 2: Bollinger plus RSI

Why next:

- it teaches range trading and mean reversion
- it shows how two indicators can confirm each other

Key idea:

- Bollinger Bands describe a moving price range
- RSI tries to show when momentum is stretched
- together they help identify possible reversal points in sideways markets

Run it:

```powershell
python .\Backtesting\strategies\backtest_bollinger_rsi.py --symbol SPY --start 2022-01-01 --end 2026-01-01 --bb-period 20 --bb-std 2.0 --rsi-period 14
python .\Backtesting\strategies\live_bollinger_rsi.py --symbol SPY --bb-period 20 --bb-std 2.0 --rsi-period 14
```

### Phase 3: RSI stack

Why later:

- it introduces multi timeframe confirmation
- it is more advanced than a single signal on one chart

Key idea:

- a setup is stronger when more than one timeframe agrees

Run it:

```powershell
python .\Backtesting\strategies\backtest_rsi_stack.py --symbol SPY --start 2023-01-01 --end 2026-01-01 --fast-tf 1Hour --slow-tf 1Day --oversold 35 --overbought 65
python .\Backtesting\strategies\live_rsi_stack.py
```

### Phase 4: Gap momentum

Why last:

- it is intraday only
- it depends on timing near market open
- it uses minute data and more conditions

Key idea:

- some stocks open far above the previous close
- that opening gap can continue if momentum and volume confirm it

Run it:

```powershell
python .\Backtesting\strategies\backtest_gap_momentum.py --symbol SPY --start 2024-01-01 --end 2026-01-01 --gap-threshold 0.02 --momentum-bars 3 --stop-loss 0.015 --take-profit 0.04 --volume-multiplier 1.5
python .\Backtesting\strategies\live_gap_momentum.py
```

## Suggested Month by Month Path

### Month 1

- complete setup
- use only paper trading
- run several backtests on familiar symbols
- log at least a few manual sample trades in the journal

### Month 2

- focus on one or two simple setups only
- review journal entries weekly
- compare what the strategy says versus what you expected as a human

### Month 3

- review consistency, not just raw profit
- study losing periods and drawdown behavior
- automate only the parts you fully understand

## Example Learning Prompts

Use these with your preferred external AI tool if helpful.

```text
Explain EMA crossover like I know spreadsheets but not technical analysis.
```

```text
Explain what a backtest can and cannot prove in plain English.
```

```text
I have a strategy with a 55 percent win rate but poor profit factor. What should I review first?
```

```text
Help me compare trend following strategies versus mean reversion strategies using simple examples.
```

## Common Mistakes

- trying every strategy at once
- moving to live paper automation before reading the output carefully
- confusing paper profitability with readiness for live money
- ignoring the journal review step

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| roadmap feels overwhelming | too many modules at once | follow the phases in order |
| strategy output makes no sense | missing glossary or trading basics | go back to the root README glossary |
| paper trading feels random | no clear setup focus | pick one strategy and one symbol for a while |

## When to Use This Module

Use it when:

- you need a guided path
- you are new to both trading and programming
- you want to build confidence without rushing

Do not use it when:

- you need exact setup commands right now
- you need deep implementation details on a specific script

## TODO and Known Gaps

1. The detailed `ROADMAP.md` currently goes deeper on some strategy phases than this summary file.
2. The roadmap assumes paper trading only, which is the intended safe learning path for this repo.

<!-- markdownlint-enable MD013 -->
