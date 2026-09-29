from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_installs_hash_checked_lock_and_enforces_coverage() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "--require-hashes -r requirements.lock.txt" in workflow
    assert "--cov-fail-under=50" in workflow
    assert "CoveragePercentTarget = 40" in workflow
    assert "actions/upload-artifact@v7" in workflow


def test_release_publication_is_explicit_and_validated() -> None:
    script = (ROOT / "scripts" / "New-Release.ps1").read_text(encoding="utf-8")

    assert "[switch]$Publish" in script
    assert "Invoke-ReleaseValidation.ps1" in script
    assert "@('tag', '-a', $tag" in script
    assert "@('push', 'origin', 'main')" in script
    assert "@('push', 'origin', $tag)" in script
    assert "@('release', 'create', $tag" in script
    assert "SupportsShouldProcess" in script
