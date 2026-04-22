<!-- markdownlint-disable MD013 -->

# 001 Core Trading Foundation Requirements

## Change Summary

Retrofit the existing `Trading` repository into a spec-driven GitHub workflow without rebuilding or destabilizing the current Python and PowerShell trading toolkit.

## Current Baseline

The repository already contains:

- Alpaca paper-trading helpers in Python and PowerShell
- backtesting strategies and live-paper runners
- a Flask-based journal service with CSV and SQLite storage
- scheduler scripts
- a standalone RSI plus MACD bot
- a FastAPI BTC signal executor
- reusable PowerShell modules under `src/`
- Python and PowerShell tests under `Tests/`

The repository did not contain a `.github` spec workflow, reusable prompt assets, or CI automation before this retrofit.

## Functional Requirements

### FR-1 Repository Audit

The repo must include a concrete audit of the current codebase covering structure, purpose, languages, entry points, tests, documentation, and current gaps.

### FR-2 Spec Workflow Scaffolding

The repo must include GitHub Spec workflow assets for:

- requirements
- spec
- plan
- tasks
- implementation
- audit
- regression testing
- release readiness

### FR-3 Baseline Spec Package

The repo must include a first numbered spec package describing the current trading foundation as it exists today.

### FR-4 Repo-Specific Agent Guidance

The repo must include repository-specific Copilot or coding-agent instructions that reflect the current architecture, safety boundaries, and testing expectations.

### FR-5 README Alignment

The root `README.md` must describe the current repository behavior, current architecture, setup, usage, development flow, and the new GitHub Spec workflow.

### FR-6 CI Baseline

The repo must include a CI workflow that validates stable quality gates based on the actual stack already present in the repository.

### FR-7 Minimal Disruption

The retrofit must preserve existing source code and tracked runtime artifacts unless a change is clearly necessary for maintainability or workflow clarity.

### FR-8 Future-Work Routing

Future non-trivial repo work must be routed through numbered spec folders under `specs/`.

## Non-Functional Requirements

### NFR-1 Accuracy

All new documentation must reflect the current repo, not an imagined future product.

### NFR-2 Maintainability

New files must be structured for reuse by human contributors and AI coding agents.

### NFR-3 Safety

The retrofit must not change default paper-trading safety assumptions or imply live-trading readiness.

### NFR-4 Tool Compatibility

The repo must document or encode the current testing layout so local and CI workflows do not depend on unstated conventions.

## Non-Goals

- rewriting trading strategy logic
- consolidating Python and PowerShell into one stack
- renaming top-level feature folders
- fixing all existing PowerShell test debt in the same retrofit
- converting the repo into a deploy-on-merge production trading system

## Acceptance Signals

1. The repo contains `.github/`, `specs/001-core-trading-foundation/`, and updated root docs.
2. The README and audit documents describe the existing repo accurately.
3. CI is present and executable for the current stable verification path.
4. Future contributors can follow a clear requirements-to-audit workflow from files inside the repo.

<!-- markdownlint-enable MD013 -->
