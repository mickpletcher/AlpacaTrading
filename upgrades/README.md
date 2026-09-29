<!-- markdownlint-disable MD013 MD024 -->

# Applied Upgrades

## Overview

This document tracks repository-level upgrades that have already been applied to the `Trading` repository. It is intended to capture concrete repo improvements rather than speculative ideas.

## Upgrade 001: GitHub Spec Retrofit

### Summary

Retrofitted the existing repository into a spec-driven workflow without rebuilding or replacing the current Python and PowerShell trading toolkit.

### What Changed

- added `.github/copilot-instructions.md` for repo-specific coding guidance
- added `.github/prompts/` with reusable prompts for requirements, spec, plan, tasks, implementation, audit, regression testing, release readiness, and module publication
- added `.github/workflows/ci.yml` for Python and PowerShell quality checks
- added `specs/001-core-trading-foundation/` with `requirements.md`, `spec.md`, `plan.md`, and `tasks.md`
- added `docs/repo-audit.md` to capture the current repository audit
- updated `README.md` so the documented architecture, setup, usage, and workflow match the actual repo
- added `pytest.ini` so Python tooling explicitly targets the existing `Tests/` directory

### Outcome

- future non-trivial work now has a requirements to spec to plan to tasks workflow
- repo guidance is now explicit for human contributors and AI coding agents
- CI exists for the stable current validation path
- the current codebase remains preserved

## Upgrade 002: Upgrades Tracking Directory

### Summary

Added a dedicated `upgrades/` directory to track completed repo upgrades separately from speculative future ideas.

### What Changed

- created `upgrades/README.md` to track completed repository upgrades
- created `upgrades/future-upgrades.md` to hold tiered future-upgrade planning
- updated `.gitignore` so `upgrades/future-upgrades.md` stays local and is not pushed to the repository

### Outcome

- completed structural upgrades now have a clear home in the repo
- future ideas can be captured without forcing unfinished planning into version control
- the repository now has a lightweight upgrade log that complements the spec system

## Upgrade 003: Living Documentation Standard 2.2

### Summary

Adopted a repository-local Tier 2 documentation standard using single-valued responsibility authorities and evidence-based assessment.

### What Changed

- declared the authority mapping in `PROJECT-STANDARD.md` and `.docs-authority.json`
- consolidated repository agent rules under `AGENTS.md`
- added architecture, operations, defect, debt, future-work, decision, and change-history authorities
- adapted the existing repository audit and test guide as current assessment and validation authorities
- added `scripts/docs-check.ps1` for missing-authority and freshness checks

### Outcome

- contributors and agents can resolve one authoritative document per responsibility
- current defects and debt are separated from future capability ideas
- material assessment and architecture claims now carry repository evidence
- documentation compliance is locally checkable without repository administration permissions

## Notes

- `README.md` in `upgrades/` is the resolved history authority
- `FUTURE-UPGRADES.md` is the repository authority for deferred improvements
- detailed implementation work remains routed through numbered spec folders under `specs/`

## Upgrade 004: Trading safety remediation

### Summary

Closed the validated order-routing, test-isolation, journal-correctness, runtime-data, dependency, and repository-protection findings from the 2026-09-28 assessment.

### Resolved defects

- BUG-001: BTC market orders now use GTC and carry the inbound signal ID as the Alpaca client order ID.
- BUG-002: PowerShell risk tests inject Pester temporary storage. The operational risk-state hash remained unchanged during the full suite.
- BUG-003: Authentication tests inject the HTTP implementation and cannot reach Alpaca.
- BUG-004: SQLite is authoritative. CSV import is explicit and skips database rows already represented in the export.
- BUG-005: Profit factor uses gross profit divided by gross loss and streak queries use deterministic order.
- BUG-006: Webhook actions are strict and validation logs never include the inbound payload or passphrase.

### Resolved debt

