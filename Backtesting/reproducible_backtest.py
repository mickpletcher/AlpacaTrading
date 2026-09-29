from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "evaluation-config.json"
DEFAULT_OUTPUT = ROOT / "output"


@dataclass(frozen=True)
class Metrics:
    total_return_pct: float
    benchmark_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    turnover: float
    trades: int


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    digest.update(content)
    return digest.hexdigest()


def load_configuration(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported evaluation configuration schema.")
    return config


def load_dataset(config_path: Path, config: dict[str, Any]) -> tuple[pd.DataFrame, Path, str]:
    dataset_config = config["dataset"]
    dataset_path = (config_path.parent / dataset_config["path"]).resolve()
    actual_hash = file_sha256(dataset_path)
    expected_hash = str(dataset_config["sha256"]).lower()
    if actual_hash != expected_hash:
        raise ValueError(f"Dataset checksum mismatch. Expected {expected_hash}, got {actual_hash}.")

    data = pd.read_csv(dataset_path, parse_dates=["Date"])
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    if data.empty or data["Date"].duplicated().any() or not data["Date"].is_monotonic_increasing:
        raise ValueError("Dataset dates must be non-empty, unique, and increasing.")
    numeric = ["Open", "High", "Low", "Close", "Volume"]
    if data[numeric].isna().any().any() or (data[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError("Dataset price and volume values must be complete and prices must be positive.")
    return data, dataset_path, actual_hash


def strategy_returns(data: pd.DataFrame, fast: int, slow: int, cost_bps: float) -> tuple[pd.Series, pd.Series]:
    if fast <= 0 or slow <= fast:
        raise ValueError("EMA parameters require 0 < fast < slow.")
    close = data["Close"].astype(float)
    fast_ema = close.ewm(span=fast, adjust=False).mean()
    slow_ema = close.ewm(span=slow, adjust=False).mean()
    position = (fast_ema > slow_ema).astype(float)
    position.iloc[:slow] = 0.0
    market_returns = close.pct_change().fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs())
    net_returns = position.shift(1).fillna(0.0) * market_returns - turnover * (cost_bps / 10_000.0)
    return net_returns, position


def benchmark_returns(data: pd.DataFrame, cost_bps: float) -> pd.Series:
    returns = data["Close"].astype(float).pct_change().fillna(0.0)
    if len(returns) > 1:
        returns.iloc[0] -= cost_bps / 10_000.0
        returns.iloc[-1] -= cost_bps / 10_000.0
    return returns


def calculate_metrics(returns: pd.Series, benchmark: pd.Series, position: pd.Series) -> Metrics:
    equity = (1.0 + returns).cumprod()
    benchmark_equity = (1.0 + benchmark).cumprod()
    total_return = float((equity.iloc[-1] - 1.0) * 100.0)
    benchmark_return = float((benchmark_equity.iloc[-1] - 1.0) * 100.0)
    standard_deviation = float(returns.std(ddof=0))
    sharpe = float(math.sqrt(252) * returns.mean() / standard_deviation) if standard_deviation > 0 else 0.0
    drawdown = equity / equity.cummax() - 1.0
    turnover = float(position.diff().abs().fillna(position.abs()).sum())
    entries = int(((position == 1.0) & (position.shift(1).fillna(0.0) == 0.0)).sum())
    return Metrics(
        total_return_pct=round(total_return, 6),
        benchmark_return_pct=round(benchmark_return, 6),
        annualized_volatility_pct=round(standard_deviation * math.sqrt(252) * 100.0, 6),
        sharpe_ratio=round(sharpe, 6),
        max_drawdown_pct=round(float(drawdown.min() * 100.0), 6),
        turnover=round(turnover, 6),
        trades=entries,
    )


def evaluate(data: pd.DataFrame, parameters: dict[str, int], total_cost_bps: float) -> tuple[Metrics, list[float]]:
    returns, position = strategy_returns(data, parameters["fast"], parameters["slow"], total_cost_bps)
    benchmark = benchmark_returns(data, total_cost_bps)
    metrics = calculate_metrics(returns, benchmark, position)
    equity = ((1.0 + returns).cumprod() * 100.0).round(6).tolist()
    return metrics, equity


def choose_parameters(data: pd.DataFrame, grid: list[dict[str, int]], total_cost_bps: float) -> dict[str, int]:
    scored: list[tuple[float, float, int, int]] = []
    for parameters in grid:
        metrics, _ = evaluate(data, parameters, total_cost_bps)
        scored.append((metrics.sharpe_ratio, metrics.total_return_pct, -parameters["fast"], -parameters["slow"]))
    best = max(scored)
    return {"fast": -best[2], "slow": -best[3]}


def build_report(config_path: Path) -> dict[str, Any]:
    config = load_configuration(config_path)
    data, dataset_path, dataset_hash = load_dataset(config_path, config)
    cost_config = config["costs"]
    total_cost_bps = float(cost_config["commission_bps"]) + float(cost_config["slippage_bps"])
    grid = [{"fast": int(item["fast"]), "slow": int(item["slow"])} for item in config["parameter_grid"]]

    fixed = config["fixed_split"]
    training_bars = int(fixed["training_bars"])
    out_bars = int(fixed["out_of_sample_bars"])
    if training_bars + out_bars > len(data):
        raise ValueError("Fixed split is larger than the dataset.")
    training = data.iloc[:training_bars].reset_index(drop=True)
    out_sample = data.iloc[training_bars : training_bars + out_bars].reset_index(drop=True)
    selected = choose_parameters(training, grid, total_cost_bps)
    training_metrics, _ = evaluate(training, selected, total_cost_bps)
    out_metrics, out_equity = evaluate(out_sample, selected, total_cost_bps)

    walk = config["walk_forward"]
    walk_train = int(walk["training_bars"])
    walk_test = int(walk["test_bars"])
    walk_step = int(walk["step_bars"])
    folds: list[dict[str, Any]] = []
    fold_number = 1
    for test_start in range(walk_train, len(data) - walk_test + 1, walk_step):
        train_start = test_start - walk_train
        train = data.iloc[train_start:test_start].reset_index(drop=True)
        test = data.iloc[test_start : test_start + walk_test].reset_index(drop=True)
        parameters = choose_parameters(train, grid, total_cost_bps)
        metrics, _ = evaluate(test, parameters, total_cost_bps)
        folds.append(
            {
                "fold": fold_number,
                "training_start": train["Date"].iloc[0].date().isoformat(),
                "training_end": train["Date"].iloc[-1].date().isoformat(),
                "test_start": test["Date"].iloc[0].date().isoformat(),
                "test_end": test["Date"].iloc[-1].date().isoformat(),
                "selected_parameters": parameters,
                "metrics": asdict(metrics),
            }
        )
        fold_number += 1

    return {
        "schema_version": 1,
        "dataset": {
            "path": dataset_path.relative_to(ROOT).as_posix(),
            "sha256": dataset_hash,
            "symbol": config["dataset"]["symbol"],
            "source": config["dataset"]["source"],
            "rows": len(data),
            "start": data["Date"].iloc[0].date().isoformat(),
            "end": data["Date"].iloc[-1].date().isoformat(),
        },
        "costs": {
            "commission_bps": float(cost_config["commission_bps"]),
            "slippage_bps": float(cost_config["slippage_bps"]),
            "total_per_position_change_bps": total_cost_bps,
        },
        "fixed_split": {
            "training_bars": training_bars,
            "out_of_sample_bars": out_bars,
            "training_start": training["Date"].iloc[0].date().isoformat(),
            "training_end": training["Date"].iloc[-1].date().isoformat(),
            "out_of_sample_start": out_sample["Date"].iloc[0].date().isoformat(),
            "out_of_sample_end": out_sample["Date"].iloc[-1].date().isoformat(),
            "selected_parameters": selected,
            "training_metrics": asdict(training_metrics),
            "out_of_sample_metrics": asdict(out_metrics),
            "out_of_sample_equity": out_equity,
        },
        "walk_forward": {
            "training_bars": walk_train,
            "test_bars": walk_test,
            "step_bars": walk_step,
            "folds": folds,
        },
    }


def _equity_svg(values: list[float]) -> str:
    width, height = 900, 240
    if not values:
        return ""
    minimum, maximum = min(values), max(values)
    span = maximum - minimum or 1.0
    points = []
    for index, value in enumerate(values):
        x = 10 + index * (width - 20) / max(1, len(values) - 1)
        y = 10 + (maximum - value) * (height - 20) / span
        points.append(f"{x:.2f},{y:.2f}")
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Out-of-sample equity curve"><polyline points="{" ".join(points)}" fill="none" stroke="#2563eb" stroke-width="3"/></svg>'


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation-report.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    folds = report["walk_forward"]["folds"]
    with (output_dir / "walk-forward.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["fold", "training_start", "training_end", "test_start", "test_end", "fast", "slow", "return_pct", "benchmark_pct", "sharpe", "max_drawdown_pct", "trades"])
        for fold in folds:
            metrics = fold["metrics"]
            parameters = fold["selected_parameters"]
            writer.writerow([fold["fold"], fold["training_start"], fold["training_end"], fold["test_start"], fold["test_end"], parameters["fast"], parameters["slow"], metrics["total_return_pct"], metrics["benchmark_return_pct"], metrics["sharpe_ratio"], metrics["max_drawdown_pct"], metrics["trades"]])

    fixed = report["fixed_split"]
    metrics = fixed["out_of_sample_metrics"]
    rows = "".join(
        f"<tr><td>{fold['fold']}</td><td>{html.escape(fold['test_start'])} to {html.escape(fold['test_end'])}</td><td>{fold['selected_parameters']['fast']}/{fold['selected_parameters']['slow']}</td><td>{fold['metrics']['total_return_pct']:.2f}%</td><td>{fold['metrics']['benchmark_return_pct']:.2f}%</td></tr>"
        for fold in folds
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reproducible Backtest Report</title>
<style>body{{font-family:Segoe UI,sans-serif;margin:0;background:#f3f6fb;color:#172033}}main{{max-width:1100px;margin:32px auto;padding:28px;background:white;border-radius:16px;box-shadow:0 8px 30px #0001}}h1{{margin-top:0}}.meta{{color:#526078}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{padding:16px;background:#eef4ff;border-radius:12px}}.value{{font-size:28px;font-weight:700}}svg{{width:100%;height:240px;background:#fbfdff;border:1px solid #d8e2f0;border-radius:12px}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #dce3ec}}code{{word-break:break-all}}@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}}}</style></head>
<body><main><h1>Reproducible Backtest Report</h1><p class="meta">Sanitized fixed fixture. No account or credential data.</p>
<p><strong>Dataset:</strong> {html.escape(report['dataset']['symbol'])}, {report['dataset']['rows']} rows, {html.escape(report['dataset']['start'])} to {html.escape(report['dataset']['end'])}<br><strong>SHA-256:</strong> <code>{report['dataset']['sha256']}</code><br><strong>Costs:</strong> {report['costs']['commission_bps']:.1f} bps commission plus {report['costs']['slippage_bps']:.1f} bps slippage per position change</p>
<h2>Fixed out-of-sample result</h2><p>Parameters {fixed['selected_parameters']['fast']}/{fixed['selected_parameters']['slow']} were selected on {fixed['training_start']} to {fixed['training_end']}, then evaluated once on {fixed['out_of_sample_start']} to {fixed['out_of_sample_end']}.</p>
<div class="cards"><div class="card"><div>Strategy return</div><div class="value">{metrics['total_return_pct']:.2f}%</div></div><div class="card"><div>Buy and hold</div><div class="value">{metrics['benchmark_return_pct']:.2f}%</div></div><div class="card"><div>Sharpe ratio</div><div class="value">{metrics['sharpe_ratio']:.2f}</div></div><div class="card"><div>Max drawdown</div><div class="value">{metrics['max_drawdown_pct']:.2f}%</div></div></div>
<h2>Out-of-sample equity</h2>{_equity_svg(fixed['out_of_sample_equity'])}
<h2>Walk-forward folds</h2><table><thead><tr><th>Fold</th><th>Test period</th><th>EMA</th><th>Strategy</th><th>Benchmark</th></tr></thead><tbody>{rows}</tbody></table>
<p class="meta">Historical and synthetic results do not predict future performance.</p></main></body></html>"""
    (output_dir / "evaluation-report.html").write_text(document, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the checksum-verified reproducible EMA evaluation.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.config.resolve())
        if not args.verify_only:
            write_outputs(report, args.output.resolve())
        fixed = report["fixed_split"]
        metrics = fixed["out_of_sample_metrics"]
        print(f"Dataset verified: {report['dataset']['sha256']}")
        print(f"Selected EMA: {fixed['selected_parameters']['fast']}/{fixed['selected_parameters']['slow']}")
        print(f"Out-of-sample return: {metrics['total_return_pct']:.2f}%")
        print(f"Buy-and-hold return: {metrics['benchmark_return_pct']:.2f}%")
        print(f"Walk-forward folds: {len(report['walk_forward']['folds'])}")
        if not args.verify_only:
            print(f"Report: {(args.output.resolve() / 'evaluation-report.html')}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Evaluation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
