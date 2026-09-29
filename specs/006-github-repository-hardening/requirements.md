<!-- markdownlint-disable MD013 MD024 MD060 -->

# 006 GitHub Repository Hardening Requirements

## Goal

Make the repository's GitHub controls enforce the documented review, validation, security-reporting, workflow-supply-chain, and release-tag boundaries.

## Requirements

1. Require pull requests for `main` without requiring an approval while the repository has one maintainer.
2. Apply the `main` protection rules to repository administrators with no bypass actor.
3. Require current Python, PowerShell, documentation, and CodeQL results before `main` can change.
4. Block branch deletion, force pushes, and non-linear history on `main`.
5. Allow squash merging only, enable pull request branch updates, and delete merged branches automatically.
6. Pin every external GitHub Action to a reviewed full commit SHA.
7. Restrict Actions to GitHub-owned actions and require full commit SHA references.
8. Pin Pester and PSScriptAnalyzer to reviewed versions in CI.
9. Replace raw exception-derived journal API responses with stable client-facing validation messages.
10. Add regression tests proving attacker supplied numeric text is not reflected and valid journal writes still succeed.
11. Add a root security policy and enable private vulnerability reporting.
12. Protect version tags matching `v*` from updates, deletion, and force pushes.
13. Disable unused Wiki and Projects features.
14. Preserve the paper-only execution boundary and credential-free default validation.

## Acceptance Criteria

- A pull request is required for `main`, including for the repository administrator.
- The branch ruleset requires `python-quality`, `powershell-quality`, `documentation-quality`, and CodeQL with strict current-branch validation.
- CodeQL blocks medium-or-higher security alerts.
- The tag ruleset protects `v*` tags without blocking creation of a new version tag.
- GitHub reports squash as the only allowed merge method, automatic branch deletion and branch updates enabled, and Wiki and Projects disabled.
- GitHub Actions reports selected actions, GitHub-owned actions allowed, and full SHA pinning required.
- The two journal `py/stack-trace-exposure` findings close after CodeQL analyzes the merged change.
- Focused and repository validation pass without live credentials or paper-account mutation.

<!-- markdownlint-enable MD013 MD024 MD060 -->
