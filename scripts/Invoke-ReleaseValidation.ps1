[CmdletBinding()]
param(
    [ValidateRange(1, 100)]
    [int]$PythonCoverageMinimum = 50,
    [ValidateRange(1, 100)]
    [int]$PowerShellCoverageMinimum = 40,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'

function Import-ValidationModule {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [Parameter(Mandatory)]
        [version]$MinimumVersion
    )

    $localManifest = Get-ChildItem -LiteralPath (Join-Path $repoRoot ".tools\$Name") -Filter "$Name.psd1" -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object { [version]$_.Directory.Name } -Descending |
        Select-Object -First 1
    if ($localManifest -and [version]$localManifest.Directory.Name -ge $MinimumVersion) {
        Import-Module $localManifest.FullName -Force
        return
    }
    Import-Module $Name -MinimumVersion $MinimumVersion -Force
}

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv with Python 3.13 before release validation.'
}

Push-Location $repoRoot
try {
    if (-not $SkipInstall) {
        & $pythonPath -m pip install --require-hashes -r requirements.lock.txt
        if ($LASTEXITCODE -ne 0) { throw 'Locked dependency installation failed.' }
    }

    & $pythonPath -m compileall -q Alpaca Backtesting Journal rsi_macd_bot btc-signal-executor Operations Tests
    if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed.' }

    & $pythonPath -m pytest .\Tests -q --disable-warnings --cov --cov-config=.coveragerc --cov-report=term:skip-covered --cov-report=xml:coverage.xml --cov-fail-under=$PythonCoverageMinimum
    if ($LASTEXITCODE -ne 0) { throw 'Python tests or coverage threshold failed.' }

    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency validation failed.' }
    Write-Output 'Python validation passed.'

    $repoSrc = (Resolve-Path .\src).Path
    $env:PSModulePath = "$repoSrc$([IO.Path]::PathSeparator)$env:PSModulePath"
    Get-ChildItem .\src -Recurse -Filter *.psd1 -File | ForEach-Object {
        Test-ModuleManifest -Path $_.FullName | Out-Null
    }
    Get-ChildItem .\src -Directory | ForEach-Object {
        Import-Module $_.Name -Force
    }
    Write-Output 'PowerShell manifests and imports passed.'

    pwsh -NoProfile -File .\scripts\Invoke-PowerShellStaticAnalysis.ps1
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell static analysis failed.' }
    Write-Output 'PowerShell static analysis passed.'

    Import-ValidationModule -Name Pester -MinimumVersion 5.5.0
    Write-Output 'Pester loaded.'
    $configuration = New-PesterConfiguration
    $configuration.Run.Path = '.\Tests'
    $configuration.Run.PassThru = $true
    $configuration.Output.Verbosity = 'Normal'
    $configuration.CodeCoverage.Enabled = $true
    $configuration.CodeCoverage.Path = @('.\src\*\*.psm1')
    $configuration.CodeCoverage.OutputFormat = 'JaCoCo'
    $configuration.CodeCoverage.OutputPath = '.\powershell-coverage.xml'
    $configuration.CodeCoverage.CoveragePercentTarget = $PowerShellCoverageMinimum
    $result = Invoke-Pester -Configuration $configuration
    if ($result.FailedCount -gt 0 -or $result.Result -ne 'Passed') {
        throw 'PowerShell tests or coverage threshold failed.'
    }
    Write-Output "PowerShell tests passed: $($result.PassedCount) tests, $([math]::Round($result.CodeCoverage.CoveragePercent, 2)) percent coverage."

    pwsh -NoProfile -File .\scripts\docs-check.ps1 -FailOnGap
    if ($LASTEXITCODE -ne 0) { throw 'Documentation authority validation failed.' }
    Write-Output 'Documentation authority validation passed.'

    git diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Whitespace validation failed.' }
    Write-Output 'Whitespace validation passed.'

    Write-Output 'Release validation passed.'
}
finally {
    Pop-Location
}
