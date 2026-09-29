<!-- markdownlint-disable MD013 MD024 MD060 -->

# 006 GitHub Repository Hardening Plan

1. Record the Class 4 decision and exact repository-control requirements.
2. Fix and test the journal exception-disclosure boundary.
3. Pin workflow actions and PowerShell validation modules.
4. Add the approved security policy and update routed living documentation.
5. Run focused and full local validation.
6. Push a feature branch and open a pull request.
7. Apply merge, Actions, vulnerability-reporting, feature, branch-ruleset, and tag-ruleset settings in a safe order.
8. Verify the rulesets before removing the legacy branch protection rule.
9. Require hosted CI and CodeQL, squash merge the pull request, and verify main, alerts, and repository settings.

The settings are applied after the pinned workflow exists on the pull request so full-SHA enforcement does not block validation. The legacy branch protection rule remains until the replacement branch ruleset is active and verified.

<!-- markdownlint-enable MD013 MD024 MD060 -->
