<!-- markdownlint-disable MD013 MD024 MD060 -->

# Validation

This file is the authoritative validation procedure. Per-change results belong in the completion report, commit, or pull request. They do not accumulate here.

## Environment Requirements

- Python matching the supported CI version when release confidence is required. CI currently uses Python 3.13.
- PowerShell 7.
- Pester 5.5 or newer.
- PSScriptAnalyzer.
- No live Alpaca credentials in the default validation environment.

Create a clean virtual environment before dependency or release validation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt -r .\rsi_macd_bot\requirements.txt -r .\btc-signal-executor\requirements.txt
```

## Basic Validation

Use for documentation, internal tooling, and low-risk refactors.

### Python syntax

```powershell
python -m compileall -q Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor
```

Expected exit code: 0. Typical runtime: under one minute.

### Python unit tests

```powershell
python -m pytest .\Tests -q
```

Expected exit code: 0. Credential-dependent tests may skip. Every completion report must state the skip count and reason.

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
Import-Module PSScriptAnalyzer
$files = Get-ChildItem .\src,.\Alpaca,.\Backtesting,.\Scheduler,.\examples -Recurse -Include *.ps1,*.psm1 -File
$results = $files | ForEach-Object {
    Invoke-ScriptAnalyzer -Path $_.FullName -Settings .\PSScriptAnalyzerSettings.psd1
}
$results | Group-Object RuleName,Severity | Sort-Object Count -Descending
```

Expected result: no `Error` or `ParseError`. Existing warnings are tracked under TD-004 and must be reported, not hidden.

## Pester Isolation

Risk tests inject Pester's temporary test directory into `Initialize-AlpacaRisk`. Authentication tests inject a local request implementation into `Invoke-AlpacaRequest`. The default suite must not alter `Journal/alpaca_risk_state.json` or make an outbound request.

The command is:

```powershell
pwsh -NoProfile -Command "Import-Module Pester -MinimumVersion 5.5.0 -Force; Invoke-Pester -Path .\Tests -CI"
```

For changes to either injection boundary, compare the operational risk-state hash before and after the suite and inspect the test implementation for direct network calls.

## Integration Validation

Credential-dependent checks use an Alpaca paper account only:

```powershell
python -m pytest .\Tests\test_connection.py -v
```

Expected exit code: 0. Without `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`, the tests skip. Record that as a waiver for changes that require provider-contract assurance.

Do not submit orders merely to prove connectivity.

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
python -m pip check
```

Expected exit code: 0 in a clean supported environment. Dependabot and CodeQL provide hosted dependency and code scanning after changes reach GitHub.

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
- Backtest quality remains research grade. See TD-006.

<!-- markdownlint-enable MD013 MD024 MD060 -->
