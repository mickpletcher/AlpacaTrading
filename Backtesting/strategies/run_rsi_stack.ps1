<#
Filename: run_rsi_stack.ps1
Purpose: Run RSI Stack workflows for backtest and live modes.
Author: TODO

Scheduled Task example:
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Backtesting\strategies\run_rsi_stack.ps1`" -Mode backtest -Symbol SPY -Start 2023-01-01 -FastTF 1Hour -SlowTF 1Day"
$triggerOpen = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 9:25AM
$triggerClose = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 4:05PM
Register-ScheduledTask -TaskName "TradingRsiStackWorkflow" -Action $action -Trigger @($triggerOpen, $triggerClose) -Description "Run RSI stack workflow near open and close."
#>

param(
    [ValidateSet("backtest", "live", "both")]
    [string]$Mode = "backtest",

    [string]$Symbol = "SPY",

    [string]$Start = "2023-01-01",

    [string]$FastTF = "1Hour",

    [string]$SlowTF = "1Day"
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

Write-SchedulerLog "run_rsi_stack.ps1 started | mode=$Mode | symbol=$Symbol | fast_tf=$FastTF | slow_tf=$SlowTF"

$backtestScript = Join-Path $PSScriptRoot "backtest_rsi_stack.py"
$liveScript = Join-Path $PSScriptRoot "live_rsi_stack.py"
$exitCode = 0

try {
    if (-not (Test-AlpacaCredentials)) {
        Write-Host "ALPACA_API_KEY or ALPACA_SECRET_KEY was not found. Skipping RSI Stack run."
        $exitCode = 0
    }
    elseif ($Mode -eq "backtest") {
        $exitCode = Invoke-PythonScript -ScriptPath $backtestScript -Args @("--symbol", $Symbol, "--start", $Start, "--fast-tf", $FastTF, "--slow-tf", $SlowTF)
    }
    elseif ($Mode -eq "live") {
        $exitCode = Invoke-PythonScript -ScriptPath $liveScript -Args @()
    }
    else {
        $backtestCode = Invoke-PythonScript -ScriptPath $backtestScript -Args @("--symbol", $Symbol, "--start", $Start, "--fast-tf", $FastTF, "--slow-tf", $SlowTF)
        if ($backtestCode -ne 0) {
            Write-Host "Backtest failed. Live run skipped."
            $exitCode = $backtestCode
        }
        else {
            $confirmation = Read-Host "Type YES to proceed to live trading: "
            if ($confirmation -eq "YES") {
                $exitCode = Invoke-PythonScript -ScriptPath $liveScript -Args @()
            }
            else {
                Write-Host "Live run cancelled by user."
                $exitCode = 0
            }
        }
    }
}
finally {
    Write-SchedulerLog "run_rsi_stack.ps1 completed | mode=$Mode | symbol=$Symbol | fast_tf=$FastTF | slow_tf=$SlowTF | exit_code=$exitCode"
}

exit $exitCode
