<!-- markdownlint-disable MD013 -->

# 007 Community and Accessibility Specification

## Classification and Scope

Class 3: repository governance and user-facing accessibility improvements. This change does not alter account permissions, authentication, the trading boundary, deployment, data models, calculations, or existing repository security settings. No Class 4 decision is introduced.

## Community Surface

Root policies define contribution, conduct, support, and accessibility responsibilities. Their ownership is recorded in `PROJECT-STANDARD.md` and `.docs-authority.json`. `CONTRIBUTING.md` links to the existing validation and development authorities rather than duplicating them. The README exposes these routes.

Five GitHub issue forms cover bugs, ideas, documentation, questions, and accessibility. Forms disclose public visibility, request synthetic evidence, and route vulnerabilities to the verified private-report form. Blank issues remain enabled. The PR template requests scope, test evidence, accessibility review, privacy review, and limitations. CODEOWNERS names the verified repository owner for community policy and journal UI review; it does not change branch protection or promise a reviewer response.

The code of conduct uses a truthful contact process: GitHub content-reporting tools for platform abuse and a public request for a private contact route without incident details when no dedicated private conduct address is published. The security policy preserves its existing scope and provides the exact verified private-report link with a safe fallback when unavailable.

## Journal Accessibility

Use native labeled controls, semantic navigation, keyboard activation, predictable focus, sufficient text contrast, visible control boundaries, text status/error feedback, and reduced motion. Prevent repeated requests while a mutation is pending and preserve form data on failure. Keep tables navigable with headings and accessible names. Use synthetic records to exercise success, failure, repeated, and cancelled actions.

Accessibility-related DOM changes must not imply that BUG-009 is fully remediated. Its server-validation and Content Security Policy requirements remain separately tracked.

## Generated Reports

The journal summary, reproducible backtest report, and operations report use document language, viewport metadata, a main landmark, descriptive headings, captions, scoped table headers, visible focus, and keyboard-scrollable table regions where applicable. Provide text values for chart data and status meaning independent of color. Preserve existing computations and escaped output.

## Validation and Evidence

Regression tests run under the existing Python CI suite. Browser checks use synthetic or mocked local data. Report whether real browser, zoom/reflow, screen-reader, and other assistive-technology checks actually ran. GitHub recognition requires a default-branch readback and cannot be inferred from a feature branch. Local and hosted test evidence belongs in the pull request and scoped assessment update.

<!-- markdownlint-enable MD013 -->
