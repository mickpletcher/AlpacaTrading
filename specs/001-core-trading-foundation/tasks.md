<!-- markdownlint-disable MD013 -->

# 001 Core Trading Foundation Tasks

## Completed Retrofit Tasks

- [x] T001 Audit the repository structure, runtime surfaces, tests, and documentation baseline.
  - Files: `README.md`, `requirements.txt`, `Tests/`, `src/`, feature folders
  - Verification: manual repo inspection plus compile and test discovery

- [x] T002 Create a root-level repo audit document.
  - Files: `docs/repo-audit.md`
  - Verification: audit includes structure, languages, entry points, tests, CI gap, and architectural issues

- [x] T003 Update the root README to describe the actual current architecture and workflows.
  - Files: `README.md`
  - Verification: README covers setup, usage, development flow, GitHub Spec workflow, and repo structure

- [x] T004 Add repo-specific Copilot instructions for mixed Python and PowerShell development.
  - Files: `.github/copilot-instructions.md`
  - Verification: instructions cover architecture, safety, naming, testing, and spec alignment

- [x] T005 Add reusable GitHub prompt files for requirements through release-readiness.
  - Files: `.github/prompts/*.prompt.md`
  - Verification: prompts reference real repo paths and current module boundaries

- [x] T006 Create the baseline numbered spec package for the current repository state.
  - Files: `specs/001-core-trading-foundation/requirements.md`, `spec.md`, `plan.md`, `tasks.md`
  - Verification: spec package reflects current repo, not a replacement product

- [x] T007 Add CI for stable current quality checks.
  - Files: `.github/workflows/ci.yml`
  - Verification: workflow installs Python deps, compiles Python, runs `pytest`, validates PowerShell manifests, imports modules, and runs script analysis

- [x] T008 Normalize Python test discovery for the existing `Tests/` folder.
  - Files: `pytest.ini`
  - Verification: `pytest` points to `Tests/`

- [x] T009 Tighten ignore rules for local environment and generated noise.
  - Files: `.gitignore`
  - Verification: local caches, venvs, logs, and build artifacts are ignored

## Follow-Up Backlog

- [ ] T010 Modernize `Tests/*.Tests.ps1` to a single supported Pester version.
  - Files: `Tests/*.Tests.ps1`
  - Verification: `Invoke-Pester` passes in CI with a pinned Pester version

- [ ] T011 Decide whether tracked generated artifacts in `Journal/` should remain versioned or move to generated-only status.
  - Files: `Journal/report.html`, `Journal/trades.db`, related docs
  - Verification: documented repo policy for generated artifacts

- [ ] T012 Add targeted module ownership notes for major feature areas.
  - Files: likely `docs/` and future spec packages
  - Verification: contributors can identify change boundaries before editing

## Baseline Verification Notes

- Python compile check passed.
- Python `pytest` in `.venv` passed with `36 passed, 3 skipped`.
- PowerShell Pester remains deferred pending modernization and compatibility cleanup.

<!-- markdownlint-enable MD013 -->
