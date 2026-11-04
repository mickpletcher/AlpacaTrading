<!-- markdownlint-disable MD013 -->
# Contributing to AlpacaTrading

Thank you for helping make this learning toolkit safer, clearer, and easier to use. Documentation, accessibility reports, tests, and small fixes are welcome. Follow the [code of conduct](CODE_OF_CONDUCT.md) and [accessibility guidance](ACCESSIBILITY.md).

## Choose the right route

Use the [issue chooser](https://github.com/mickpletcher/AlpacaTrading/issues/new/choose) for bugs, feature ideas, documentation, accessibility barriers, and questions. A [blank issue](https://github.com/mickpletcher/AlpacaTrading/issues/new) remains available if a form is a barrier. Search existing issues and read [known defects](ISSUES.md) first. Suspected vulnerabilities must use the private process in [SECURITY.md](SECURITY.md), not a public issue or pull request. See [SUPPORT.md](SUPPORT.md) for other help.

All issues, pull requests, attachments, and Actions logs in this repository are public. Use synthetic data. Never include API keys, webhook passphrases, account identifiers, account screenshots, private journal records, database files, or real trading exports.

## Prepare a focused change

1. Follow the safe setup in [README.md](README.md). Use an isolated environment and the hash-verified dependency lock.
2. Read [PROJECT-STANDARD.md](PROJECT-STANDARD.md), which defines change classes and documentation ownership. Non-trivial changes need a numbered package under `specs/` with requirements, specification, plan, and tasks. Read [AGENTS.md](AGENTS.md) when using a coding assistant.
3. Work on a branch from current `main`. Keep one clear purpose per pull request and preserve unrelated work and runtime data.
4. Keep component boundaries and the paper-only safety controls intact. Default automated checks must not use credentials, contact Alpaca, or mutate a paper account. Never enable live trading as part of an unrelated change.
5. Add regression tests for changed behavior. Review affected documentation and add a `changelog.d/` fragment for meaningful changes.
6. Follow the [validation authority](Tests/README.md). Record the exact commands, environment, exit codes, pass/fail/skip counts, and reasons for any check not run. Do not hide failures, weaken tests, or claim checks that did not run.
7. Review the change for accessibility, privacy, and safe failure behavior before publishing it.

## Submit and review

Open a focused pull request against `main`, using the [pull request template](.github/PULL_REQUEST_TEMPLATE.md). Explain the problem, scope, numbered spec, implementation, validation, and remaining limitations. Link related public issues without copying sensitive details. Draft pull requests are useful while validation or discussion is unfinished.

Required checks and resolved review conversations must permit the merge. A passing check is not a claim of profitability, complete accessibility, or freedom from vulnerabilities. Keep feedback specific to the work and give maintainers room to request changes. No review or response deadline is promised.

For UI changes, use keyboard-only testing, visible focus, useful labels, readable contrast, resizing, and clear status messages. Test success and failure flows, repeated clicks, and cancelled actions using synthetic records. For generated reports, check the actual HTML output, including headings and table structure. See [ACCESSIBILITY.md](ACCESSIBILITY.md) for scope and known limits.

## License and attribution

The repository uses the [MIT License](LICENSE). Preserve existing copyright notices and third-party attribution. Only contribute material you have the right to share under the applicable license. Do not add copied datasets, screenshots, or code with incompatible terms.
<!-- markdownlint-enable MD013 -->
