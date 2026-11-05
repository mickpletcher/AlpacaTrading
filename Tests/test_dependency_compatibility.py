"""Offline dependency smoke checks using synthetic data and temporary artifacts."""

from __future__ import annotations

import importlib.util
import re
import socket
import sys
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT_INPUTS = (
    "requirements.txt",
    "requirements-dev.txt",
    "rsi_macd_bot/requirements.txt",
    "btc-signal-executor/requirements.txt",
)


@pytest.fixture
def offline(monkeypatch):
    """Fail rather than accidentally connecting to a provider during smoke tests."""
    def forbidden(*args, **kwargs):
        raise AssertionError("Dependency smoke tests must not access the network")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def _pins(path: Path) -> dict[str, str]:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith(("#", "--")):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)(?:\s+\\)?", line.strip())
        assert match is not None, f"Review unsupported requirement syntax in {path}: {line}"
        name = re.sub(r"[-_.]+", "-", match[1]).lower()
        assert name not in pins, f"Duplicate requirement {name} in {path}"
        pins[name] = match[2]
    return pins


def test_all_direct_requirements_match_hash_lock():
    locked = _pins(ROOT / "requirements.lock.txt")
    for relative_path in REQUIREMENT_INPUTS:
        for name, version in _pins(ROOT / relative_path).items():
            assert locked.get(name) == version, (
                f"{relative_path}: {name}=={version} differs from lock "
                f"({locked.get(name)}); align all inputs and regenerate the lock"
            )


def test_real_rsi_macd_indicators_with_synthetic_prices(offline, monkeypatch):
    # Only configuration constants are replaced. The actual pandas-ta indicator
    # implementations run, without importing credential/environment configuration.
    config = types.ModuleType("config")
    config.RSI_OVERBOUGHT = 70
    config.RSI_OVERSOLD = 30
    config.SIGNAL_WINDOW = 3
    spec = importlib.util.spec_from_file_location(
        "dependency_smoke_rsi_indicators", ROOT / "rsi_macd_bot" / "indicators.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    missing = object()
    previous_config = sys.modules.get("config", missing)
    with monkeypatch.context() as isolated:
        isolated.setitem(sys.modules, "config", config)
        spec.loader.exec_module(module)
    assert sys.modules.get("config", missing) is previous_config

    steps = np.arange(160, dtype=float)
    source = pd.DataFrame({"close": 100 + steps * 0.05 + 5 * np.sin(steps / 5)})
    original = source.copy(deep=True)
    calculated = module.calculate_macd(module.calculate_rsi(source))
    pd.testing.assert_frame_equal(source, original)
    assert len(calculated) == len(source)
    assert calculated["rsi"].dropna().between(0, 100).all()
    assert calculated["rsi"].notna().sum() > 100
    mature = calculated[["macd", "macd_signal", "macd_hist"]].tail(100)
    assert np.isfinite(mature.to_numpy(dtype=float)).all()
    np.testing.assert_allclose(
        mature["macd_hist"], mature["macd"] - mature["macd_signal"], atol=1e-12
    )
    assert module.get_signal(calculated) in {None, "BUY", "SELL"}
    short = module.calculate_macd(source.head(2))
    assert short[["macd", "macd_signal", "macd_hist"]].isna().all().all()


def test_backtesting_bokeh_plot_with_synthetic_data(offline, tmp_path):
    from backtesting import Backtest
    from bokeh.resources import INLINE

    # The repository module installs a broad warning filter on import. Keep that
    # local to this test rather than changing warning behavior for later tests.
    with warnings.catch_warnings():
        from Backtesting.backtest import EMACrossover

    steps = np.arange(160, dtype=float)
    close = 100 + steps * 0.05 + 5 * np.sin(steps / 5)
    prices = pd.DataFrame(
        {"Open": close, "High": close + 1, "Low": close - 1,
         "Close": close, "Volume": np.full(len(steps), 1000)},
        index=pd.date_range("2026-01-01", periods=len(steps), freq="h"),
    )
    backtest = Backtest(prices, EMACrossover, cash=10000, commission=0.001,
                        exclusive_orders=True, finalize_trades=True)
    result = backtest.run()
    assert np.isfinite(result["Equity Final [$]"])
    assert result["# Trades"] > 0
    output = tmp_path / "dependency-backtest.html"
    # Backtesting emits Bokeh HTML without opening a browser or requesting data.
    plot = backtest.plot(filename=str(output), open_browser=False, resample=False)
    assert output.is_file()
    assert "Bokeh" in output.read_text(encoding="utf-8")
    from bokeh.embed import file_html
    inline = tmp_path / "dependency-backtest-inline.html"
    inline.write_text(file_html(plot, INLINE, "Offline dependency smoke"), encoding="utf-8")
    assert inline.stat().st_size > 1000


def test_pillow_png_round_trip_and_bokeh_image(offline, tmp_path):
    from bokeh.embed import file_html
    from bokeh.plotting import figure
    from bokeh.resources import INLINE
    from PIL import Image

    output = tmp_path / "synthetic.png"
    with Image.new("RGBA", (8, 8), (10, 20, 30, 255)) as image:
        image.save(output, format="PNG")
    with Image.open(output) as image:
        image.load()
        assert image.size == (8, 8)
        assert image.getpixel((0, 0)) == (10, 20, 30, 255)
        rgba = np.array(image.convert("RGBA"), dtype=np.uint8)
    packed = np.ascontiguousarray(rgba).view(np.uint32).reshape(8, 8)
    plot = figure(width=200, height=200)
    plot.image_rgba(image=[packed], x=0, y=0, dw=8, dh=8)
    html = file_html(plot, INLINE, "Synthetic Pillow image")
    (tmp_path / "synthetic-image.html").write_text(html, encoding="utf-8")
    assert "ImageRGBA" in html
