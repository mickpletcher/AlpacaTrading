# Implement From Spec In Trading Repo

Implement the target change using the existing spec package as the source of truth.

## Instructions

1. Read `requirements.md`, `spec.md`, `plan.md`, and `tasks.md` first.
2. Inspect the affected code before editing.
3. Preserve existing behavior outside the approved scope.
4. Reuse existing PowerShell modules and Python helpers instead of duplicating logic.
5. Update README or module docs when commands, entry points, or workflows change.
6. Update tests in `Tests/` when behavior changes.
7. Run the smallest reliable verification set before finishing.

## Safety Rules

- Do not switch paper-trading defaults to live trading.
- Do not remove existing feature folders as part of an unrelated implementation.
- Do not invent a new architecture if the current one can be extended cleanly.

## Output Expectation

Return:

- the files changed
- verification performed
- remaining risks or follow-up debt
