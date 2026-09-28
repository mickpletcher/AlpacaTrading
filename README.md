<!-- markdownlint-disable MD013 -->

# Trading Repository

Mixed Python and PowerShell trading tooling for Alpaca paper trading, strategy backtesting, journaling, scheduling, and trading workflow learning.

> [!WARNING]
> This repository is for education and paper-trading workflow development. It is not financial advice, and it should not be treated as production live-trading software without additional controls.

## Current Status

- Status: Active, paper-trading and research use only
- Execution boundary: Python and PowerShell order paths fail closed to Alpaca paper trading
- Documentation standard: 2.2
- Project tier: 2
- Primary technologies: Python, PowerShell, Flask, FastAPI, SQLite

For current repository health, risks, and priorities, see the [Current Assessment](docs/repo-audit.md).

## What The Project Does Today

This repository already supports six main workflows:

1. Alpaca paper-trading helpers in Python and PowerShell under `Alpaca/`
2. Strategy research and replay under `Backtesting/`
3. A browser-based trade journal and CSV/HTML reporting under `Journal/`
4. Windows and shell scheduling entry points under `Scheduler/`
5. A standalone RSI plus MACD bot under `rsi_macd_bot/`
6. A FastAPI webhook executor for BTC signals under `btc-signal-executor/`

The repo also includes a modular PowerShell Alpaca client under `src/`, example PowerShell scripts under `examples/`, Python strategy tests, and PowerShell module tests under `Tests/`.

## Documentation

- [Authority Map And Development Rules](PROJECT-STANDARD.md)
- [Current Assessment](docs/repo-audit.md)
- [Architecture](ARCHITECTURE.md)
- [Validation](Tests/README.md)
- [Operations](OPERATIONS.md)
- [Defects](ISSUES.md)
- [Technical Debt](TECH-DEBT.md)
- [Future Upgrades](FUTURE-UPGRADES.md)
- [Change History](CHANGELOG.md)
- [Applied Upgrades](upgrades/README.md)
- [Core Trading Foundation Spec](specs/001-core-trading-foundation/spec.md)
- [Backtesting Guide](Backtesting/README.md)
- [Journal Guide](Journal/README.md)
- [Scheduler Guide](Scheduler/README.md)
- [Learning Roadmap](Learning%20Roadmap/README.md)
- [RSI Plus MACD Bot Guide](rsi_macd_bot/README.md)
- [BTC Signal Executor Guide](btc-signal-executor/README.md)

## Recommended Tutorials

### Tutorial 1: First Safe Walkthrough

1. Read the [Learning Roadmap](Learning%20Roadmap/README.md).
2. Complete the root setup steps in this file.
3. Run `python .\Backtesting\backtest.py`.
4. Open the [Journal Guide](Journal/README.md) and run the journal app.
5. Run the [Tests Guide](Tests/README.md) Python checks.

### Tutorial 2: Strategy To Review Loop

1. Use the [Backtesting Guide](Backtesting/README.md) to run one strategy backtest.
2. Review generated trade output in [Journal](Journal/README.md).
3. Use the [Scheduler Guide](Scheduler/README.md) only after the manual flow works.

### Tutorial 3: Advanced Automation Paths

1. Read [RSI Plus MACD Bot Guide](rsi_macd_bot/README.md) for a scheduled bot loop.
2. Read [BTC Signal Executor Guide](btc-signal-executor/README.md) for webhook-based execution.
3. Review the [Project Standard](PROJECT-STANDARD.md), [Applied Upgrades](upgrades/README.md), and relevant numbered spec before structural repo changes.

## Current Architecture

The repository is a collection of independently executable trading tools rather than one deployable application. See [ARCHITECTURE.md](ARCHITECTURE.md) for evidence, data flow, integrations, storage, and safety boundaries.

## Setup

### Prerequisites

- Python 3.13 recommended
- PowerShell 7 recommended for module and automation workflows
- An Alpaca paper account if you want connectivity or paper-trading runs

### Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Populate `.env` with Alpaca paper credentials before running connectivity or paper-trading commands.

## Usage

### Run the baseline backtester

```powershell
python .\Backtesting\backtest.py
```

### Run the journal app

```powershell
python .\Journal\journal_server.py
```

Then open `http://localhost:5000`.

### Run paper trading helpers

```powershell
python .\Alpaca\paper_trade.py
pwsh -NoProfile -File .\Alpaca\alpaca_paper.ps1
```

### Run the Python test suite

```powershell
.\.venv\Scripts\python.exe -m pytest .\Tests -q
```

### Run PowerShell module checks manually

```powershell
pwsh -NoProfile -Command "Get-ChildItem .\src -Recurse -Filter *.psd1 | ForEach-Object { Test-ModuleManifest $_.FullName | Out-Null }"
```

## Development Workflow

Future repository work should follow the retrofit GitHub Spec process now included in this repo:

1. Capture the change in `specs/<NNN-name>/requirements.md`
2. Convert requirements into implementation detail in `spec.md`
3. Create an execution plan in `plan.md`
4. Break the work into discrete tasks in `tasks.md`
5. Implement with the spec open and update docs/tests alongside code
6. Run an audit against the completed change
7. Run regression checks before merge

Validation procedures and current limitations are maintained in [Tests/README.md](Tests/README.md). Current executed results are maintained in the [Current Assessment](docs/repo-audit.md).

## GitHub Spec Workflow

This repository now includes:

- `AGENTS.md` for authoritative repo-specific implementation guidance
- `.github/prompts/` for reusable requirements, spec, plan, task, audit, regression, and release prompts
- `specs/001-core-trading-foundation/` as the baseline spec retrofit for the current repository state
- `docs/repo-audit.md` as the current repository assessment
- `upgrades/README.md` as the applied-upgrades log for repo-level improvements

When adding a new feature, create the next numbered folder under `specs/` and keep the change grounded in the current architecture rather than reimagining the project.

## Repository Structure

```text
Trading/
|-- .github/
|   |-- copilot-instructions.md
|   |-- prompts/
|   `-- workflows/
|-- docs/
|   |-- repo-audit.md
|   |-- decisions/
|   `-- screenshots/
|-- specs/
|   |-- 001-core-trading-foundation/
|   `-- 002-living-documentation-standard/
|-- src/
|-- Alpaca/
|-- Backtesting/
|-- Journal/
|-- Scheduler/
|-- rsi_macd_bot/
|-- btc-signal-executor/
|-- examples/
|-- Tests/
|-- AGENTS.md
|-- ARCHITECTURE.md
|-- OPERATIONS.md
|-- PROJECT-STANDARD.md
|-- .env.example
|-- .gitignore
|-- pytest.ini
|-- README.md
`-- requirements.txt
```

## Known Limitations

See [ISSUES.md](ISSUES.md) for active defects and [TECH-DEBT.md](TECH-DEBT.md) for accepted implementation risks. The BTC webhook is paper-only and requires the limits, replay database, passphrase, and ingress controls documented in its component guide.

<!-- markdownlint-enable MD013 -->
