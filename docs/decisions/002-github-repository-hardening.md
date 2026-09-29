<!-- markdownlint-disable MD013 MD024 -->

# ADR 002: GitHub repository enforcement and security reporting

**Status:** Accepted
**Date:** 2026-09-28

## Context

The repository's default branch has strict Python and PowerShell checks, but the sole administrator can bypass them and push directly. Documentation and CodeQL are not required. All actions are allowed, workflow dependencies use mutable tags, public vulnerability reporting has no private path, and version tags have no protection. Two journal routes return raw exception text to callers.

## Decision

1. Use an active default-branch ruleset with no bypass actor to require pull requests, strict Python, PowerShell, and documentation checks, CodeQL merge protection, linear history, resolved review threads, and squash-only merging.
2. Require zero approvals while the repository has one maintainer. Increase the count when an independent trusted reviewer is available.
3. Use an active `v*` tag ruleset to block tag updates, deletion, and non-fast-forward changes while permitting new version tags.
4. Pin GitHub Actions to reviewed full commit SHAs, restrict Actions to GitHub-owned actions, and pin CI validation modules.
5. Publish a root security policy and enable GitHub private vulnerability reporting.
6. Return stable journal validation errors instead of exception-derived text.
7. Disable Wiki and Projects because tracked repository documents are authoritative.

## Consequences

- Every change to `main`, including an owner change, must use a pull request and pass required checks.
- A single maintainer can still merge an eligible pull request without self-approval.
- Compromised or retargeted action version tags cannot silently change executed workflow code.
- Medium-or-higher CodeQL security findings block a merge.
- Vulnerability reporters have a private GitHub channel.
- Release tags cannot be rewritten or deleted without first changing the ruleset.
- Emergency changes require an explicit, auditable ruleset change instead of an undocumented bypass.

## Alternatives rejected

- Keeping administrator bypass was rejected because it allowed the failed `v0.1.0` release commit to reach `main` without hosted validation enforcement.
- Requiring one approval was rejected while only one maintainer exists because authors cannot provide independent approval for their own pull requests.
- Mutable action tags were rejected because they do not identify immutable workflow code.
- Wiki and Projects were rejected as parallel authorities while repository Markdown and numbered specs govern the project.

<!-- markdownlint-enable MD013 MD024 -->
