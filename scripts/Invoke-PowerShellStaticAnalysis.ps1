[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$localManifest = Get-ChildItem -LiteralPath (Join-Path $repoRoot '.tools\PSScriptAnalyzer') -Filter 'PSScriptAnalyzer.psd1' -File -Recurse -ErrorAction SilentlyContinue |
    Sort-Object { [version]$_.Directory.Name } -Descending |
    Select-Object -First 1

if ($localManifest -and [version]$localManifest.Directory.Name -ge [version]'1.24.0') {
    Import-Module $localManifest.FullName -Force
}
else {
    Import-Module PSScriptAnalyzer -MinimumVersion 1.24.0 -Force
}

Push-Location $repoRoot
try {
    $powershellFiles = Get-ChildItem .\src,.\Alpaca,.\Backtesting,.\Scheduler,.\examples -Recurse -Include *.ps1,*.psm1 -File
    if (-not $powershellFiles) {
        throw 'No PowerShell files were found for analysis.'
    }
    $analysis = @($powershellFiles | ForEach-Object {
        Invoke-ScriptAnalyzer -Path $_.FullName -Settings .\PSScriptAnalyzerSettings.psd1
    })
    $blockingAnalysis = @($analysis | Where-Object { $_.Severity -in @('Error', 'ParseError') })
    $warnings = @($analysis | Where-Object { $_.Severity -eq 'Warning' })
    $information = @($analysis | Where-Object { $_.Severity -eq 'Information' })
    Write-Output "PowerShell analysis: $($powershellFiles.Count) files, $($blockingAnalysis.Count) errors, $($warnings.Count) warnings, $($information.Count) informational findings."
    if ($blockingAnalysis.Count -gt 0) {
        $blockingAnalysis | Format-Table RuleName, Severity, ScriptName, Line -AutoSize
        throw 'PSScriptAnalyzer reported blocking issues.'
    }
}
finally {
    Pop-Location
}
