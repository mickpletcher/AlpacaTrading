<!-- markdownlint-disable MD013 -->

# 008 Dependency Consolidation Requirements

1. Audit every remote branch against current `main`, preserving unique work and recognizing squash-equivalent or duplicate patches.
2. Integrate the sixteen pending dependency updates as a consistent, tested change. Resolve shared-manifest and transitive constraints instead of merging incompatible pins.
3. Preserve the Python 3.13 hash lock, immutable GitHub Action references, paper-only boundary, runtime data, and protected-PR merge process.
4. Verify all direct requirements against the resolved lock and exercise affected calculations, validation, and rendering with synthetic data.
5. Run clean hash-verified installation, dependency validation, compile checks, full pytest coverage, and required hosted checks on the final head.
6. Merge only after checks pass. Verify each source update is present or explicitly superseded by a compatible dependency resolution before closing its PR and removing its branch.
7. Verify `main` is the only remote branch after cleanup and check post-merge CI. Do not disable future dependency updates or weaken repository protection to achieve cleanup.
8. Do not load brokerage credentials, request account data, or submit paper or live orders.

<!-- markdownlint-enable MD013 -->
