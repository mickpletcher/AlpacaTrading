<!-- markdownlint-disable MD013 MD024 MD060 -->

# 005 Research, Operations, and Release Plan

1. Establish the dependency lock and coverage dependencies.
2. Add coverage commands and CI gates so later work is measured immediately.
3. Implement the deterministic dataset, evaluator, reports, and tests.
4. Implement local health collection, scheduler status, reports, and tests.
5. Generate sanitized screenshots from the completed local interfaces.
6. Implement release validation, changelog consolidation, tag, push, and GitHub release automation.
7. Run full Python, PowerShell, dependency, documentation, screenshot, and release dry-run validation.
8. Update living authorities, remove completed proposals and debt, and append resolved history.

This order minimizes repeated environment and documentation work. The release process is last because it consumes the lock, coverage gates, reports, and final validation commands.

<!-- markdownlint-enable MD013 MD024 MD060 -->
