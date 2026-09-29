<!-- markdownlint-disable MD013 MD024 MD060 -->

# Technical Debt

Technical debt is known engineering work that is not necessarily a current behavior defect.

## TD-004: PowerShell warnings are not controlled by CI

**Status:** Open

**Severity:** Medium
**Area:** PowerShell quality

CI blocks analyzer errors but allows warnings. The current assessment found 171 warnings and 3 informational findings. Most warnings are `Write-Host` style findings, but the set also includes empty catches and suspicious null comparisons.

**Recommended resolution:** Review correctness-related warnings first, create an approved baseline for intentional console output, and make CI reject new unreviewed warnings.

Resolved TD-001, TD-002, TD-003, TD-005, and TD-007 are recorded under Upgrade 004 in `upgrades/README.md`. Resolved TD-006 and TD-009 are recorded under Upgrade 005.
Resolved TD-008 is recorded under Upgrade 006.

<!-- markdownlint-enable MD013 MD024 MD060 -->
