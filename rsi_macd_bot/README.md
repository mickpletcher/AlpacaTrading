<!-- markdownlint-disable MD013 -->

# RSI Plus MACD Signal Bot

This module provides a fully automated RSI plus MACD signal bot built with Alpaca py.

It places market orders when RSI and MACD confirmation occur within a configured window, then places a stop loss after each buy.

## Related Repo Guides

- [Root README](../README.md)
- [Scheduler Guide](../Scheduler/README.md)
- [Journal Guide](../Journal/README.md)
- [Tests Guide](../Tests/README.md)
- [Learning Roadmap](../Learning%20Roadmap/README.md)
- [Applied Upgrades](../upgrades/upgrades.md)
- [Core Trading Foundation Spec](../specs/001-core-trading-foundation/spec.md)

## Suggested Tutorials

### Tutorial 1: Dependency And Startup Check

1. Install this module's requirements from this guide.
2. Run the manual validation checklist in [Tests/README.md](../Tests/README.md).
3. Confirm paper-mode startup before leaving the bot running.

### Tutorial 2: Bot To Journal Review

1. Run `python .\rsi_macd_bot\bot.py`.
2. Review `rsi_macd_bot/trades.log`.
3. Cross-check trade review steps in the [Journal Guide](../Journal/README.md).

### Tutorial 3: Scheduled Bot Automation

1. Validate the bot manually first.
2. Use [Scheduler/README.md](../Scheduler/README.md) for timed-launch patterns.
3. Review [Applied Upgrades](../upgrades/upgrades.md) before making repo-level bot workflow changes.

## Purpose

Use this module when you want to:

- scan multiple symbols every 5 minutes during market hours
- execute buy and sell orders automatically
- enforce position sizing and max open trade limits
- log each signal and order event for review

Do not use this module when you need:

- manual order confirmation
- historical replay testing only
- a no risk environment with no external API calls

## File Map

| File | Purpose |
| --- | --- |
| `config.py` | Parameters for watchlist, indicators, timing, and risk |
| `data_fetcher.py` | Historical bars retrieval with safe error handling |
| `indicators.py` | RSI and MACD math plus combined signal detection |
| `order_manager.py` | Position checks, sizing, market orders, and stop orders |
| `logger.py` | Rotating logger for signal and order events |
| `bot.py` | Main schedule loop and graceful shutdown summary |
| `.env.example` | Environment template |
| `requirements.txt` | Module dependencies |

## Signal Logic

BUY requires:

1. RSI cross below oversold
2. MACD histogram turn positive
3. both within `SIGNAL_WINDOW` bars

SELL requires:

1. RSI cross above overbought
2. MACD histogram turn negative
3. both within `SIGNAL_WINDOW` bars

## Order Logic

- skip buy when symbol already has an open position
- skip buy when open positions already equal `MAX_OPEN_TRADES`
- compute quantity from account equity and `POSITION_SIZE_PCT`
- submit day market order
- submit stop order at entry times `(1 - RISK_PER_TRADE)`

## Setup

From repo root:

```powershell
python -m pip install -r .\rsi_macd_bot\requirements.txt
Copy-Item .\rsi_macd_bot\.env.example .env
notepad .env
```

Example env:

```dotenv
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
PAPER=true
```

## Run

```powershell
python .\rsi_macd_bot\bot.py
```

## Logging

Events are written to:

```text
rsi_macd_bot/trades.log
```

Format:

```text
[TIMESTAMP] SYMBOL | SIGNAL | ACTION | QTY | PRICE | RSI | MACD_HIST
```

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| Bot fails at startup | missing API key or secret | update `.env` with valid Alpaca credentials |
| Bot runs but no orders | market closed or no qualifying signals | confirm market hours and inspect `trades.log` signals |
| Order rejected | buying power, symbol status, or account restrictions | check logged API code and Alpaca dashboard |
| Stop order missing | buy fill price not returned quickly | inspect logs and increase fill wait retries if needed |

## Safety

- keep `PAPER=true` during validation
- start with small sizing values
- review logs daily for skipped actions and API errors
- move to live mode only after repeatable paper behavior

<!-- markdownlint-enable MD013 -->
