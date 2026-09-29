[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv with Python 3.13 before regenerating the lock.'
}

& $pythonPath -m pip install --upgrade 'pip-tools==7.6.1'
if ($LASTEXITCODE -ne 0) {
    throw 'pip-tools installation failed.'
}

Push-Location $repoRoot
try {
    & $pythonPath -m piptools compile `
        --generate-hashes `
        --allow-unsafe `
        --resolver=backtracking `
        --strip-extras `
        --output-file=requirements.lock.txt `
        requirements.txt `
        requirements-dev.txt `
        rsi_macd_bot/requirements.txt `
        btc-signal-executor/requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw 'Lock generation failed.'
    }

    & $pythonPath -m pip install --require-hashes -r requirements.lock.txt
    if ($LASTEXITCODE -ne 0) {
        throw 'Locked dependency installation failed.'
    }

    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) {
        throw 'Locked dependency validation failed.'
    }
}
finally {
    Pop-Location
}
