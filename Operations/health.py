from __future__ import annotations

import argparse
import html
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ALPACA_DIR = ROOT / "Alpaca"
if str(ALPACA_DIR) not in sys.path:
    sys.path.insert(0, str(ALPACA_DIR))

DEFAULT_CONFIG = Path(__file__).resolve().parent / "health-config.example.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "runtime"
SEVERITY_ORDER = {"PASS": 0, "UNKNOWN": 1, "WARN": 1, "FAIL": 2}


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    summary: str
    evidence: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def check_stale_file(root: Path, item: dict[str, Any], now: datetime) -> CheckResult:
    path = root / item["path"]
    required = bool(item.get("required", False))
    if not path.exists():
        status = "FAIL" if required else "UNKNOWN"
        return CheckResult(f"Stale data: {item['name']}", status, "File is missing.", item["path"])
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_minutes = (now - modified).total_seconds() / 60.0
    maximum = float(item["max_age_minutes"])
    status = "PASS" if age_minutes <= maximum else "FAIL"
    summary = f"Last update was {age_minutes:.1f} minutes ago; limit is {maximum:.1f}."
    return CheckResult(f"Stale data: {item['name']}", status, summary, item["path"])


def check_rejected_orders(root: Path, config: dict[str, Any], now: datetime) -> CheckResult:
    patterns = [str(item).lower() for item in config["rejected_order_patterns"]]
    cutoff_minutes = float(config["rejected_order_lookback_minutes"])
    inspected = 0
    matches: list[str] = []
    for relative in config["rejected_order_logs"]:
        path = root / relative
        if not path.exists():
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if (now - modified).total_seconds() / 60.0 > cutoff_minutes:
            continue
        inspected += 1
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-500:]
        for line in lines:
            if any(pattern in line.lower() for pattern in patterns):
                matches.append(f"{relative}: {line[-240:]}")
    if matches:
        return CheckResult("Rejected orders", "FAIL", f"Found {len(matches)} rejection or API error event(s).", " | ".join(matches[:5]))
    if inspected == 0:
        return CheckResult("Rejected orders", "UNKNOWN", "No recent order log was available.", "No matching log file within the lookback window.")
    return CheckResult("Rejected orders", "PASS", "No rejection pattern was found in recent logs.", f"Inspected {inspected} log file(s).")


def check_scheduler(root: Path, config: dict[str, Any], now: datetime) -> CheckResult:
    relative = config["scheduler_status_path"]
    path = root / relative
    if not path.exists():
        return CheckResult("Scheduler run", "UNKNOWN", "Scheduler status is missing.", relative)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CheckResult("Scheduler run", "FAIL", "Scheduler status is unreadable.", str(exc))
    finished = parse_time(str(state.get("finished_at", "")))
    if finished is None:
        return CheckResult("Scheduler run", "WARN", "The scheduler has no completed timestamp.", relative)
    age = (now - finished).total_seconds() / 60.0
    if age > float(config["scheduler_max_age_minutes"]):
        return CheckResult("Scheduler run", "FAIL", f"Last completed run is stale at {age:.1f} minutes.", relative)
    exit_code = state.get("exit_code")
    if exit_code != 0:
        return CheckResult("Scheduler run", "FAIL", f"Last run exited with code {exit_code}.", str(state.get("error", "")))
    return CheckResult("Scheduler run", "PASS", f"Last run completed {age:.1f} minutes ago with exit code 0.", relative)


def check_circuit_breaker(root: Path, config: dict[str, Any], now: datetime) -> CheckResult:
    relative = config["circuit_state_path"]
    path = root / relative
    if not path.exists():
        return CheckResult("Circuit breaker", "UNKNOWN", "Circuit-breaker state is missing.", relative)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CheckResult("Circuit breaker", "FAIL", "Circuit-breaker state is unreadable.", str(exc))
    if bool(state.get("auth_blocked")):
        return CheckResult("Circuit breaker", "FAIL", "Authentication is blocked.", str(state.get("auth_reason", "")))
    pause_until = parse_time(str(state.get("pause_until", "")))
    if pause_until is not None and pause_until > now:
        return CheckResult("Circuit breaker", "FAIL", f"Trading is paused until {pause_until.isoformat()}.", str(state.get("pause_reason", "")))
    losses = int(state.get("consecutive_losses", 0) or 0)
    if losses > 0:
        return CheckResult("Circuit breaker", "WARN", f"Circuit is closed with {losses} consecutive loss(es).", relative)
    return CheckResult("Circuit breaker", "PASS", "Circuit is closed and authentication is not blocked.", relative)


