<!-- markdownlint-disable MD013 -->

# 008 Dependency Consolidation Plan

1. Inventory remote branch heads and original PRs; inspect every unique patch.
2. Consolidate compatible direct and transitive updates on current main, resolving duplicate dotenv updates and coupled constraints.
3. Regenerate the Python 3.13 lock and perform a clean hash-verified installation.
4. Add regression checks for manifest/lock agreement and synthetic indicator and rendering compatibility.
5. Run local checks, publish a draft integration PR, and verify all required hosted checks on the final head.
6. Squash merge under the user's authorization, verify each original update in main, close superseded PRs, and remove integrated branches with head checks.
7. Verify the remaining remote branch list and post-merge checks. Record exact results and waivers in the PR.

<!-- markdownlint-enable MD013 -->
