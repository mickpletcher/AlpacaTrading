<!-- markdownlint-disable MD013 MD024 -->

# ADR 001: Paper-only execution and local runtime state

**Status:** Accepted
**Date:** 2026-09-28

## Context

Python execution surfaces independently infer paper or live mode. The BTC webhook accepts internet-originated orders without durable replay controls, bounded order size, or a reliable paper endpoint check. PowerShell tests write to operational risk state. Journal CSV and SQLite synchronization can duplicate records. Runtime trade and safety data is tracked in Git.

## Decision

1. All Python order-routing surfaces use one shared fail-closed paper-mode assertion.
2. Live Python order routing is unavailable until a separate approved design adds explicit operator, environment, and account confirmation.
3. The BTC webhook remains paper-only and validates symbol, action, quantity, notional, timestamp, replay identifier, request rate, daily loss, and execution-failure state before routing an order.
4. SQLite is the journal authority. CSV is explicit import or generated export only.
5. Runtime journal, log, database, report, and safety-state files remain local and ignored by Git.
6. Automated tests inject temporary state and transport boundaries. Default validation cannot reach Alpaca or alter operational state.

## Consequences

- Existing paper workflows remain available.
- Changing an environment variable or source constant cannot enable Python live trading.
- Existing TradingView alerts must add `signal_id` and `timestamp`.
- Existing journal CSV data requires an explicit import instead of automatic synchronization.
- Previously tracked runtime files remain on the operator's machine after removal from Git tracking.

## Alternatives rejected

- A warning-only live mode was rejected because it does not enforce an execution boundary.
- Bidirectional CSV and SQLite synchronization was rejected because it creates two competing authorities.
- Tests that copy or restore operational state were rejected because a failed test can still corrupt the source data.

<!-- markdownlint-enable MD013 MD024 -->
