# Audit Change In Trading Repo

Review the implemented change against the relevant spec package and the current repository behavior.

## Audit Focus

- requirements coverage
- behavioral regressions
- architecture drift
- missing tests
- documentation drift
- PowerShell and Python stack consistency

## Instructions

1. Read the target spec package first.
2. Review changed files against the rest of the repo.
3. Identify concrete findings, prioritized by severity.
4. Flag mismatches between implementation and spec.
5. Call out missing verification, especially around:
   - order routing
   - risk controls
   - journal persistence
   - scheduler automation
   - CI behavior

## Output Format

- findings first, ordered by severity
- open questions or assumptions
- brief summary of overall alignment
