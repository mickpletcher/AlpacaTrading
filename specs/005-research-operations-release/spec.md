<!-- markdownlint-disable MD013 MD024 MD060 -->

# 005 Research, Operations, and Release Specification

## Classification

Class 3. This package adds functional research, operations, dependency, validation, and release interfaces. It does not change the live-trading trust boundary.

## Reproducible Evaluation

`Backtesting/reproducible_backtest.py` reads a versioned JSON configuration and a repository dataset. It verifies the dataset SHA-256 before calculation. The first fixed split selects an EMA parameter pair on training data and evaluates it once on held-out data. Rolling folds repeat selection using only each fold's training window.

The evaluator models commission and slippage in basis points at every position change. It reports strategy and buy-and-hold return, annualized volatility, Sharpe ratio, maximum drawdown, turnover, trade count, fold boundaries, selected parameters, and configuration metadata. JSON and HTML output are deterministic apart from an optional generated timestamp that is excluded from equality tests.

## Local Health

`Operations/health.py` reads an example-backed JSON configuration, scheduler state, bot and strategy logs, circuit-breaker state, and optional read-only Alpaca paper account data. Missing runtime evidence produces `UNKNOWN`. Active rejected-order evidence, stale files, open circuit breakers, nonzero scheduler exits, and positions without matching sell stop orders produce alerts.

The command writes `Operations/runtime/health-status.json`, `health-report.html`, and `health-alerts.log`. Exit code 0 means no fail state, 1 means warning or unknown state, and 2 means at least one failed check.

## Coverage

Python coverage uses pytest-cov and fails below the committed aggregate threshold. Pester measures `src/` modules and fails below its committed threshold. CI uploads XML and PowerShell coverage artifacts even when a threshold fails.

## Dependency Lock

`requirements.lock.txt` is generated from all three direct requirement files with a pinned pip-tools version and hashes. CI installs only from the lock with `--require-hashes`. A PowerShell refresh script regenerates the lock and checks the installed environment.

## Screenshots

Actual sanitized screenshots are PNG files captured from the deterministic backtest report, a journal instance containing synthetic records, and credential-free paper-helper command output. No API key, account identifier, local user path, or private market activity may be visible.

## Release Process

`scripts/New-Release.ps1` validates semantic version input and repository state, runs the release checks, consolidates sorted Markdown fragments into a dated changelog section, and supports a preparation-only path. `-Publish` is the only path allowed to commit, tag, push, and invoke `gh release create`. Existing tags and releases fail closed.

## Evidence Boundary

CI and release validation can prove deterministic local behavior. They cannot prove broker acceptance or profitability. Credential-dependent paper integration remains a recorded waiver.

<!-- markdownlint-enable MD013 MD024 MD060 -->
