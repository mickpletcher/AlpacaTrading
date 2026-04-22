<!-- markdownlint-disable MD013 -->

# 001 Core Trading Foundation Spec

## Scope

Add a spec-driven repository workflow around the current codebase while preserving the existing trading, backtesting, journaling, and automation modules.

## Baseline Architecture

The repository is a multi-surface toolkit with these stable boundaries:

- `src/`: reusable PowerShell Alpaca client, stream, and risk modules
- `Alpaca/`: Python and PowerShell paper-trading entry points
- `Backtesting/`: research and runner scripts for multiple strategies
- `Journal/`: trade journal web UI and reporting tools
- `Scheduler/`: launchers for recurring execution
- `rsi_macd_bot/`: standalone Python bot
- `btc-signal-executor/`: standalone FastAPI webhook service
- `Tests/`: Python and PowerShell verification

## Proposed Design

### 1. Repository Workflow Layer

Introduce a repository workflow layer composed of:

- `.github/copilot-instructions.md`
- `.github/prompts/*.prompt.md`
- `.github/workflows/ci.yml`
- `specs/001-core-trading-foundation/*`

This layer governs future changes without changing the current runtime architecture.

### 2. Documentation Alignment

Update root documentation to:

- describe the real current modules
- describe stable setup and verification commands
- explain the new spec workflow
- document known verification gaps rather than hiding them

### 3. Test Path Normalization

Add `pytest.ini` so Python tooling uses the existing `Tests/` directory explicitly.

### 4. CI Strategy

Implement CI in two tracks:

- Python quality:
  - install dependencies
  - compile Python packages
  - run `pytest` against `Tests/`
- PowerShell quality:
  - validate module manifests
  - import modules
  - run `PSScriptAnalyzer`

CI intentionally does not gate on the current PowerShell Pester suite yet because that suite requires a dedicated compatibility modernization effort.

## Impacted Files And Folders

- `README.md`
- `.gitignore`
- `pytest.ini`
- `docs/repo-audit.md`
- `.github/copilot-instructions.md`
- `.github/prompts/*.prompt.md`
- `.github/workflows/ci.yml`
- `specs/001-core-trading-foundation/*.md`

## Data And Control Flow

No runtime trading data flow changes are introduced.

The only new control flow is development-process flow:

1. contributor creates or updates spec package
2. contributor implements change
3. contributor audits implementation
4. contributor runs regression checks
5. CI validates the stable automated baseline

## Compatibility Notes

- Existing Python and PowerShell entry points remain unchanged.
- Existing generated journal artifacts remain in place.
- The mixed-stack architecture remains the supported model.
- `Tests/` remains the canonical automated test folder for now.

## Risks

1. Over-tightening CI around PowerShell tests would create false negatives before the Pester suite is modernized.
2. Renaming `Tests/` in this retrofit would create avoidable path churn and platform-specific risk.
3. Broad doc edits could drift from code if not grounded in actual file inspection.

## Verification Strategy

### Required

- `python -m compileall Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor`
- `.\.venv\Scripts\python.exe -m pytest .\Tests -q`

### CI Required

- Python dependency install
- Python compile check
- Python `pytest`
- PowerShell module manifest validation
- PowerShell module import smoke check
- PowerShell script analysis

### Deferred

- Modernized Pester execution under a single supported Pester version

## Out Of Scope

- strategy refactors
- journal schema redesign
- webhook executor behavior changes
- bot logic changes
- live-trading enablement

<!-- markdownlint-enable MD013 -->