def missing_stop_symbols(positions: Iterable[Any], orders: Iterable[Any]) -> list[str]:
    protected: dict[str, float] = {}
    for order in orders:
        order_type = str(getattr(order, "type", "")).lower()
        side = str(getattr(order, "side", "")).lower()
        if "stop" not in order_type or "sell" not in side:
            continue
        symbol = str(getattr(order, "symbol", "")).upper()
        protected[symbol] = protected.get(symbol, 0.0) + float(getattr(order, "qty", 0) or 0)
    missing: list[str] = []
    for position in positions:
        symbol = str(getattr(position, "symbol", "")).upper()
        quantity = abs(float(getattr(position, "qty", 0) or 0))
        if quantity > 0 and protected.get(symbol, 0.0) + 1e-9 < quantity:
            missing.append(symbol)
    return sorted(missing)


def check_missing_stops(config: dict[str, Any]) -> CheckResult:
    if not bool(config.get("check_paper_account_stops", True)):
        return CheckResult("Protective stops", "UNKNOWN", "Paper-account stop inspection is disabled.", "Enable check_paper_account_stops to inspect read-only account state.")
    api_key = os.getenv("ALPACA_API_KEY", "").strip()
    secret_key = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        return CheckResult("Protective stops", "UNKNOWN", "Paper credentials are unavailable.", "No account request was made.")
    try:
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest
        from trading_safety import PaperTradingClient

        client = PaperTradingClient(api_key=api_key, secret_key=secret_key)
        positions = client.get_all_positions()
        orders = client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
        missing = missing_stop_symbols(positions, orders)
    except Exception as exc:
        return CheckResult("Protective stops", "UNKNOWN", "Paper-account inspection failed.", f"{type(exc).__name__}: {exc}")
    if missing:
        return CheckResult("Protective stops", "FAIL", f"Position(s) lack matching open sell-stop quantity: {', '.join(missing)}.", "Read-only paper-account comparison.")
    return CheckResult("Protective stops", "PASS", "Every open paper position has matching open sell-stop quantity.", f"Checked {len(positions)} position(s).")


def run_checks(config_path: Path, root: Path = ROOT, now: datetime | None = None) -> list[CheckResult]:
    active_now = now or utc_now()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported health configuration schema.")
    results = [check_stale_file(root, item, active_now) for item in config["stale_files"]]
    results.extend([check_rejected_orders(root, config, active_now), check_scheduler(root, config, active_now), check_circuit_breaker(root, config, active_now), check_missing_stops(config)])
    return results


def write_report(results: list[CheckResult], output_dir: Path, now: datetime) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    worst = max((SEVERITY_ORDER[result.status] for result in results), default=0)
    overall = "FAIL" if worst == 2 else "ATTENTION" if worst == 1 else "PASS"
    payload = {"schema_version": 1, "checked_at": now.isoformat(), "overall": overall, "checks": [asdict(result) for result in results]}
    (output_dir / "health-status.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    alerts = [result for result in results if result.status != "PASS"]
    if alerts:
        with (output_dir / "health-alerts.log").open("a", encoding="utf-8") as stream:
            for result in alerts:
                stream.write(f"{now.isoformat()}\t{result.status}\t{result.name}\t{result.summary}\n")
    rows = "".join(f"<tr><td><span class=\"status {result.status.lower()}\">{html.escape(result.status)}</span></td><td>{html.escape(result.name)}</td><td>{html.escape(result.summary)}</td><td><code>{html.escape(result.evidence)}</code></td></tr>" for result in results)
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local Trading Health</title><style>body{{font-family:Segoe UI,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}main{{max-width:1150px;margin:32px auto;background:white;padding:28px;border-radius:16px;box-shadow:0 8px 28px #0001}}h1{{margin-top:0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #dde3ea;vertical-align:top}}.status{{font-weight:700;padding:5px 9px;border-radius:20px}}.pass{{background:#dff5e5;color:#176b32}}.warn,.unknown{{background:#fff3cd;color:#755800}}.fail{{background:#fde2e2;color:#991b1b}}code{{white-space:normal;word-break:break-word}}.meta{{color:#5d6878}}</style></head><body><main><h1>Local Trading Health</h1><p class="meta">Checked {html.escape(now.isoformat())}. Overall: <strong>{overall}</strong>. Read-only checks; no order was submitted.</p><table><thead><tr><th>Status</th><th>Check</th><th>Summary</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>"""
    (output_dir / "health-report.html").write_text(document, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect local paper-trading health without submitting orders.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = utc_now()
    try:
        results = run_checks(args.config.resolve(), now=now)
        write_report(results, args.output.resolve(), now)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Health check failed: {exc}")
        return 2
    if args.json_output:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            print(f"{result.status:<7} {result.name}: {result.summary}")
        print(f"Report: {(args.output.resolve() / 'health-report.html')}")
    return max((SEVERITY_ORDER[result.status] for result in results), default=0)


if __name__ == "__main__":
    raise SystemExit(main())
