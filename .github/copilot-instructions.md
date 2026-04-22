# Trading Repository Copilot Instructions

## Scope

This repository is an existing mixed Python and PowerShell trading toolkit. Treat it as a retrofit-first codebase, not a greenfield project.

## Core Rules

1. Preserve existing working trading, backtesting, journal, and scheduler code unless a change is explicitly required.
2. Favor additive changes over rewrites.
3. Default all execution and examples to Alpaca paper-trading mode unless a spec explicitly states otherwise.
4. Keep module boundaries intact:
   - reusable PowerShell API and risk logic belongs in `src/`
   - script-style entry points belong in their existing feature folders
   - journal concerns stay in `Journal/`
   - strategy logic stays in `Backtesting/strategies/`
5. Do not silently invent product capabilities that are not already present in the repo.

## Architecture Rules

- Reuse the PowerShell modules under `src/` rather than duplicating Alpaca API calls in new `.ps1` files.
- Keep strategy implementations decoupled from the journal UI.
- Keep scheduler scripts thin. They should orchestrate existing modules or scripts, not own business logic.
- Preserve separate runtime surfaces for:
  - backtesting
  - paper trading
  - journaling
  - webhook execution
  - standalone bots

## Naming Conventions

- Python files use `snake_case.py`.
- PowerShell modules and scripts use `Verb-Noun` style for functions and descriptive PascalCase-ish file names where the repo already follows PowerShell conventions.
- New specs use `specs/NNN-short-kebab-name/`.
- New docs should describe the current behavior first, then proposed changes.

## Testing Expectations

- Python changes should keep `.\.venv\Scripts\python.exe -m pytest .\Tests -q` passing when the change affects Python code.
- PowerShell changes should preserve module importability and manifest validity.
- When touching PowerShell parsing, auth, config, or risk code, update or add tests in `Tests/*.Tests.ps1`.
- Avoid depending on live credentials in default CI checks.

## Refactor Safety Rules

- Do not rename top-level product folders without an explicit migration task.
- Do not collapse the mixed Python and PowerShell architecture into a single stack.
- Do not remove tracked generated artifacts during routine feature work unless the spec explicitly includes that cleanup.
- Treat `Tests/` as the current canonical automated test directory even though its capitalization is nonstandard.

## Documentation Rules

- Keep the root `README.md` aligned with the actual repository contents.
- Update module docs when entry points or commands change.
- Record significant repo-shaping work under `specs/`.

## Spec-Driven Delivery Requirement

All future non-trivial work must align to a spec package:

1. Create or update `requirements.md`
2. Create or update `spec.md`
3. Create or update `plan.md`
4. Create or update `tasks.md`
5. Implement only what the spec covers
6. Audit the implementation against the spec
7. Run regression checks before merge

If code and spec disagree, update one of them deliberately. Do not leave them drifting.
