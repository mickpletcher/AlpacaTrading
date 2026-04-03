# Learning Roadmap

## Phase 2: Bollinger Bands + RSI Combo

This strategy is better suited to sideways or range bound markets than trending markets because it bets on reversion after volatility extremes.

Indicator roles and why they complement each other:

- Bollinger Bands measure volatility and identify price moves outside a normal range.
- RSI measures momentum and confirms whether the move is truly overbought or oversold.
- Bandwidth measures market regime. Lower bandwidth helps focus on quieter, mean reversion conditions.

BUY requires all three conditions:

1. Price crosses below the lower Bollinger Band.
2. RSI is below 35.
3. Bandwidth is below 0.1.

All three matter because a band breach alone can happen in trend continuation, RSI alone can stay extreme, and low bandwidth helps filter out trending phases where reversals are less reliable.

Run a backtest:

```bash
python Backtesting/strategies/backtest_bollinger_rsi.py --symbol SPY --start 2022-01-01 --end 2026-01-01 --bb-period 20 --bb-std 2.0 --rsi-period 14
```

Run live paper trading:

```bash
python Backtesting/strategies/live_bollinger_rsi.py --symbol SPY --bb-period 20 --bb-std 2.0 --rsi-period 14
```

In Journal/trades.csv, watch for:

- Consistent symbol and side rows with notes showing backtest_bollinger_rsi or live_bollinger_rsi_paper.
- Stable entry and exit behavior after actual BUY then SELL cycles.
- PnL distribution and hold duration that match your expected range behavior.

Warning:
This strategy can underperform in strong directional trends. Avoid deployment in clear trend expansion periods where price rides one band for extended time.

Suggested next step for Phase 3:
Add a 50 day SMA filter to block trades when price is in a clear uptrend or downtrend.

## Phase 3: RSI Stack (Multi-Timeframe)

RSI Stack requires agreement across multiple timeframes before a signal can fire. This improves signal quality by filtering setups that only appear on one timeframe.

Timeframes used:

- 1Hour is the primary tactical entry timing layer.
- 1Day is the strategic confirmation layer.

Thresholds are relaxed to 35 and 65 instead of 30 and 70 so entries and exits can happen earlier while still requiring oversold or overbought confirmation.

rsi_stack_score is the count of timeframes currently aligned in the same directional condition. Higher values indicate stronger multi timeframe agreement.

Run a backtest:

```bash
python Backtesting/strategies/backtest_rsi_stack.py --symbol SPY --start 2023-01-01 --end 2026-01-01 --fast-tf 1Hour --slow-tf 1Day --oversold 35 --overbought 65
```

Run live paper trading:

```bash
python Backtesting/strategies/live_rsi_stack.py
```

In Journal/trades.csv, compare outcomes where stack score is 2 versus 1 to verify whether full agreement improves results over partial agreement.

Compared with Phase 1 and Phase 2, the core advantage is fewer but higher conviction trades.

Known limitation:
Adding more timeframes reduces signal frequency. There is always a tradeoff between signal quality and number of opportunities.

Suggested next steps for Phase 4:
Add a third timeframe such as 1Week, or introduce a volume confirmation filter.

## Phase 4: Gap-Up Momentum (Intraday)

A gap up is when a stock opens materially above the previous day close. That opening imbalance can create early momentum in the first 15 minutes as new buyers and short covering flow into the move.

Entry requires all three conditions:

1. Gap threshold: the open must be at least 2 percent above the prior close, which filters out small random opens.
2. Momentum bars: the next confirmation bars must stay green so the move is not fading immediately after the open.
3. Volume check: opening volume must exceed the per minute baseline by a multiplier to confirm real participation and avoid thin prints.

Exit condition priority order:

1. Stop loss first for capital protection.
2. Take profit second to lock gains when momentum extends.
3. End of day exit last as a hard no overnight hold rule.

This strategy pairs directly with Scheduler because launch timing is mandatory. It must start by 9:25 AM ET so it can process the scan window from 9:30 to 9:45 ET, then run its own internal hold loop through the day.

Scheduled Task registration pattern:

1. Task 1 at 9:25 AM ET to launch the live scan before market open.
2. Task 2 at 4:05 PM ET to confirm end of day handling and make logs and trade rows visible after close.

Two tasks are needed because this is intraday and time window driven, unlike the earlier end of day style strategies.

To evaluate performance in Journal/trades.csv, filter notes for rows containing gap_momentum. Compare counts of stop_loss exits versus take_profit exits and tune gap, momentum, or risk thresholds from that distribution.

Key difference from Phases 1 to 3:
This phase is intraday only. No position is allowed to carry into the next session under any circumstance.

Known limitations:

1. Works best on single stocks with earnings or news catalysts. Broad ETFs like SPY usually show fewer high quality gap continuation moves.
2. Requires 1 minute bars and therefore uses more API calls than daily bar strategies.
3. Very sensitive to the first 15 minutes. Late launch can miss the only valid entry window.

Suggested next step for Phase 5:
Add a pre market scanner that selects the strongest gap candidates before 9:30 AM, then run Gap Momentum on those symbols instead of one fixed symbol.
