BeforeAll {
    $script:ReleaseScript = Join-Path $PSScriptRoot '..\scripts\New-Release.ps1'
}

Describe 'Release preparation' {
    It 'consolidates fragments without committing or tagging' {
        $repo = Join-Path $TestDrive 'release-repo'
        $scripts = Join-Path $repo 'scripts'
        $fragments = Join-Path $repo 'changelog.d'
        New-Item -ItemType Directory -Path $scripts,$fragments -Force | Out-Null
        Copy-Item -LiteralPath $script:ReleaseScript -Destination (Join-Path $scripts 'New-Release.ps1')
        Set-Content -LiteralPath (Join-Path $repo 'CHANGELOG.md') -Value "# Changelog`n`n## Existing`n`n- Existing note.`n" -Encoding utf8
        Set-Content -LiteralPath (Join-Path $fragments 'change.md') -Value "### Added`n`n- Prepared release test.`n" -Encoding utf8

        git -C $repo init -b main | Out-Null
        git -C $repo config user.name 'Release Test'
        git -C $repo config user.email 'release-test@example.invalid'
        git -C $repo add .
        git -C $repo commit -m seed | Out-Null

        Push-Location $repo
        try {
            & (Join-Path $scripts 'New-Release.ps1') -Version '1.2.3' -SkipValidation -Confirm:$false
        }
        finally {
            Pop-Location
        }

        (Get-Content -LiteralPath (Join-Path $repo 'CHANGELOG.md') -Raw) | Should -Match '## v1\.2\.3 -'
        Test-Path -LiteralPath (Join-Path $fragments 'change.md') | Should -BeFalse
        (git -C $repo rev-list --count HEAD).Trim() | Should -Be '1'
        (git -C $repo tag) | Should -BeNullOrEmpty
    }
}
