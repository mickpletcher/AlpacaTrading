<!-- markdownlint-disable MD013 -->

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

## Notes

- `README.md` in `upgrades/` is for completed or intentionally applied upgrades
- `future-upgrades.md` is for backlog planning and local prioritization
- detailed implementation work for future upgrades should still be routed through numbered spec folders under `specs/`

<!-- markdownlint-enable MD013 -->
