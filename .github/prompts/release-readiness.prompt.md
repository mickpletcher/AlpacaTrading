# Release Readiness For Trading Repo

Assess whether a change in this repository is ready to merge or release.

## Checklist Areas

- spec package is complete and current
- README and affected module docs are updated
- CI covers the changed surface appropriately
- Python verification is green where relevant
- PowerShell verification is appropriate for the touched modules
- secrets are not committed
- paper-trading safeguards remain intact
- generated artifacts were not accidentally rewritten without intent

## Instructions

1. Review the change set and associated spec package.
2. Identify blockers vs non-blocking follow-ups.
3. Be explicit about any known test debt that still exists in the repo.

## Output Format

- readiness verdict
- blockers
- non-blocking follow-ups
- final recommendation