- TD-001: Every Python order-routing surface uses the shared fail-closed `PaperTradingClient` or the exact paper REST endpoint assertion.
- TD-002: Automated tests now cover the webhook, journal, scheduler wrapper, shared paper boundary, execution-surface adoption, and RSI order construction.
- TD-003: Runtime journal, report, log, database, and risk-state files were removed from Git tracking and ignored without deleting local files.
- TD-005: NumPy is pinned within numba's supported range, all three requirement sets install together, and CI runs `pip check`.
- TD-007: Dependabot alerts, automated security fixes, CodeQL default setup, strict required CI checks, conversation resolution, and force-push and deletion protection were enabled on `main`.

### Security boundary

The BTC webhook is paper-only. It enforces a ticker allowlist, finite quantity and notional caps, UTC freshness, persistent replay IDs, constant-time passphrase comparison, request rate limits, a buy-side failure circuit breaker, and a daily-loss limit. Sell and close requests remain available as risk-reducing actions when the buy breaker is open.

### Outcome

The repository remains paper-only. Live Python order routing cannot be enabled through an environment value or source constant. Enabling live execution requires a separate approved Class 4 design.

## Upgrade 005: Reproducible research and operations foundation

### Summary

Added repeatable strategy evaluation, local health reporting, coverage gates, a locked Python environment, real sanitized screenshots, and a guarded release workflow.

### What Changed

- added a fixed checksum-protected dataset and versioned evaluation configuration
- added transaction costs, a buy-and-hold benchmark, a fixed out-of-sample period, parameter selection on training data, and expanding-window walk-forward results
- added local JSON and HTML health reporting for stale files, rejected orders, missing protective stops, circuit-breaker state, and scheduler failures
- made both scheduler launchers publish a machine-readable last-run status
- added Python and PowerShell coverage reports with 50 percent and 40 percent minimums
- added a hash-verified Python 3.13 dependency lock and regeneration script
- replaced placeholder artwork with sanitized screenshots captured from the running local tools
- added full release validation and a guarded changelog, tag, push, and GitHub release script

### Resolved work

- FU-002: Reproducible strategy evaluation pipeline
- FU-003: Local operational status and alerting
- FU-004: Test coverage reporting
- FU-005: Tagged release snapshots
- TD-006: Strategy evaluation reproducibility
- TD-009: Python dependency reproducibility

### Outcome

The repository now has a deterministic baseline for comparing one EMA strategy, visible local operational failures, enforced coverage floors, repeatable installs, truthful screenshots, and a single documented release path. These controls do not claim profitability or replace paper-account supervision.

## Upgrade 006: GitHub repository hardening

### Summary

Enforced the repository's pull request, security scanning, merge, workflow dependency, vulnerability reporting, and release tag policies.

### What Changed

- protected `main` with required pull requests, zero approvals for the sole maintainer, administrator enforcement, strict current-branch checks, conversation resolution, and linear history
- required Python, PowerShell, documentation, and CodeQL checks before merge
- restricted Actions to reviewed GitHub-owned actions and required full commit SHA references
- pinned Pester 5.7.1 and PSScriptAnalyzer 1.24.0 exactly
- enabled squash-only merging, automatic source-branch deletion, and update-branch support
- added `SECURITY.md`, enabled private vulnerability reporting, and protected `v*` tags from update or deletion
- disabled unused Wiki and Projects features
- replaced reflected journal conversion errors with stable responses and rejected non-finite inputs and computed P&L before persistence

### Resolved work

- BUG-010: The two medium journal response alerts and three workflow permission alerts are fixed. The post-merge CodeQL scan reports zero open alerts.
- TD-008: Repository merge and quality gates now enforce the intended workflow, including administrators.

### Validation

Pull request 17 passed Python, PowerShell, documentation, and CodeQL checks before squash merge. Post-merge runs 36525657007 and 36525656614 passed on `main` commit `0e12e8eb121d13959e65aaab870cbca31e084154`.

### Outcome

Repository delivery now fails closed on the required quality and security checks. The trading boundary remains paper-only.

<!-- markdownlint-enable MD013 MD024 -->
