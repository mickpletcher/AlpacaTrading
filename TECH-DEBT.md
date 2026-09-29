<!-- markdownlint-disable MD013 MD024 MD060 -->

# Technical Debt

Technical debt is known engineering work that is not necessarily a current behavior defect.

## TD-004: PowerShell warnings are not controlled by CI

**Status:** Open

**Severity:** Medium
**Area:** PowerShell quality

CI blocks analyzer errors but allows warnings. The current assessment found 171 warnings and 3 informational findings. Most warnings are `Write-Host` style findings, but the set also includes empty catches and suspicious null comparisons.

**Recommended resolution:** Review correctness-related warnings first, create an approved baseline for intentional console output, and make CI reject new unreviewed warnings.

## TD-008: GitHub merge and quality gates do not preserve the intended workflow

**Status:** Open

**Severity:** Medium
**Area:** GitHub repository settings

GitHub allows merge commits, rebase merges, and squash merges. Automatic source-branch deletion is disabled. Branch protection requires Python and PowerShell checks but not documentation quality or CodeQL. Administrator enforcement is disabled.

**Recommended resolution:** Keep squash merge only, enable branch deletion after merge, require all applicable checks, and decide whether administrator enforcement is appropriate for this repository.

Resolved TD-001, TD-002, TD-003, TD-005, and TD-007 are recorded under Upgrade 004 in `upgrades/README.md`. Resolved TD-006 and TD-009 are recorded under Upgrade 005.

<!-- markdownlint-enable MD013 MD024 MD060 -->
