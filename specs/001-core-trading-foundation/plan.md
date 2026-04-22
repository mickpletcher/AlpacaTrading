<!-- markdownlint-disable MD013 -->

# 001 Core Trading Foundation Plan

## Objective

Add a production-friendly spec workflow and baseline automation around the existing repository with minimal disruption to the current codebase.

## Assumptions

1. The current source code and tracked artifacts should remain intact.
2. Python verification in the repo virtualenv is the most stable current automated signal.
3. PowerShell module quality can be gated through manifest validation, import checks, and static analysis before Pester modernization.

## Phase 1 Documentation And Audit

### Work

- update `README.md`
- create `docs/repo-audit.md`
- create `pytest.ini`
- improve `.gitignore`

### File Touch List

- `README.md`
- `docs/repo-audit.md`
- `pytest.ini`
- `.gitignore`

### Validation

- confirm docs reflect actual folder structure and entry points
- confirm `pytest` resolves `Tests/` through `pytest.ini`

## Phase 2 Spec Workflow Scaffolding

### Work

- create `.github/copilot-instructions.md`
- create reusable prompt files
- create baseline numbered spec package

### File Touch List

- `.github/copilot-instructions.md`
- `.github/prompts/*.prompt.md`
- `specs/001-core-trading-foundation/*.md`

### Validation

- confirm prompts are repo-specific, not generic filler
- confirm the spec package reflects the current repository state

## Phase 3 CI Baseline

### Work

- add GitHub Actions workflow for Python and PowerShell quality

### File Touch List

- `.github/workflows/ci.yml`

### Validation

- verify the commands match currently available repo commands
- avoid gating on unstable or unmigrated PowerShell test surfaces

## Phase 4 Follow-Up Backlog Capture

### Work

- explicitly document deferred PowerShell test modernization
- capture non-blocking repo hardening items in the spec task list

### Validation

- ensure deferred work is visible and actionable

## Safety Notes

- Do not rename `Tests/` in this retrofit.
- Do not rewrite trading logic during scaffolding work.
- Do not treat current PowerShell Pester failures as incidental; capture them as intentional follow-up debt.

## Rollback Notes

If needed, this retrofit can be rolled back by removing the new `.github/`, `specs/`, `docs/repo-audit.md`, and `pytest.ini` files and restoring the previous `README.md` and `.gitignore` without affecting core runtime code.

<!-- markdownlint-enable MD013 -->
