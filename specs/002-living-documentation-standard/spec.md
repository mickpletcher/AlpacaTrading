<!-- markdownlint-disable MD013 MD024 MD060 -->

# 002 Living Documentation Standard Spec

## Classification

Class 2 internal implementation. The change adds repository governance, living documentation authorities, and a local compliance script without changing runtime interfaces or trading behavior.

## Design

- Declare Tier 2 and Adoption Mode in `PROJECT-STANDARD.md`.
- Keep `README.md` as project overview.
- Adapt `docs/repo-audit.md` as current assessment.
- Adapt `Tests/README.md` as validation authority.
- Keep `upgrades/README.md` as resolved history.
- Create authorities for responsibilities not already served.
- Create `AGENTS.md` and reduce `.github/copilot-instructions.md` to an authority pointer.
- Add `.docs-authority.json` and `scripts/docs-check.ps1`.

## Validation

- Parse `.docs-authority.json` and resolve every authority.
- Run `scripts/docs-check.ps1` in table and Markdown modes.
- Run Markdown lint when tooling is available.
- Run safe repository checks because no runtime code changes are intended.
- Waive Pester rerun if it remains unsafe due BUG-002 and BUG-003.

## Safety

- No credentials or private account information enter documentation.
- No runtime journal or risk state is modified.
- Existing history is preserved.

<!-- markdownlint-enable MD013 MD024 MD060 -->
