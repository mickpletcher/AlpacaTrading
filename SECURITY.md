# Security Policy

## Supported Versions

Security fixes are applied to `main` and the latest published release. Older releases are not supported.

## Reporting a Vulnerability

Use GitHub private vulnerability reporting for this repository. Do not open a public issue for a suspected vulnerability.

Include the affected component, reproduction conditions, impact, and the smallest proof needed to confirm the problem. Do not include real API keys, account identifiers, private trading data, or other credentials.

The maintainer will review the report, determine severity and scope, and coordinate disclosure after a fix is available.

## System and Scope

This repository contains local backtesting, paper-trading, scheduling, journal, health, and webhook tools. It is source code, not a maintainer-operated hosted service.

Security-sensitive components include:

- Alpaca authentication, endpoint selection, risk checks, and order submission
- the internet-facing boundary of the BTC webhook when an operator deploys it
- the loopback-only journal and its stored trade data
- local credential, replay, risk, database, log, and report files
- GitHub Actions, dependency automation, release scripts, and repository protection

## Threat Model and Trust Boundaries

Webhook requests, imported CSV data, journal form data, HTTP fields, environment configuration, and external API responses are untrusted.

Local operators and reviewed repository code are trusted only within the permissions they are given. Alpaca, package registries, GitHub Actions, and market-data providers are external dependencies.

Credentials and private runtime data must remain outside Git. The journal must remain bound to loopback. Any public webhook deployment must use controlled TLS ingress and a secret-bearing authentication boundary.

## Security Invariants

- Every order path must fail closed unless it targets the exact Alpaca paper endpoint.
- Live-money order submission must remain unavailable.
- Authentication, replay, rate, quantity, notional, daily-loss, and circuit-breaker checks must run before an order is submitted.
- Untrusted input must not become executable code, SQL, HTML, a file path, a log-control sequence, or a detailed exception response.
- API responses must not expose credentials, secrets, stack traces, internal paths, or private account data.
- Runtime databases, exports, logs, reports, replay state, and risk state must remain local and ignored.
- Default automated checks must not contact Alpaca or mutate an operator's paper account.
- GitHub workflows and releases must use reviewed dependencies and enforced repository protections.

## Reportable Findings and Severity Context

Report vulnerabilities that can realistically:

- cross the paper-only boundary or submit an unauthorized paper order
- bypass authentication, replay, risk, loss, rate, or size controls
- expose credentials, private account data, journal data, or internal implementation details
- allow injection, unsafe file access, or remote execution
- compromise repository workflows, dependencies, protected branches, tags, or releases

Treat any path to live trading, credential theft, arbitrary code execution, or material repository supply-chain compromise as high severity or critical depending on reachability and impact.

## Out of Scope

The following are not security vulnerabilities by themselves:

- strategy profitability, market performance, slippage, or paper-account outcomes
- missing features or documentation without a broken security boundary
- attacks that require prior control of the operator's Windows account or GitHub account, unless the report demonstrates an additional privilege or trust-boundary bypass
- denial of service limited to a manually started local-only process with no effect outside that process

These exclusions do not apply when the behavior also exposes secrets, corrupts protected data, bypasses a safety control, or reaches another trust boundary.

## Known Limitations and Compensating Controls

Current known defects and operating restrictions are maintained in `ISSUES.md`, `TECH-DEBT.md`, and `OPERATIONS.md`. A documented limitation is not automatically an accepted security risk.

The repository defaults to paper trading, keeps the journal on loopback, uses local ignored runtime state, and runs credential-free automated tests. Operators must still supervise paper-order tools as documented in `OPERATIONS.md`.
