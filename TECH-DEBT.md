<!-- markdownlint-disable MD013 MD024 MD060 -->

# Technical Debt

## TD-004: PowerShell static-analysis warnings are not treated as debt by CI

**Status:** Open
**Severity:** Medium
**Area:** PowerShell quality
**Introduced/Discovered:** 2026-09-28
**Standing waiver:** No

**Related files:** `.github/workflows/ci.yml`, `PSScriptAnalyzerSettings.psd1`

**Description:** CI blocks only analyzer errors. The assessment found 171 warnings, including empty catch blocks and suspicious null comparisons.

**Impact:** Meaningful warnings can accumulate without review.

**Recommended resolution:** Baseline noisy rules, fix correctness-related warnings, then enforce a reviewed threshold.

**Fix trigger:** Next PowerShell quality pass.

**Estimated effort:** Medium

## TD-006: Strategy evaluation is not reproducible enough for decision making

**Status:** Open
**Severity:** Medium
**Area:** Backtesting
**Introduced/Discovered:** 2026-09-28
**Standing waiver:** No

**Related files:** `Backtesting/`

**Description:** Strategy runners use different data sources and inconsistent transaction-cost assumptions. Out-of-sample and walk-forward validation are absent.

**Impact:** Results are useful for learning but weak evidence for automated trading decisions.

**Recommended resolution:** Implement FU-002.

**Fix trigger:** Before strategy promotion beyond paper experiments.

**Estimated effort:** Large

Resolved TD-001, TD-002, TD-003, TD-005, and TD-007 are recorded under Upgrade 004 in `upgrades/README.md`.

<!-- markdownlint-enable MD013 MD024 MD060 -->
