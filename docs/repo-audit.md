<!-- markdownlint-disable MD013 MD024 MD060 -->

# Repository Assessment

**Last full assessment:** 2026-09-29

**Assessed base commit:** `0e12e8eb121d13959e65aaab870cbca31e084154`

**Assessed change:** Upgrade 006 GitHub repository hardening under `specs/006-github-repository-hardening/`

**Basis:** Local repository inspection, current Python and PowerShell validation, documentation checks, and live GitHub readback for CI, branches, merge settings, branch protection, releases, and security alerts.
**Assessed by:** Agent

## Scoped Dependency Assessment: 2026-11-05

**Base:** `d4029f2` (`main`). **Scope:** [specification 008](../specs/008-dependency-consolidation/spec.md), not a new full trading or security assessment.

The sixteen remaining remote branches are dependency updates. The [source inventory](../specs/008-dependency-consolidation/source-branches.json) records their heads and PRs. Combining them requires aligning pandas and dotenv across manifests, refreshing FastAPI and Pydantic in the common lock, and resolving two incompatible transitive pins. Pydantic 2.14.2 requires pydantic-core 2.50.2, superseding the isolated 2.49.0 update. yfinance 1.2.1 is the smallest compatible companion update for curl-cffi 0.16.3. NumPy 2.2.6 remains unchanged for pandas-ta/numba compatibility. FastAPI adds its required opentelemetry-api dependency without adding an exporter or enabling telemetry configuration.

The Python 3.13 lock was regenerated with the targeted upgrades, preserving the original verified colorama and tzdata blocks needed on Windows. The upstream Action tags match their new immutable SHA references. Repository policy tests retain coverage, hash-install, and pinned-module requirements. New offline tests detect stale manifest-only updates and exercise actual RSI/MACD calculations, backtesting.py/Bokeh reports, and Pillow serialization.

Local validation on Python 3.13.5: compile checks and pip check passed; full pytest passed 112 tests with 3 missing-credential skips and 58.26 percent coverage (exit 0). Forty-eight dependency/resource warnings include upstream pandas 4 migration warnings; future pandas 4 support is not established. The existing journal DOM suite and JavaScript syntax checks passed. These results do not establish external market-data behavior or broker acceptance. No account requests or orders were made.

Final exact-head hosted CI, Windows hash-install, browser, PowerShell, documentation, CodeQL, merge, and remote-branch deletion evidence belongs in the integration PR. Local PowerShell and real Chromium were not executed. Existing BUG-007 through BUG-009 remain open.

## Scoped Community and Accessibility Assessment: 2026-11-04

**Base:** `2a415e13bbc3fd48c48279edbe74e02c642d5ecf` (`main`). **Scope:** [specification 007](../specs/007-community-accessibility/spec.md), not a new full security or trading assessment.

GitHub's community profile reported 57 percent before this change: README and MIT license were present, while the code of conduct, contributing guide, issue template, and PR template were missing. Private vulnerability reporting was verified enabled. New community policies and forms use the verified repository owner and private-report route, retain blank issues, and require no medical details for accessibility reports.

The local journal now has labeled controls, keyboard tabs, visible focus, higher contrast, persistent text feedback, reduced motion, and pending-request guards. Generated journal, research, and health reports have semantic tables and keyboard-scrollable regions; the research equity chart has a full text-table alternative. Trading logic, calculations, data ownership, and account boundaries are unchanged.

Current local evidence on Python 3.13.5 with the exact hash-locked dependencies:

- Compile check: exit 0 for all existing Python surfaces and `Tests`.
- `python -m pytest Tests -q --cov --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=50`: exit 0, 108 passed, 3 skipped because paper credentials are absent, 16 dependency/resource warnings, 55.34 percent coverage.
- `python -m pip check`: exit 0, no broken requirements.
- `npm --prefix Tests/browser run test:dom`: exit 0. Keyboard tab state, save failure/data retention, duplicate suppression, cancellation, focus restoration, fetch errors, literal text, prompt generation, and clipboard fallback passed with synthetic data.
- Generated-report fixtures, JavaScript syntax, issue YAML/policy tests, and `git diff --check`: passed.

