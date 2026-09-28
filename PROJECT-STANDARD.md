<!-- markdownlint-disable MD013 MD024 MD060 -->

# Project Standard

**Standard version:** 2.2
**Project tier:** 2
**Lifecycle mode:** Adoption
**Tier rationale:** This repository contains multiple executable surfaces, external Alpaca and market-data integrations, schedulers, stateful local data, and order-routing code. Failure can have operational consequences. No client agreement or delivery sign-off exists, so Tier 2C does not apply.
**Promotion trigger:** Promote to Tier 2C only when a named stakeholder relationship includes agreed scope and delivery sign-off.

## Authority Mapping

| Responsibility | Authority | Notes |
|---|---|---|
| Project overview | `README.md` | Pre-existing authority |
| Current assessment | `docs/repo-audit.md` | Pre-existing audit adapted as current assessment |
| Architecture | `ARCHITECTURE.md` | Created during 2.2 adoption |
| Change history | `CHANGELOG.md` | Created during 2.2 adoption |
| Defect tracking | `ISSUES.md` | Created during 2.2 adoption |
| Technical debt | `TECH-DEBT.md` | Created during 2.2 adoption |
| Deferred improvements | `FUTURE-UPGRADES.md` | Created during 2.2 adoption |
| Validation | `Tests/README.md` | Pre-existing test guide adapted as validation authority |
| Operations | `OPERATIONS.md` | Created during 2.2 adoption |
| Requirement traceability | Not required at this tier | Tier 2C only |
| Agreed scope | Not required at this tier | Tier 2C only |
| Agreed design | Not required at this tier | Tier 2C only |
| Scope amendments | Not required at this tier | Tier 2C only |
| Decision history | `docs/decisions/README.md` | Derived, append-only index |
| Resolved history | `upgrades/README.md` | Pre-existing applied-upgrade history |
| Development rules | `PROJECT-STANDARD.md` | This file |
| Agent rules | `AGENTS.md` | Root authority; other instruction files are pointers |

The machine-readable mapping in `.docs-authority.json` must agree with this table.

## Document Classes

- Living documents describe current truth. Correct them when repository evidence changes.
- Contractual documents preserve an agreement. This tier has none.
- Derived documents preserve decisions and resolved history. Append; do not rewrite history.
- Governance documents define repository method and carry a standard version.

## Source of Truth

For what the system does, executable repository state, configuration, schemas, and tests govern over documentation.

For what the system should do, an explicitly approved spec governs the change it covers. The numbered packages under `specs/` are internal change records, not client contracts.

When intent and implementation conflict, record the conflict. Do not silently edit either side to hide it.

## Change Classes

| Class | Name | Typical changes |
|---|---|---|
| 0 | Trivial | Formatting, typo, ignore entry, generated output refresh |
| 1 | Documentation | Human-facing documentation only |
| 2 | Internal implementation | Refactor, test work, internal tooling, repository governance |
| 3 | Functional | Feature, bug fix, dependency, configuration, interface change |
| 4 | Architectural or security | Trust boundary, data model, deployment, authentication, security control |

Class 0 skips the documentation lifecycle. Class 1 reviews the target authority. Class 2 and above read the current assessment handoff and the authorities routed by change type. Class 4 changes presume a proposed ADR before implementation.

## Routed Reads

| Change type | Read before work | Review after work |
|---|---|---|
| Internal refactor | Architecture, technical debt, validation | Change history, technical debt, assessment |
| Test-only change | Validation | Change history, validation, assessment |
| Bug fix | Assessment, validation, defects | Change history, defects, assessment |
| New feature or interface | Overview, architecture, validation, future upgrades | Overview, change history, architecture, validation, assessment |
| Dependency change | Architecture, technical debt, validation | Change history, architecture, debt, assessment |
| Configuration change | Operations, architecture, validation | Change history, operations, assessment |
| Architecture, security, deployment | Architecture, decisions, validation, operations | Change history, architecture, decisions, validation, operations, assessment |

Resolve each responsibility through the Authority Mapping. Do not create parallel authorities.

## Evidence and Validation

- Every material living-document claim must cite repository evidence or be marked unverified.
- Never claim a command passed unless it was executed in the current work session.
- Report commands, exit codes, pass and fail counts, skipped tests, and skip reasons.
- A required check that cannot run safely is waived on the record with reason, risk, and follow-up.
- Validation procedures live in `Tests/README.md`. Per-change results belong in the completion report, commit, or pull request.

## Change History and Decisions

- Add a fragment under `changelog.d/` for every Class 2 or higher change and meaningful Class 1 change.
- Consolidate fragments into `CHANGELOG.md` during a release or monthly maintenance.
- Write an ADR before a Class 4 change or significant design decision.
- Accepted ADR content is immutable except for status and reciprocal supersession fields.
- Append resolved work to `upgrades/README.md`; do not leave resolved entries in active defect or debt authorities.

## Compliance

Run:

```powershell
pwsh -NoProfile -File .\scripts\docs-check.ps1 -FailOnGap
pwsh -NoProfile -File .\scripts\docs-check.ps1 -Markdown
```

`MISSING` is a compliance gap. `REVIEW` requires a conscious freshness review. The generated Markdown table is copied into the current assessment and is never hand-authored.

## Security Rules

- Never commit secrets, tokens, private certificates, real account identifiers, or private infrastructure details.
- Keep configuration examples placeholder-only.
- Default all examples and automated execution to paper trading.
- Do not weaken a safety control to simplify development or validation.

<!-- markdownlint-enable MD013 MD024 MD060 -->
