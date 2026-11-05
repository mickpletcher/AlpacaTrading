<!-- markdownlint-disable MD013 -->

# 008 Dependency Consolidation Specification

## Classification and Scope

Class 3: dependency and validation changes. Integrate the remaining Dependabot branches into the current default branch. Trading behavior, account permissions, security settings, application boundaries, and deployment remain unchanged. Existing defects BUG-007 through BUG-009 remain open.

## Coupled Updates

The root Python lock resolves all four requirement inputs together. Align pandas across the root and RSI bot manifests. Apply python-dotenv consistently across all three runtime manifests; the root update subsumes the two component-only patches. Resolve Pydantic and its exact pydantic-core dependency together. Resolve curl-cffi with a compatible yfinance release because yfinance 1.2.0 excludes curl-cffi 0.16.3. Use yfinance 1.2.1, the smallest compatible companion version, and pydantic-core 2.50.2, which Pydantic 2.14.2 requires exactly. Update FastAPI's resolved transitive dependencies only as needed. Preserve the original hash-verified colorama and tzdata entries required by Windows; validate that platform in hosted CI. Preserve NumPy 2.2.6 and its existing pandas-ta/numba constraint unless a demonstrated conflict requires a separate decision.

The two Actions updates retain SHA pins and Python 3.13. Their commits must match the upstream version tags. No workflow permissions or required checks are reduced.

## Verification and Branch Removal

Record source branches, immutable heads, and PR numbers in the integration evidence. Validate the combined dependency graph rather than relying on old checks that installed a stale lock. A squash merge may make ancestry insufficient to identify integrated work; compare updated pins, workflow references, and source diffs before branch removal. Recheck remote heads immediately before deletion so concurrent work is not lost.

Credential-dependent integration is waived because account access is outside scope. Synthetic tests cannot prove broker acceptance, external market-data service compatibility, strategy profitability, or complete accessibility conformance.

<!-- markdownlint-enable MD013 -->
