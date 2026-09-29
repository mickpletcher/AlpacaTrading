<!-- markdownlint-disable MD013 MD024 MD060 -->

# 006 GitHub Repository Hardening Specification

## Classification

Class 4. This package changes repository security enforcement, workflow trust, disclosure handling, protected references, and client-visible error behavior.

## Branch and Merge Enforcement

One active repository ruleset targets the default branch. It has no bypass actor, requires pull requests with zero approvals, requires review-thread resolution, permits squash merges only, requires linear history, blocks deletion and non-fast-forward updates, and requires the Python, PowerShell, and documentation GitHub Actions checks from the GitHub Actions app.

The same ruleset requires CodeQL results and blocks medium-or-higher security alerts. Required checks use strict current-branch validation. The legacy branch protection rule is removed only after the active ruleset is read back successfully.

Repository merge settings disable merge commits and rebase merges, keep squash merges, enable branch updates, and delete merged source branches automatically.

## Workflow Supply Chain

Every `uses:` reference in the repository workflow points to a verified commit from the official action repository and retains a version comment for maintenance. CI installs Pester 5.7.1 and PSScriptAnalyzer 1.24.0 exactly.

Repository Actions policy allows GitHub-owned actions, rejects unselected third-party actions, requires full commit SHA references, keeps the default workflow token read-only, and does not let workflows approve pull requests.

## Journal Error Boundary

The journal accepts untrusted JSON only from loopback clients. Validation failures retain HTTP 400 and the existing JSON error shape, but responses contain stable route-specific messages rather than caught exception text. Detailed Python conversion errors are neither returned nor logged by this change.

Focused tests send distinctive attacker-controlled numeric values through required, optional, missing, and non-object payload cases. The values must not appear in responses. Valid POST and PUT behavior must remain available.

## Security Reporting

The root `SECURITY.md` defines supported versions, private reporting, system boundaries, trust boundaries, security invariants, reportability, narrow exclusions, and known limitations. GitHub private vulnerability reporting is enabled so suspected vulnerabilities do not need to be disclosed in public issues.

## Tag Protection and Repository Features

An active tag ruleset targets `refs/tags/v*`. It blocks updates, deletion, and non-fast-forward changes without blocking new tag creation.

Wiki and Projects are disabled because repository Markdown authorities and tracked specifications are the maintained sources of truth. Issues remain enabled for public defect reports after private vulnerability reporting is available.

## Evidence Boundary

Local tests prove stable journal error behavior and workflow configuration. GitHub API readback proves repository settings. Hosted CI and CodeQL prove the pushed revision is accepted by the configured services. No validation submits an Alpaca order.

<!-- markdownlint-enable MD013 MD024 MD060 -->