Local Chromium launch was blocked by the execution environment's socket restriction, and PowerShell is not installed locally. Hosted [CI run 41917635415](https://github.com/mickpletcher/AlpacaTrading/actions/runs/41917635415) verified the implementation at `55066f78d14bae2f48147ef1379153c6a268cbd6` on Windows with Python 3.13.17, Node 22, and Chromium 156. Journal keyboard, focus, failure/retry/cancellation, populated-history reflow, and axe checks passed. All three generated reports passed desktop and 320-pixel reflow, keyboard scrolling, axe checks, and 200 percent text enlargement. PowerShell passed 54 tests with zero failures/skips; analysis reported zero errors, 171 existing warnings, and 3 informational findings. Documentation checks and CodeQL also passed.

Sixteen synthetic screenshots were reviewed. That review prompted a final refinement: preserve readable report columns within keyboard-scrollable containers instead of compressing words into narrow columns. The added regression checks are included in the 108-test local result above. Exact-head hosted results for that refinement and any later changes are tracked in [pull request 42](https://github.com/mickpletcher/AlpacaTrading/pull/42) and must pass before merge. Screen-reader and other assistive-technology checks, actual browser zoom, non-Chromium browsers, and a full WCAG conformance assessment remain not assessed.

BUG-007, BUG-008, and BUG-009 remain open. Text escaping improves part of the journal rendering path but does not complete BUG-009's server limits, Content Security Policy, or security validation.

Pull request 42 was authorized and merged at `5ef326aad5b5901192b6908caed8f1a64264b796`. GitHub's API reports 100 percent community health, and its Community Standards page marks all eight checklist entries Added, including Security policy and Issue templates; it also recognizes `ACCESSIBILITY.md`. Post-merge [CI run 41921847677](https://github.com/mickpletcher/AlpacaTrading/actions/runs/41921847677) passed Python, browser accessibility, PowerShell, and documentation checks. Direct issue-chooser review nevertheless found only two visible forms. GitHub rejected the other three because five field descriptions were empty. The scoped correction replaces those descriptions, adds a regression assertion, and requires every form to be opened in the live chooser after merge. That final rendering check remains pending until the correction reaches the default branch.

The delayed review of pull request 42 also identified offscreen mobile save errors, obsolete failed-read feedback, and focus theft during a delayed post-delete refresh. All three were reproduced with failing synthetic regressions. [Pull request 43](https://github.com/mickpletcher/AlpacaTrading/pull/43) adds narrow fixes and tests: reveal active-form errors without changing focus, discard stale failures before and during delayed announcement, and recheck focus after refresh. Exact-head hosted evidence and final integration acceptance are tracked in that pull request.

The sections below retain the last full assessment's evidence. Historical counts and GitHub state are explicitly dated and must not be treated as new executions for specification 007.

## Plain-Language Summary

The repository is a collection of paper-trading and strategy-learning tools. It is not one application and it cannot place live-money orders.

The consolidated `main` branch builds and its automated tests pass. Three verified defects remain open. The highest-priority defect is in the RSI plus MACD bot's handling of stop orders. The BTC webhook limit and local journal also need safety fixes. CodeQL reports zero open alerts.

Beginners should start with `Backtesting/reproducible_backtest.py` and the local journal. Automated paper-order tools should remain supervised until the open defects in `ISSUES.md` are fixed.

## Agent Handoff

- Preserve the shared Python paper-only boundary in `Alpaca/trading_safety.py`.
- Treat live execution as unavailable. It requires a new Class 4 proposal and ADR.
- Fix BUG-007 before approving unattended RSI plus MACD bot operation.
- Fix BUG-008 before treating `WEBHOOK_MAX_NOTIONAL` as an enforced broker-value ceiling.
- Fix BUG-009 before accepting untrusted journal or CSV text.
- Report suspected vulnerabilities through the private process in `SECURITY.md`.
- Keep runtime database, CSV, log, report, replay, and risk-state files local and ignored.
- Use `Operations/health.py` as a local warning surface, not as proof that the paper account is safe.
- Regenerate `requirements.lock.txt` after direct dependency changes and use the release scripts for tagged snapshots.
- SQLite is authoritative for the browser journal. CSV import remains explicit.
- Use `PROJECT-STANDARD.md` to resolve documentation authorities before creating documentation.

## Living Documentation Compliance

Historical table generated by `scripts/docs-check.ps1 -Markdown` on 2026-09-29. Current authority mapping includes the community policies and is checked by hosted CI.

| Responsibility | Authority | Last updated | Status |
|---|---|---|---|
| Project overview | README.md | 2026-09-29 | Current |
| Current assessment | docs/repo-audit.md | uncommitted | Current |
| Architecture | ARCHITECTURE.md | uncommitted | Current |
| Change history | CHANGELOG.md | 2026-09-28 | Current |
| Defect tracking | ISSUES.md | 2026-09-29 | Current |
| Technical debt | TECH-DEBT.md | 2026-09-29 | Current |
| Deferred improvements | FUTURE-UPGRADES.md | 2026-09-28 | Current |
| Validation | Tests/README.md | 2026-09-29 | Current |
| Operations | OPERATIONS.md | 2026-09-29 | Current |
| Requirement traceability | Not required at this tier |  | N/A |
| Agreed scope | Not required at this tier |  | N/A |
| Agreed design | Not required at this tier |  | N/A |
| Scope amendments | Not required at this tier |  | N/A |
| Decision history | docs/decisions/README.md | 2026-09-29 | Current |
| Resolved history | upgrades/README.md | 2026-09-29 | Current |
| Development rules | PROJECT-STANDARD.md | 2026-09-28 | Current |
| Agent rules | AGENTS.md | 2026-09-28 | Current |

## Full-Assessment Validation Evidence: 2026-09-29

- Python syntax: passed for `Alpaca`, `Backtesting`, `Journal`, `rsi_macd_bot`, and `btc-signal-executor`.
- Python tests: 87 passed, 0 failed, and 3 skipped because Alpaca paper credentials were absent. Sixteen dependency deprecation and resource warnings were reported.
- Python coverage: 53.91 percent, above the enforced 50 percent repository threshold.
- Python dependencies: the hash-verified lock installed successfully and `pip check` reported no broken requirements.
- PowerShell tests: 54 passed, 0 failed, and 0 skipped with Pester 5.7.1.
- PowerShell coverage: 48.65 percent, above the enforced 40 percent repository threshold.
- PowerShell analyzer: 0 errors, 171 warnings, and 3 informational findings with PSScriptAnalyzer 1.24.0.
- Documentation authority checks: passed in table and Markdown modes.
- Reproducible backtest: passed checksum validation, selected EMA 5/20 on training data, reported 11.63 percent out-of-sample return versus 9.06 percent for buy and hold, and completed five walk-forward folds.
- Local health: executed successfully and returned the expected failure status because scheduler evidence was stale and optional runtime evidence and credentials were absent.
- Sanitized screenshots: captured from the actual fixed backtest report, an isolated journal with synthetic rows, and the paper-only terminal help.
- Hosted CI: Python, PowerShell, and documentation jobs passed on `main` commit `0e12e8e` in run 36525657007.
- Dependabot: 0 open alerts.
- Secret scanning: 0 open alerts.
- CodeQL: Python and Actions analysis passed on `main` commit `0e12e8e` in run 36525656614. Both journal response alerts are fixed and zero alerts remain open.

## Standing Waivers

### Alpaca paper integration

Credential-dependent integration tests were skipped.

- Reason: Paper credentials are intentionally absent from the validation environment.
- Risk: Local tests prove request construction and safety behavior with fake clients, not broker acceptance.
- Follow-up: Run bounded, no-order paper connectivity checks before supervised paper execution. Do not submit an order merely to prove connectivity.

### Pre-existing repository-wide Markdown style findings

Repository-wide Markdown lint was not rerun for Upgrade 006. The 2026-09-28 assessment reported 45 findings in legacy GitHub prompt files, `Learning Roadmap/ROADMAP.md`, and the completed `specs/001-core-trading-foundation/plan.md`. Upgrade 006 changed 14 implementation files and 9 closure files. Both pull requests passed the repository's documentation-quality authority check, which is not a repository-wide Markdown style lint.

- Reason: Those style-only findings are outside the novice usage and current-authority scope of this change.
- Risk: A future repository-wide Markdown lint gate would fail until they are corrected or explicitly configured.
- Follow-up: Correct the active roadmap and prompt files in a focused cleanup. Preserve completed specification content while applying only an approved lint policy.

## Current Capabilities

- Historical strategy evaluation with Yahoo Finance and Alpaca market data.
- Fixed-data EMA evaluation with transaction costs, a benchmark, fixed out-of-sample testing, and walk-forward folds.
- Python and PowerShell paper-account helpers with fail-closed endpoint controls.
- Reusable PowerShell modules for configuration, authentication, market data, orders, positions, streams, and risk.
- Local browser journal using SQLite, explicit CSV import, CSV export, and summary statistics.
- Windows and shell scheduler launchers.
- Local JSON and HTML health reporting for stale data, rejected orders, missing stops, circuit-breaker state, and scheduler failures.
- Hash-verified Python dependency installation, coverage gates, and a guarded tagged-release workflow.
- Paper-only RSI plus MACD bot. Supervision is required while BUG-007 is open.
- Paper-only FastAPI BTC webhook with bounded input, persistent SQLite replay protection, rate limiting, failure gating, and a daily-loss gate. BUG-008 limits the strength of its notional control.

## Verified Open Defects

| ID | Severity | Summary |
| --- | --- | --- |
| BUG-007 | High | RSI bot can leave an unprotected position or an unmatched stop order |
| BUG-008 | Medium | BTC notional limit trusts the webhook price instead of an authoritative quote |
| BUG-009 | Medium | Journal input limits and browser defense remain incomplete |

Details and safe-use limits are maintained in `ISSUES.md`.

## Technical Debt Summary

- High: 0
- Medium: 1
- Low: 0

Details are maintained in `TECH-DEBT.md`.

## Current Priorities

1. Fix BUG-007 and add complete paper-order lifecycle tests.
2. Fix BUG-008 and BUG-009.
3. Reduce PowerShell correctness warnings under TD-004.
4. Extend the fixed evaluation model and dataset only when a strategy needs comparable research evidence.

## GitHub Repository State: 2026-09-29 Snapshot

- `main` was the only branch and there were no open pull requests after implementation PR 17 merged. This assessment closure uses a temporary branch with pull request 18 targeting protected `main`.
- Squash is the only enabled merge method. Automatic source-branch deletion and update-branch support are enabled.
- The active `main protection` ruleset requires pull requests, strict `python-quality`, `powershell-quality`, and `documentation-quality` checks, CodeQL at medium or higher, conversation resolution, and linear history. Zero approvals are required while there is one maintainer. No administrator bypass is configured.
- The active `release tag protection` ruleset has no bypass actors and blocks updates, deletions, and non-fast-forward changes for `v*` tags.
- Actions are restricted to GitHub-owned `actions/*` dependencies pinned to full commit SHAs. Pester 5.7.1 and PSScriptAnalyzer 1.24.0 are exact pins.
- Private vulnerability reporting is enabled. Wiki and Projects are disabled.
- Initial tagged release: `v0.1.0`.

## Repository Limitations

- This is a collection of related tools, not one packaged application.
- Backtests are educational and do not prove profitability.
- There is no centralized deployment or hosted monitoring. Health and alerting are local only.
- Webhook rate and failure counters are process-local. Replay identifiers are persistent in SQLite.
- Live trading is intentionally unavailable.

<!-- markdownlint-enable MD013 MD024 MD060 -->
