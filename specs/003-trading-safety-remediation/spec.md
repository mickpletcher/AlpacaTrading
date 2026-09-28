<!-- markdownlint-disable MD013 -->

# Trading Safety Remediation

## Scope

Resolve BUG-001 through BUG-006 and the directly related paper-mode, runtime-data, validation, and repository automation gaps recorded in the 2026-09-28 assessment.

## Design

- Add a shared `Alpaca/trading_safety.py` assertion used by every Python order-routing entry point.
- Keep Python execution paper-only. The assertion accepts only `https://paper-api.alpaca.markets`.
- Refactor the BTC FastAPI application into an injectable application factory. Keep production defaults environment-driven. Use bounded in-memory rate, replay, and failure state because the current service is single-process and has no database.
- Use payload price only for notional validation. Execution remains a market order.
- Inject the PowerShell risk state directory through `Initialize-AlpacaRisk` and the HTTP request implementation through `Invoke-AlpacaRequest`.
- Remove automatic CSV-to-SQLite synchronization from journal request paths. Retain an explicit import function for migration and a database-to-CSV export function.
- Enforce loopback access and validate mutable journal requests.
- Ignore and untrack runtime artifacts without deleting local copies.
- Extend Windows CI and add Dependabot and CodeQL workflows.

## Compatibility

- Existing paper account credentials and order commands remain valid.
- TradingView messages require two new fields: `signal_id` and UTC `timestamp`.
- CSV files remain importable and exportable, but are no longer a live peer database.
- PowerShell public functions remain compatible because new injection parameters are optional.

## Out of scope

- Enabling live trading.
- Distributed webhook replay or rate-limit storage.
- Authentication for a remotely hosted journal. Remote journal hosting remains prohibited.
- Backtest methodology changes.

<!-- markdownlint-enable MD013 -->
