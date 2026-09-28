<!-- markdownlint-disable MD013 -->

# Requirements

1. Python trading entry points must fail closed unless configured for the exact Alpaca paper endpoint.
2. BTC orders must use a crypto-supported time in force.
3. The BTC webhook must reject unsupported symbols and actions, stale or future messages, duplicate signal identifiers, excessive quantities or notionals, excessive request rates, daily losses beyond the configured limit, and orders after repeated execution failures.
4. Webhook logs must not contain the shared passphrase or full inbound payload.
5. PowerShell tests must use temporary risk state and an injected HTTP transport.
6. SQLite must be the journal authority. CSV import must be explicit and idempotent. CSV export must not cause later duplicate inserts.
7. Journal statistics must calculate profit factor from gross profit and gross loss and derive streaks from deterministic order.
8. Journal writes must validate request bodies and remain loopback-only.
9. Runtime journal, report, log, database, and safety-state files must not be tracked.
10. CI must exercise the BTC executor, journal, shared Python safety gate, scheduler wrapper, and existing suites. Dependency and code scanning configuration must exist.

<!-- markdownlint-enable MD013 -->
