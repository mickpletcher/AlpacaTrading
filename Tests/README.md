<!-- markdownlint-disable MD013 MD024 MD060 -->

# Validation

This file is the authoritative validation procedure. Per-change results belong in the completion report, commit, or pull request. They do not accumulate here.

Validation means running repeatable checks that catch syntax errors, broken behavior, invalid PowerShell modules, dependency conflicts, and documentation gaps. A passing test suite reduces risk, but it does not prove that a strategy is profitable or that Alpaca will accept every paper order.

## Beginner Quick Check

Run this from the repository root after setup:

```powershell
.\.venv\Scripts\python.exe -m compileall -q Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor Operations Tests
.\.venv\Scripts\python.exe -m pytest .\Tests -q --cov --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=50
.\.venv\Scripts\python.exe -m pip check
pwsh -NoProfile -File .\scripts\docs-check.ps1 -FailOnGap
```

How to read the result:

- `passed` means a test completed successfully.
- `failed` means the change should not be treated as ready.
- `skipped` means a test intentionally did not run. The normal reason here is missing paper credentials.
- a warning is not the same as a failure, but it still needs review.
- an exit code of `0` means the command reported success.

These default Python checks do not submit orders.

## Environment Requirements

- Python matching the supported CI version when release confidence is required. CI currently uses Python 3.13.
- PowerShell 7.
- Pester 5.5 or newer.
- PSScriptAnalyzer.
- No live Alpaca credentials in the default validation environment.

Install the PowerShell validation modules once for the current user if they are not already available:

```powershell
Install-Module Pester -MinimumVersion 5.5.0 -Scope CurrentUser -Force
Install-Module PSScriptAnalyzer -MinimumVersion 1.24.0 -Scope CurrentUser -Force
```

Create a clean virtual environment before dependency or release validation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --require-hashes -r .\requirements.lock.txt
```

If the requirement files changed after `.venv` was created, refresh the environment with the install command again or delete and recreate the environment yourself. `pip check` only checks what is currently installed.

## Basic Validation

Use for documentation, internal tooling, and low-risk refactors.

### Python syntax

```powershell
python -m compileall -q Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor Operations Tests
```

Expected exit code: 0. Typical runtime: under one minute.

### Python unit tests

```powershell
python -m pytest .\Tests -q --cov --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=50
```

Expected exit code: 0. Credential-dependent tests may skip. Every completion report must state the skip count and reason.

The Python suite must maintain at least 50 percent total statement coverage. CI uploads `coverage.xml` so gaps can be reviewed without changing the threshold blindly.

The tests use fake clients and temporary files for normal order, risk, journal, and webhook checks. They do not need real credentials.

### PowerShell module validation

```powershell
$repoSrc = (Resolve-Path .\src).Path
$env:PSModulePath = "$repoSrc$([IO.Path]::PathSeparator)$env:PSModulePath"
Get-ChildItem .\src -Recurse -Filter *.psd1 -File | ForEach-Object {
    Test-ModuleManifest -Path $_.FullName | Out-Null
}
Get-ChildItem .\src -Directory | ForEach-Object {
    Import-Module $_.Name -Force
}
```

Expected exit code: 0 with no import errors.

### Documentation compliance

```powershell
pwsh -NoProfile -File .\scripts\docs-check.ps1 -FailOnGap
```

Expected exit code: 0 with no `MISSING` or `REVIEW` rows.

## Full Static Validation

```powershell
pwsh -NoProfile -File .\scripts\Invoke-PowerShellStaticAnalysis.ps1
```

Expected result: no `Error` or `ParseError`. Existing warnings are tracked under TD-004 and must be reported, not hidden.

## Pester Isolation

Risk tests inject Pester's temporary test directory into `Initialize-AlpacaRisk`. Authentication tests inject a local request implementation into `Invoke-AlpacaRequest`. The default suite must not alter `Journal/alpaca_risk_state.json` or make an outbound request.

The command is:

```powershell
pwsh -NoProfile -Command "$config=New-PesterConfiguration; $config.Run.Path='.\Tests'; $config.Run.Exit=$true; $config.CodeCoverage.Enabled=$true; $config.CodeCoverage.Path=@('.\src\*\*.psm1'); $config.CodeCoverage.OutputFormat='JaCoCo'; $config.CodeCoverage.OutputPath='powershell-coverage.xml'; $config.CodeCoverage.CoveragePercentTarget=40; Invoke-Pester -Configuration $config"
```

For changes to either injection boundary, compare the operational risk-state hash before and after the suite and inspect the test implementation for direct network calls.

The PowerShell suite must maintain at least 40 percent command coverage across the reusable modules in `src/`. CI uploads `powershell-coverage.xml`.

## Integration Validation

Credential-dependent checks use an Alpaca paper account only:

```powershell
python -m pytest .\Tests\test_connection.py -v
```

Expected exit code: 0. Without `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`, the tests skip. Record that as a waiver for changes that require provider-contract assurance.

Do not submit orders merely to prove connectivity.

Connectivity proves only that the credentials and endpoint respond. It does not prove that order sizing, protection, exits, or strategy logic are correct.

## Component Validation

| Component | Automated validation | Additional procedure |
|---|---|---|
| Shared strategies | `Tests/test_*.py` | Run the affected backtest with synthetic or paper data |
| PowerShell modules | Manifests, imports, analyzer, isolated Pester | Use examples only with paper credentials |
| Journal | `Tests/test_journal.py` | Preserve data and start locally for UI checks |
| Scheduler | `Tests/test_scheduler.py` | Run manually under the intended account and inspect exit log |
| RSI and MACD bot | `Tests/test_execution_surfaces.py`, `Tests/test_trading_safety.py` | Paper-only dry run and log review |
| BTC executor | `Tests/test_btc_signal_executor.py`, `Tests/test_trading_safety.py` | Use fake clients by default; paper integration requires dedicated credentials |

## Dependency Validation

```powershell
python -m pip install --require-hashes -r .\requirements.lock.txt
python -m pip check
```

Expected exit code: 0 in a clean supported environment. Dependabot and CodeQL provide hosted dependency and code scanning after changes reach GitHub.

When a direct requirement changes, regenerate the reviewed lock from Python 3.13:

```powershell
pwsh -NoProfile -File .\scripts\Update-PythonLock.ps1
```

## Validation Matrix

| Change type | Class | Unit | Integration | Security | Smoke |
|---|---|---|---|---|---|
| Documentation only | 1 | No | No | No | Documentation check |
| Internal refactor | 2 | Yes | As needed | No | Yes |
| Test-only | 2 | Target suite | No | No | As needed |
| Bug fix | 3 | Yes | As needed | As needed | Yes |
| Interface or configuration | 3 | Yes | Yes | As needed | Yes |
| Dependency | 3 | Yes | Yes | Yes | Yes |
| Architecture, security, deployment | 4 | Yes | Yes | Yes | Yes |

## Known Validation Limitations

- Live Alpaca integration is absent from default checks because credentials are intentionally unavailable.
- Distributed webhook rate limiting and replay storage are not tested because the service is currently single-process.
- The fixed reproducible evaluator covers one EMA strategy and one synthetic daily dataset. Other strategy backtests still use their existing data sources and assumptions.
- The RSI plus MACD suite does not yet cover the complete entry, protective-stop, cancellation, exit, partial-fill, and recovery lifecycle. See BUG-007.
- The journal suite does not yet include stored HTML injection regression cases. See BUG-009.
- Coverage thresholds are repository-wide starting points. Safety-critical order lifecycle paths still need focused regression coverage as defects are fixed.

<!-- markdownlint-enable MD013 MD024 MD060 -->
