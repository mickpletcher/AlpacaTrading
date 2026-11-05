from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_installs_hash_checked_lock_and_enforces_coverage() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "--require-hashes -r requirements.lock.txt" in workflow
    assert "--cov-fail-under=50" in workflow
    assert "CoveragePercentTarget = 40" in workflow
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    assert "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0" in workflow
    assert "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9" in workflow
    assert "PSScriptAnalyzer -RequiredVersion 1.24.0" in workflow
    assert "Pester -RequiredVersion 5.7.1" in workflow

    analyzer_script = (ROOT / "scripts" / "Invoke-PowerShellStaticAnalysis.ps1").read_text(
        encoding="utf-8"
    )
    assert "Import-Module PSScriptAnalyzer -RequiredVersion $requiredVersion" in analyzer_script
    assert "-MinimumVersion" not in analyzer_script


def test_release_publication_is_explicit_and_validated() -> None:
    script = (ROOT / "scripts" / "New-Release.ps1").read_text(encoding="utf-8")

    assert "[switch]$Publish" in script
    assert "Invoke-ReleaseValidation.ps1" in script
    assert "@('tag', '-a', $tag" in script
    assert "@('push', 'origin', 'main')" in script
    assert "@('push', 'origin', $tag)" in script
    assert "@('release', 'create', $tag" in script
    assert "SupportsShouldProcess" in script


def test_security_policy_defines_private_reporting_and_boundaries() -> None:
    policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "GitHub private vulnerability reporting" in policy
    assert "Live-money order submission must remain unavailable." in policy
    assert "API responses must not expose credentials" in policy
    assert "documented limitation is not automatically an accepted security risk" in policy
