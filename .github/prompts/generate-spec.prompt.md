# Generate Spec For Trading Repo

Use the approved requirements document in the target `specs/<NNN-name>/` folder to produce a technical specification for this repository.

## Repository Context

- Python and PowerShell are both first-class stacks.
- `src/` contains reusable PowerShell modules.
- `Backtesting/`, `Journal/`, `Scheduler/`, `rsi_macd_bot/`, and `btc-signal-executor/` are feature areas with their own entry points.
- The repo is paper-trading and learning oriented by default.

## Instructions

1. Read the relevant `requirements.md` and inspect the affected code.
2. Describe the current architecture that the change must fit into.
3. Define concrete implementation boundaries by file or module area.
4. Specify data flow, interfaces, command surfaces, and documentation changes.
5. Include validation expectations for Python and PowerShell where relevant.
6. Explicitly list risks if the change touches order routing, risk controls, scheduler behavior, or journal persistence.

## Output Format

Write `specs/<NNN-name>/spec.md` with:

- scope
- baseline architecture
- proposed design
- impacted files or folders
- data and control flow
- testing and verification strategy
- rollout or compatibility notes
- out-of-scope items
