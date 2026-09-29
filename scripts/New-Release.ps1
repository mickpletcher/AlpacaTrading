[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,
    [switch]$Publish,
    [switch]$SkipValidation
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$tag = "v$Version"
$releaseDate = Get-Date -Format 'yyyy-MM-dd'

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,
        [Parameter(ValueFromRemainingArguments)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE."
    }
}

Push-Location $repoRoot
try {
    if ($Publish -and $SkipValidation) {
        throw '-SkipValidation cannot be used with -Publish.'
    }
    if ((git branch --show-current).Trim() -ne 'main') {
        throw 'Releases must be prepared from main.'
    }
    if (git status --porcelain) {
        throw 'The working tree must be clean before release preparation.'
    }

    if ($Publish) {
        Invoke-CheckedCommand -FilePath gh -Arguments @('auth', 'status')
        Invoke-CheckedCommand -FilePath git -Arguments @('fetch', '--quiet', 'origin', 'main', '--tags')
        $localCommit = (git rev-parse HEAD).Trim()
        $remoteCommit = (git rev-parse origin/main).Trim()
        if ($localCommit -ne $remoteCommit) {
            throw "Local main ($localCommit) must exactly match origin/main ($remoteCommit) before publishing."
        }
        gh release view $tag --json tagName 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            throw "GitHub release $tag already exists."
        }
    }

    git rev-parse --verify --quiet "refs/tags/$tag" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        throw "Tag $tag already exists."
    }

    if (-not $SkipValidation) {
        & (Join-Path $PSScriptRoot 'Invoke-ReleaseValidation.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'Release validation failed.' }
    }

    $fragments = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'changelog.d') -Filter '*.md' -File | Sort-Object Name)
    if ($fragments.Count -eq 0) {
        throw 'No changelog fragments were found.'
    }
    $changelogPath = Join-Path $repoRoot 'CHANGELOG.md'
    $changelog = Get-Content -LiteralPath $changelogPath -Raw
    if ($changelog -match "(?m)^## $([regex]::Escape($tag))\b") {
        throw "$tag is already present in CHANGELOG.md."
    }

    $fragmentText = foreach ($fragment in $fragments) {
        $content = Get-Content -LiteralPath $fragment.FullName -Raw
        $content = $content -replace '(?m)^<!-- markdownlint-(?:disable|enable).*?-->\r?\n?', ''
        $content.Trim()
    }
    $section = "## $tag - $releaseDate`r`n`r`n$($fragmentText -join "`r`n`r`n")`r`n`r`n"
    $insertionPoint = [regex]::Match($changelog, '(?m)^## ')
    if (-not $insertionPoint.Success) {
        throw 'CHANGELOG.md has no insertion point.'
    }
    $updatedChangelog = $changelog.Insert($insertionPoint.Index, $section)

    if ($PSCmdlet.ShouldProcess($tag, 'Consolidate changelog fragments')) {
        Set-Content -LiteralPath $changelogPath -Value $updatedChangelog -Encoding utf8 -NoNewline
        foreach ($fragment in $fragments) {
            Remove-Item -LiteralPath $fragment.FullName
        }
    }

    if (-not $Publish) {
        Write-Output "Prepared $tag locally. Review the changelog. To publish through this script, restore the preparation changes, commit the original fragments, and rerun with -Publish."
        return
    }

    $releaseNotes = Join-Path ([IO.Path]::GetTempPath()) "AlpacaTrading-$tag-release-notes.md"
    try {
        Set-Content -LiteralPath $releaseNotes -Value $section.Trim() -Encoding utf8
        if ($PSCmdlet.ShouldProcess($tag, 'Commit, tag, push, and create GitHub release')) {
            Invoke-CheckedCommand -FilePath git -Arguments @('add', '--', 'CHANGELOG.md', 'changelog.d')
            Invoke-CheckedCommand -FilePath git -Arguments @('commit', '-m', "release: $tag")
            Invoke-CheckedCommand -FilePath git -Arguments @('tag', '-a', $tag, '-m', "AlpacaTrading $tag")
            Invoke-CheckedCommand -FilePath git -Arguments @('push', 'origin', 'main')
            Invoke-CheckedCommand -FilePath git -Arguments @('push', 'origin', $tag)
            Invoke-CheckedCommand -FilePath gh -Arguments @('release', 'create', $tag, '--title', "AlpacaTrading $tag", '--notes-file', $releaseNotes, '--verify-tag')
        }
    }
    finally {
        if (Test-Path -LiteralPath $releaseNotes) {
            Remove-Item -LiteralPath $releaseNotes -Force
        }
    }
}
finally {
    Pop-Location
}
