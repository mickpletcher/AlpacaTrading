<!-- markdownlint-disable MD013 MD024 MD060 -->

# 005 Research, Operations, and Release Requirements

## Goal

Complete FU-002 through FU-005 and TD-009 with reproducible local workflows that preserve the paper-only trading boundary.

## Requirements

1. Provide a deterministic backtesting command that runs without credentials or network access.
2. Pin each evaluation to a fixed dataset checksum and explicit strategy configuration.
3. Apply configurable commission and slippage costs to strategy results.
4. Compare each result with a buy-and-hold benchmark.
5. Separate training and out-of-sample bars and produce rolling walk-forward folds without look-ahead selection.
6. Write machine-readable and beginner-readable evaluation reports outside user journal data.
7. Provide one local health command for stale data, rejected orders, missing protective stops, circuit-breaker state, and scheduler failures.
8. Health checks must distinguish `PASS`, `WARN`, `FAIL`, and `UNKNOWN` and must not require order submission.
9. Write local JSON, HTML, and alert-log health artifacts without committing runtime data.
10. Make scheduler launchers write a machine-readable final status.
11. Measure Python and PowerShell coverage in CI, retain coverage artifacts, and fail below reviewed minimums.
12. Install Python dependencies from a hash-checked lock in CI and document one lock refresh command.
13. Replace the three placeholder images with sanitized captures produced from actual repository output or interfaces.
14. Provide an explicit release command that validates the repository, consolidates changelog fragments, creates a version commit and tag, pushes them, and creates a GitHub release.
15. Release publication must require an explicit switch, a clean `main` branch, an authenticated GitHub CLI, and confirmation through PowerShell `ShouldProcess`.
16. Add automated tests for deterministic evaluation, health classification, lock and release policy, and scheduler status output.
17. Update all routed living authorities and move completed proposals and debt to resolved history.

## Safety Boundaries

- No command added by this package may enable live trading.
- Default validation and screenshots must not require Alpaca credentials.
- Health inspection may read a paper account but must never mutate it.
- Generated reports, health state, temporary screenshot data, and credentials remain ignored.
- Release automation must not publish unless `-Publish` is supplied explicitly.

## Acceptance Criteria

- Two repeated evaluation runs over the tracked fixture produce identical metric data.
- The evaluation report shows checksum, costs, benchmark, fixed out-of-sample result, and walk-forward folds.
- Health tests cover all five requested alert categories and unknown evidence.
- Python and PowerShell coverage gates pass at their committed thresholds.
- A clean environment installs with `--require-hashes` from the lock and passes `pip check`.
- Documentation references PNG captures and no placeholder screenshot remains.
- Release preparation is testable without creating a commit, tag, push, or GitHub release.

<!-- markdownlint-enable MD013 MD024 MD060 -->
