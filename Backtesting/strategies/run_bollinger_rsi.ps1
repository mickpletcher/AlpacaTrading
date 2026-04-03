<#
Filename: run_bollinger_rsi.ps1
Purpose: Run Bollinger Bands plus RSI workflows for backtest and live modes.
Author: TODO

Scheduled Task example:
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Backtesting\strategies\run_bollinger_rsi.ps1`" -Mode backtest -Symbol SPY -Start 2022-01-01"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 9:25AM
Register-ScheduledTask -TaskName "TradingBollingerRsiWorkflow" -Action $action -Trigger $trigger -Description "Run Bollinger plus RSI strategy workflow."
#>

param(
    [ValidateSet("backtest", "live", "both")]
    [string]$Mode = "backtest",

    [string]$Symbol = "SPY",

    [string]$Start = "2022-01-01"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$journalLog = Join-Path $repoRoot "Journal\scheduler_log.txt"

function Write-SchedulerLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ssK"
    Add-Content -Path $journalLog -Value "$timestamp`t$Message"
}

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        if ($value -match "^(.*?)(\s+#.*)$") {
            $value = $matches[1].TrimEnd()
        }

        [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Get-PythonCommand {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return @{ FilePath = $venvPython; Arguments = @() }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ FilePath = "python"; Arguments = @() }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ FilePath = "py"; Arguments = @("-3") }
    }

    throw "Python was not found in PATH."
}

function Test-AlpacaCredentials {
    $apiKey = $env:ALPACA_API_KEY
    $secretKey = $env:ALPACA_SECRET_KEY
    return -not ([string]::IsNullOrWhiteSpace($apiKey) -or [string]::IsNullOrWhiteSpace($secretKey))
}

function Invoke-PythonScript {
    param(
        [string]$ScriptPath,
        [string[]]$Args
    )

    $python = Get-PythonCommand
    $allArgs = @($python.Arguments + @($ScriptPath) + $Args)
    & $python.FilePath @allArgs | Out-Host
    return [int]$LASTEXITCODE
}

New-Item -ItemType Directory -Path (Split-Path $journalLog -Parent) -Force | Out-Null
Import-DotEnv -Path (Join-Path $repoRoot ".env")

Write-SchedulerLog "run_bollinger_rsi.ps1 started | mode=$Mode | symbol=$Symbol"

$backtestScript = Join-Path $PSScriptRoot "backtest_bollinger_rsi.py"
$liveScript = Join-Path $PSScriptRoot "live_bollinger_rsi.py"
$exitCode = 0

try {
    if (-not (Test-AlpacaCredentials)) {
        Write-Host "ALPACA_API_KEY or ALPACA_SECRET_KEY was not found. Skipping Bollinger RSI run."
        $exitCode = 0
    }
    elseif ($Mode -eq "backtest") {
        $exitCode = Invoke-PythonScript -ScriptPath $backtestScript -Args @("--symbol", $Symbol, "--start", $Start)
    }
    elseif ($Mode -eq "live") {
        $exitCode = Invoke-PythonScript -ScriptPath $liveScript -Args @("--symbol", $Symbol)
    }
    else {
        $backtestCode = Invoke-PythonScript -ScriptPath $backtestScript -Args @("--symbol", $Symbol, "--start", $Start)
        if ($backtestCode -ne 0) {
            Write-Host "Backtest failed. Live run skipped."
            $exitCode = $backtestCode
        }
        else {
            $confirmation = Read-Host "Backtest completed. Run live mode now? (y/n)"
            if ($confirmation -match "^[Yy]$") {
                $exitCode = Invoke-PythonScript -ScriptPath $liveScript -Args @("--symbol", $Symbol)
            }
            else {
                Write-Host "Live run cancelled by user."
                $exitCode = 0
            }
        }
    }
}
finally {
    Write-SchedulerLog "run_bollinger_rsi.ps1 completed | mode=$Mode | symbol=$Symbol | exit_code=$exitCode"
}

exit $exitCode
