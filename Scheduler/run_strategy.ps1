<#
Filename: run_strategy.ps1
Purpose: Load local secrets and launch the scheduled paper trading strategy on Windows.
Author: TODO

Register as a Scheduled Task example:
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Scheduler\run_strategy.ps1`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 9:25AM
Register-ScheduledTask -TaskName "TradingPaperStrategy" -Action $action -Trigger $trigger -Description "Run the paper trading strategy near the US market open."
#>

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
$envPath = Join-Path $repoRoot ".env"
$strategyPath = Join-Path $repoRoot "Alpaca\paper_trade.py"
$logPath = Join-Path $repoRoot "Journal\scheduler_log.txt"
$statusPath = Join-Path $repoRoot "Journal\scheduler_status.json"

function Write-SchedulerLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ssK"
    Add-Content -Path $logPath -Value "$timestamp`t$Message"
}

function Import-DotEnv {
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

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
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ FilePath = "python"; Arguments = @() }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ FilePath = "py"; Arguments = @("-3") }
    }

    throw "Python was not found in PATH."
}

function Write-SchedulerStatus {
    param(
        [Parameter(Mandatory)]
        [datetime]$StartedAt,
        [AllowNull()]
        [Nullable[datetime]]$FinishedAt,
        [AllowNull()]
        [Nullable[int]]$ExitCode,
        [string]$ErrorMessage = ""
    )

    $payload = [ordered]@{
        schema_version = 1
        started_at = $StartedAt.ToUniversalTime().ToString("o")
        finished_at = if ($null -ne $FinishedAt) { $FinishedAt.Value.ToUniversalTime().ToString("o") } else { "" }
        exit_code = $ExitCode
        error = $ErrorMessage
    }
    $payload | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding utf8
}

New-Item -ItemType Directory -Path (Split-Path $logPath -Parent) -Force | Out-Null
$startedAt = Get-Date
$exitCode = 1
$errorMessage = ""
$stdoutPath = Join-Path $env:TEMP ("trading_scheduler_stdout_{0}.log" -f ([guid]::NewGuid().ToString()))
$stderrPath = Join-Path $env:TEMP ("trading_scheduler_stderr_{0}.log" -f ([guid]::NewGuid().ToString()))
Write-SchedulerStatus -StartedAt $startedAt -FinishedAt $null -ExitCode $null

try {
    Import-DotEnv -Path $envPath
    $python = Get-PythonCommand
    Write-SchedulerLog -Message ("Starting strategy: {0}" -f $strategyPath)
    $argumentList = @($python.Arguments + @($strategyPath))
    $process = Start-Process -FilePath $python.FilePath -ArgumentList $argumentList -WorkingDirectory $repoRoot -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stderr = if (Test-Path $stderrPath) { (Get-Content -Path $stderrPath -Raw).Trim() } else { "" }

    $exitCode = $process.ExitCode
    Write-SchedulerLog -Message ("ExitCode={0}" -f $exitCode)
    if ($stderr) {
        Write-SchedulerLog -Message ("STDERR: {0}" -f $stderr)
    }
}
catch {
    $errorMessage = $_.Exception.Message
    Write-SchedulerLog -Message ("FAILED: {0}" -f $errorMessage)
}
finally {
    Write-SchedulerStatus -StartedAt $startedAt -FinishedAt (Get-Date) -ExitCode $exitCode -ErrorMessage $errorMessage
    foreach ($tempFile in @($stdoutPath, $stderrPath)) {
        if (Test-Path $tempFile) {
            Remove-Item -Path $tempFile -Force
        }
    }
}

exit $exitCode
