from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from Backtesting.reproducible_backtest import (
    DEFAULT_CONFIG,
    build_report,
    evaluate,
    load_configuration,
    load_dataset,
    write_outputs,
)


def test_repeated_reports_are_identical_and_contain_walk_forward_evidence(tmp_path: Path) -> None:
    first = build_report(DEFAULT_CONFIG)
    second = build_report(DEFAULT_CONFIG)

    assert first == second
    assert first["dataset"]["rows"] == 320
    assert len(first["walk_forward"]["folds"]) == 5
    assert first["fixed_split"]["training_end"] < first["fixed_split"]["out_of_sample_start"]

    write_outputs(first, tmp_path)
    assert json.loads((tmp_path / "evaluation-report.json").read_text(encoding="utf-8")) == first
    assert (tmp_path / "evaluation-report.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert (tmp_path / "walk-forward.csv").exists()


def test_costs_reduce_strategy_return() -> None:
    config = load_configuration(DEFAULT_CONFIG)
    data, _, _ = load_dataset(DEFAULT_CONFIG, config)
    parameters = {"fast": 9, "slow": 21}

    no_cost, _ = evaluate(data, parameters, 0.0)
    with_cost, _ = evaluate(data, parameters, 8.0)

    assert with_cost.total_return_pct < no_cost.total_return_pct
    assert with_cost.turnover == no_cost.turnover


def test_dataset_checksum_mismatch_fails_closed(tmp_path: Path) -> None:
    config = load_configuration(DEFAULT_CONFIG)
    source = DEFAULT_CONFIG.parent / config["dataset"]["path"]
    dataset = tmp_path / "sample.csv"
    dataset.write_bytes(source.read_bytes() + b"\n")
    config["dataset"]["path"] = "sample.csv"
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_dataset(config_path, config)


def test_dataset_checksum_is_stable_across_line_endings(tmp_path: Path) -> None:
    config = load_configuration(DEFAULT_CONFIG)
    source = DEFAULT_CONFIG.parent / config["dataset"]["path"]
    dataset = tmp_path / "sample.csv"
    dataset.write_bytes(source.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    config["dataset"]["path"] = "sample.csv"
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    data, _, actual_hash = load_dataset(config_path, config)

    assert len(data) == 320
    assert actual_hash == config["dataset"]["sha256"]


def test_walk_forward_test_windows_do_not_overlap_training_future() -> None:
    report = build_report(DEFAULT_CONFIG)
    folds = report["walk_forward"]["folds"]

    for fold in folds:
        assert pd.Timestamp(fold["training_end"]) < pd.Timestamp(fold["test_start"])
    for previous, current in zip(folds, folds[1:]):
        assert pd.Timestamp(previous["test_start"]) < pd.Timestamp(current["test_start"])
