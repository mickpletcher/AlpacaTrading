<!-- markdownlint-disable MD013 -->

# Scheduler Module

This folder helps you run trading scripts automatically instead of manually starting them every day.

If you are new to scheduling, think of this as a timed launcher. It does not invent trading logic. It only starts the right script at the right time and records what happened.

## Related Repo Guides

- [Root README](../README.md)
- [Backtesting Guide](../Backtesting/README.md)
- [Journal Guide](../Journal/README.md)
- [RSI Plus MACD Bot Guide](../rsi_macd_bot/README.md)
- [BTC Signal Executor Guide](../btc-signal-executor/README.md)
- [Tests Guide](../Tests/README.md)
- [Applied Upgrades](../upgrades/README.md)

## Suggested Tutorials

### Tutorial 1: Manual First, Scheduler Second

1. Validate the target script manually using the [Root README](../README.md).
2. Review its behavior in the [Backtesting Guide](../Backtesting/README.md) or module-specific README.
3. Schedule it only after logs and outputs are understood.

### Tutorial 2: Generic Paper Strategy Scheduling

1. Run `Alpaca/paper_trade.py` manually.
2. Use this guide to run `Scheduler/run_strategy.ps1`.
3. Inspect `Journal/scheduler_log.txt` and the [Journal Guide](../Journal/README.md).

### Tutorial 3: Advanced Scheduled Automation

1. For continuous bot workflows, use [rsi_macd_bot/README.md](../rsi_macd_bot/README.md).
2. For externally triggered execution, use [btc-signal-executor/README.md](../btc-signal-executor/README.md).
3. For repo-level changes to scheduling conventions, review [Applied Upgrades](../upgrades/README.md).

## What This Folder Is For

Use this folder when you want to:

- launch a paper trading entry point on a schedule
- load `.env` values automatically before the run starts
- capture run timestamps and exit codes in a log file

Do not use this folder when you need:

- strategy research
- journal analytics
- manual connectivity debugging only

## Files and What They Do

| File | Purpose |
| --- | --- |
| `run_strategy.ps1` | Windows launcher for `Alpaca/paper_trade.py` |
| `run_strategy.sh` | Shell launcher for `Alpaca/paper_trade.py` |
| `README.md` | Scheduling guide |

## Prerequisites

- all root setup steps completed
- `.env` exists in the repo root
- Python available either from `.venv` or system PATH
- strategy entry point tested manually at least once before automation

## What the Generic Scheduler Launches

The generic scheduler scripts launch:

```text
Alpaca/paper_trade.py
```

That file is a scheduler friendly entry point that calls the main paper trading helper.

Scheduler logs are written to:

```text
Journal/scheduler_log.txt
```

## Windows PowerShell Usage

### Run shell launcher manually

```powershell
pwsh -NoProfile -File .\Scheduler\run_strategy.ps1
```

Expected success:

- a new line is added to `Journal/scheduler_log.txt`
- the script launches the paper trading entry point
- the log records `ExitCode=...`

### Register with Windows Task Scheduler

Open an elevated PowerShell session and adjust the path if needed.

```powershell
$action = New-ScheduledTaskAction -Execute "pwsh.exe" -Argument "-NoProfile -File `"C:\path\to\Trading\Scheduler\run_strategy.ps1`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 9:25AM
Register-ScheduledTask -TaskName "TradingPaperStrategy" -Action $action -Trigger $trigger -Description "Run the paper trading strategy near the US market open."
```

Why `9:25 AM` is common:

- it starts the script shortly before the US stock market opens at `9:30 AM` Eastern Time

## Shell Usage

### Run manually first

```bash
bash ./Scheduler/run_strategy.sh
```

### Cron example

```bash
25 9 * * 1-5 /bin/bash /path/to/Trading/Scheduler/run_strategy.sh
```

This assumes the host machine is already using the Eastern Time zone.

## Strategy Specific Scheduler Wrappers

There are also strategy specific PowerShell wrappers in `Backtesting/strategies/`.

Examples:

- `run_ema.ps1`
- `run_bollinger_rsi.ps1`
- `run_rsi_stack.ps1`
- `run_gap_momentum.ps1`

Use those when you want a scheduled launch for a specific strategy instead of the generic paper trading entry point.

For the fully automated RSI plus MACD bot, schedule this entry point directly:

```text
rsi_macd_bot/bot.py
```

The bot setup guide is in `rsi_macd_bot/README.md` and runtime logs are written to `rsi_macd_bot/trades.log`.

For TradingView webhook driven BTC execution, run and supervise:

```text
btc-signal-executor/main.py
```

Use `btc-signal-executor/README.md` for webhook payload format, systemd deployment, and ngrok testing.

### Gap momentum note

Gap momentum is time window sensitive. The PowerShell wrapper documents a two task pattern:

1. one task before the market opens
2. one task after the close for review and confirmation workflows

## Example Usage

### Example 1: Test the Windows launcher manually

```powershell
pwsh -NoProfile -File .\Scheduler\run_strategy.ps1
Get-Content .\Journal\scheduler_log.txt -Tail 5
```

### Example 2: Test the shell launcher manually

```bash
bash ./Scheduler/run_strategy.sh
tail -n 5 ./Journal/scheduler_log.txt
```

## Expected Output

Example log entries:

```text
2026-04-03 09:25:00-04:00    Starting strategy: ...\Alpaca\paper_trade.py
2026-04-03 09:25:03-04:00    ExitCode=0
```

If there is an error, you may also see a `STDERR:` line in the log.

## Common Mistakes

- scheduling a script before testing it manually
- forgetting that market open times are Eastern Time sensitive
- assuming the generic scheduler launches every strategy in the repo
- forgetting to create `.env`
- launching the task under an account that cannot access Python or the repo path

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| task runs but nothing happens | wrong file path or Python not found | test the script manually from the same machine and account |
| `Python was not found in PATH` | Python is not installed or the environment is not visible to the task | use the project `.venv` or fix PATH |
| no log file appears | task lacks permission or wrong working path | confirm the user account can write to `Journal/` |
| timing is wrong | time zone mismatch | confirm Windows or Linux host time zone settings |

## When to Use This Module

Use it when:

- your manual paper trading workflow already works
- you want repeatable timed launches
- you want a simple log of each run

Do not use it when:

- you have not validated credentials yet
- you have not tested the script manually
- you are trying to fix strategy logic bugs

## TODO and Known Gaps

1. The generic scheduler launches `Alpaca/paper_trade.py`, not every strategy module.
2. Several strategy specific scheduling patterns are documented inside the PowerShell wrappers rather than in a unified scheduler config.

<!-- markdownlint-enable MD013 -->
