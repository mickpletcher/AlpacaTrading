<#
Filename: run_gap_momentum.ps1
Purpose: PowerShell wrapper for Gap Up Momentum backtest and live workflows.
Author: TODO

Note: This strategy needs two Scheduled Tasks because it is time window dependent and intraday.
Task 1 launches before market open so the script can run the scan window logic from 9:30 to 9:45 ET.
Task 2 runs after close to confirm end of day exits and immediate log visibility.

Task 1 (morning launch, 9:25 AM ET):
$action1 = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Backtesting\strategies\run_gap_momentum.ps1`" -Mode live -Symbol SPY"
$trigger1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 9:25AM
Register-ScheduledTask -TaskName "TradingGapMomentumMorning" -Action $action1 -Trigger $trigger1 -Description "Gap Momentum morning launch."

Task 2 (EOD confirmation, 4:05 PM ET):
$action2 = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Backtesting\strategies\run_gap_momentum.ps1`" -Mode backtest -Symbol SPY"
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 4:05PM
Register-ScheduledTask -TaskName "TradingGapMomentumEod" -Action $action2 -Trigger $trigger2 -Description "Gap Momentum EOD confirmation and reporting."
#>

param(
    [ValidateSet("backtest", "live", "both")]
    [string]$Mode = "backtest",

    [string]$Symbol = "SPY",

    [string]$Start = "2024-01-01"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$journalLog = Join-Path $repoRoot "Journal\scheduler_log.txt"
$tradesPath = Join-Path $repoRoot "Journal\trades.csv"

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
        return @{ FilePath = $venvPython; ParamList = @() }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ FilePath = "python"; ParamList = @() }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ FilePath = "py"; ParamList = @("-3") }
    }

    throw "Python was not found in PATH."
}

function Test-AlpacaCredentials {
    $apiKey = $env:ALPACA_API_KEY
    $secretKey = $env:ALPACA_SECRET_KEY
    return -not ([string]::IsNullOrWhiteSpace($apiKey) -or [string]::IsNullOrWhiteSpace($secretKey))
}

function Show-TodaysGapRows {
    if (-not (Test-Path $tradesPath)) {
        Write-Host "Journal/trades.csv not found."
        return
    }

    $today = (Get-Date).ToString("yyyy-MM-dd")
    $rows = Import-Csv -Path $tradesPath | Where-Object {
        $_.date -eq $today -and $_.notes -match "gap_momentum"
    }

    if (-not $rows) {
        Write-Host "No gap momentum rows found for today."
        return
    }

    Write-Host "Today gap momentum rows"
    $rows | Format-Table date,symbol,side,qty,entry_price,exit_price,pnl,notes -AutoSize
}

New-Item -ItemType Directory -Path (Split-Path $journalLog -Parent) -Force | Out-Null
Import-DotEnv -Path (Join-Path $repoRoot ".env")

$backtestScript = Join-Path $PSScriptRoot "backtest_gap_momentum.py"
$liveScript = Join-Path $PSScriptRoot "live_gap_momentum.py"
$exitCode = 0
$python = Get-PythonCommand

Write-SchedulerLog "run_gap_momentum.ps1 started | mode=$Mode | symbol=$Symbol"

try {
    if (-not (Test-AlpacaCredentials)) {
        Write-Host "ALPACA_API_KEY or ALPACA_SECRET_KEY was not found. Skipping gap momentum run."
        $exitCode = 0
    }
    elseif ($Mode -eq "backtest") {
        $backtestArgs = @($python.ParamList + @($backtestScript, "--symbol", $Symbol, "--start", $Start))
        & $python.FilePath @backtestArgs | Out-Host
        $exitCode = [int]$LASTEXITCODE
    }
    elseif ($Mode -eq "live") {
        $liveArgs = @($python.ParamList + @($liveScript))
        & $python.FilePath @liveArgs | Out-Host
        $exitCode = [int]$LASTEXITCODE
    }
    else {
        $backtestArgs = @($python.ParamList + @($backtestScript, "--symbol", $Symbol, "--start", $Start))
        & $python.FilePath @backtestArgs | Out-Host
        $backtestCode = [int]$LASTEXITCODE
        if ($backtestCode -ne 0) {
            Write-Host "Backtest failed. Live run skipped."
            $exitCode = $backtestCode
        }
        else {
            $confirmation = Read-Host "Type YES to proceed to live trading"
            if ($confirmation -eq "YES") {
                $liveArgs = @($python.ParamList + @($liveScript))
                & $python.FilePath @liveArgs | Out-Host
                $exitCode = [int]$LASTEXITCODE
            }
            else {
                Write-Host "Live run cancelled by user."
                $exitCode = 0
            }
        }
    }

    Show-TodaysGapRows
}
finally {
    Write-SchedulerLog "run_gap_momentum.ps1 completed | mode=$Mode | symbol=$Symbol | exit_code=$exitCode"
}

exit $exitCode
