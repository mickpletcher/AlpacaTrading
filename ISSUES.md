<!-- markdownlint-disable MD013 MD024 MD060 -->

# Defects

This file lists verified behavior that should be fixed. Read it before running any automated paper-order workflow.

## BUG-007: RSI bot does not manage protective stop orders as one lifecycle

**Status:** Open

**Severity:** High
**Area:** `rsi_macd_bot/`

The bot submits a market buy and then a separate stop order. If stop submission fails, the purchased position can remain without protection. When a later sell signal closes the position, the bot does not cancel the existing stop order first.

**Impact:** The paper account can contain an unprotected position or an old stop order that no longer matches the position.

**Evidence:** `rsi_macd_bot/bot.py` lines 98 through 124 and `rsi_macd_bot/order_manager.py` lines 98 through 122.

**Safe use:** Do not leave this bot unattended. After every paper execution test, review both positions and open orders in Alpaca.

**Required fix:** Treat entry, fill confirmation, protection, cancellation, exit, partial fills, and failure recovery as one tested order lifecycle.

## BUG-008: BTC maximum notional validation trusts the inbound signal price

**Status:** Open

**Severity:** Medium
**Area:** `btc-signal-executor/`

The webhook checks `quantity * payload price`, but the executor submits a market order. The payload price can differ from the broker price used for execution.

**Impact:** `WEBHOOK_MAX_NOTIONAL` is not a guaranteed broker-side limit. Quantity remains capped separately.

**Evidence:** `btc-signal-executor/validator.py` lines 43 through 48 and `btc-signal-executor/executor.py` lines 74 through 87.

**Safe use:** Keep `WEBHOOK_MAX_QUANTITY` conservatively low and supervise paper tests.

**Required fix:** Validate notional against a current authoritative quote with a configured price-deviation allowance, and fail closed when a reliable quote is unavailable.

## BUG-009: Journal renders stored text as HTML

**Status:** Open

**Severity:** Medium
**Area:** `Journal/`

The API stores several text fields without length or content validation. The browser inserts stored values into `innerHTML` when rendering history and setup statistics.

**Impact:** Crafted journal or imported CSV values can execute unwanted browser content when the local journal page renders them.

**Evidence:** `Journal/journal_server.py` lines 137 through 152 and `Journal/journal.html` lines 559 through 640.

**Safe use:** Keep the journal loopback-only. Do not import journal CSV files from an untrusted source.

**Required fix:** Render user-controlled values with `textContent`, add server-side limits, add regression tests, and set a restrictive Content Security Policy.

## BUG-010: Current CodeQL findings are unresolved

**Status:** Open

**Severity:** Medium
**Area:** GitHub Actions and journal API responses

CodeQL currently reports five open alerts. Three report missing explicit workflow permissions. Two report raw exception text returned by journal validation responses.

**Impact:** Workflow token permissions are implicit, and API responses can expose implementation details that callers do not need.

**Evidence:** `.github/workflows/ci.yml` and `Journal/journal_server.py` lines 119 through 125 and 163 through 169.

**Required fix:** Declare minimum workflow permissions and replace raw exception output with stable client-facing validation messages.

BUG-001 through BUG-006 were resolved by `specs/003-trading-safety-remediation/`. Their permanent history and validation summary are recorded under Upgrade 004 in `upgrades/README.md`.

New defects must receive the next permanent `BUG-` identifier. Do not reuse resolved identifiers.

<!-- markdownlint-enable MD013 MD024 MD060 -->
