<!-- markdownlint-disable MD013 MD024 MD060 -->

# AI Agent Repository Rules

Standard version: 2.2
Project tier: 2

## Authority Resolution

Resolve documentation responsibilities through the Authority Mapping in `PROJECT-STANDARD.md`. Never create a document that duplicates an existing authority.

## Startup

1. Read this file.
2. Classify the change from Class 0 through Class 4.
3. For Class 1 and above, resolve and read only the routed authorities.
4. For Class 2 and above, read the Agent Handoff in the current assessment.
5. Inspect the relevant implementation before editing.
6. Route non-trivial repository work through a numbered package under `specs/`.

## Repository Boundaries

- Treat this as an existing mixed Python and PowerShell toolkit, not a greenfield application.
- Default all execution and examples to Alpaca paper trading.
- Reusable PowerShell API and risk logic belongs in `src/`.
- Script entry points stay in their existing feature folders.
- Journal concerns stay in `Journal/`.
- Strategy logic stays in `Backtesting/strategies/`.
- Keep scheduler scripts thin.
- Do not collapse the separate backtesting, paper trading, journal, webhook, and standalone bot surfaces without an approved architectural change.
- Do not rename top-level product folders without an explicit migration plan.

## Source of Truth

For current behavior, executable repository state, configuration, schemas, and tests govern. Correct stale living documentation.

The numbered spec package governing a change defines its intended scope. If code and an approved spec conflict, record the conflict. Do not silently rewrite one to match the other.

## Evidence and Waivers

- Never claim a test, lint, build, or scan passed unless it ran in the current work session.
- Report the command, exit code, counts, skipped tests, and skip reasons.
- Never weaken or remove a valid test to make a change pass.
- State `Not assessed` when evidence is unavailable.
- If a required check cannot run safely, record a waiver with the reason, risk, and follow-up.
- Material architecture claims require inline repository evidence.

## Testing

- Use `Tests/` as the canonical automated test directory.
- Python changes must run the applicable pytest suite and compile checks.
- PowerShell changes must preserve manifest validity and module importability.
- Update Pester tests when changing PowerShell parsing, authentication, configuration, risk, or order logic.
- Do not depend on live credentials in default automated checks.
- Follow the current limitations in `Tests/README.md`. Do not run unsafe validation merely to obtain a passing result.

## Documentation

- Living documents describe current truth and are rewritten when stale.
- Derived decision and resolved-history records are append-only.
- The assessment is current truth, not a diary.
- Add a `changelog.d/` fragment for meaningful changes.
- Link to another authority instead of repeating its content.
- Never invent capabilities, requirements, architecture, validation, or status.

## Security

- Never commit secrets, credentials, tokens, private certificates, or private account identifiers.
- Use placeholders in configuration examples.
- Do not weaken a trading safety control to simplify implementation.
- Preserve user-owned and runtime data unless the scoped change explicitly includes migration or cleanup.

## Naming

- Python files use `snake_case.py`.
- PowerShell functions use approved `Verb-Noun` names.
- New spec folders use `specs/NNN-short-kebab-name/`.

## Completion

A task is complete only when implementation, executed validation, waivers, documentation, and repository state agree.

<!-- markdownlint-enable MD013 MD024 MD060 -->
