#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$ConfigPath = '.docs-authority.json',
    [switch]$FailOnGap,
    [switch]$Markdown
)

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    Write-Error "Authority map not found at $ConfigPath."
    exit 1
}

try {
    $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json -ErrorAction Stop
}
catch {
    Write-Error "Authority map is not valid JSON: $($_.Exception.Message)"
    exit 1
}

$maxDrift = if ($config.maxDriftDays) { [int]$config.maxDriftDays } else { 30 }

function Get-LastCommitDate {
    param([string]$Path)

    $iso = git log -1 --format=%cI -- $Path 2>$null
    if ([string]::IsNullOrWhiteSpace($iso)) {
        return $null
    }
    return [datetime]::Parse($iso)
}

function Test-UncommittedPath {
    param([string]$Path)

    $status = git status --porcelain -- $Path 2>$null
    return -not [string]::IsNullOrWhiteSpace(($status -join "`n"))
}

$sourceDate = $config.sourcePaths |
    ForEach-Object { Get-LastCommitDate -Path $_ } |
    Where-Object { $null -ne $_ } |
    Sort-Object -Descending |
    Select-Object -First 1

$rows = foreach ($property in $config.responsibilities.PSObject.Properties) {
    $name = $property.Name
    $entry = $property.Value
    $authority = [string]$entry.authority
    $class = [string]$entry.class

    if ($authority -in @('Not required at this tier', 'External tracker')) {
        [pscustomobject]@{ Responsibility = $name; Authority = $authority; LastUpdated = ''; Status = 'N/A' }
        continue
    }

    if (-not (Test-Path -LiteralPath $authority)) {
        [pscustomobject]@{ Responsibility = $name; Authority = $authority; LastUpdated = ''; Status = 'MISSING' }
        continue
    }

    $docDate = Get-LastCommitDate -Path $authority
    $isDirty = Test-UncommittedPath -Path $authority
    $updated = if ($isDirty -or -not $docDate) { 'uncommitted' } else { $docDate.ToString('yyyy-MM-dd') }

    if ($class -ne 'living' -or $isDirty -or -not $sourceDate -or -not $docDate) {
        [pscustomobject]@{ Responsibility = $name; Authority = $authority; LastUpdated = $updated; Status = 'Current' }
        continue
    }

    $drift = [int]($sourceDate - $docDate).TotalDays
    $status = if ($drift -gt $maxDrift) { "REVIEW (${drift}d)" } else { 'Current' }
    [pscustomobject]@{ Responsibility = $name; Authority = $authority; LastUpdated = $updated; Status = $status }
}

if ($Markdown) {
    '| Responsibility | Authority | Last updated | Status |'
    '|---|---|---|---|'
    $rows | ForEach-Object { "| $($_.Responsibility) | $($_.Authority) | $($_.LastUpdated) | $($_.Status) |" }
}
else {
    $rows | Format-Table -AutoSize
}

$gaps = $rows | Where-Object { $_.Status -eq 'MISSING' -or $_.Status -like 'REVIEW*' }
if ($gaps -and $FailOnGap) {
    exit 1
}
