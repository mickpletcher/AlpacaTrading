<!-- markdownlint-disable MD013 MD024 MD060 -->

# 004 Novice Documentation Refresh Requirements

## Change Summary

Refresh the living documentation after the consolidated `main` assessment and make the operating guides understandable to a first-time Python, PowerShell, Alpaca, or algorithmic-trading user.

## Requirements

1. Correct stale claims about the assessed commit, validation results, CodeQL alerts, data storage, and live-trading availability.
2. Give a novice one safe, ordered setup and first-run path from the root README.
3. Define essential trading and repository terms in plain language.
4. Clearly separate historical backtesting, local journaling, paper order execution, scheduling, and webhook execution.
5. Put warnings next to commands that can submit paper orders.
6. Record verified defects and deferred improvements in their existing authorities.
7. Preserve the paper-only boundary and never instruct a reader to enable live trading.
8. Keep credentials, account identifiers, and runtime data out of documentation.
9. Validate authority coverage, Markdown, links, and the unchanged runtime test baseline.

## Non-Goals

- Fixing the runtime defects found by the reassessment.
- Enabling live trading.
- Replacing the repository architecture.
- Rewriting completed specs, accepted decisions, or resolved history.

<!-- markdownlint-enable MD013 MD024 MD060 -->
