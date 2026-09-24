"""Tests for cfmat.viz: every chart renders from course data and draws what it promises."""

from datetime import datetime

import pandas as pd
import pytest

from cfmat import data, trading, viz
from cfmat.analytics import indicators, momentum, patterns, relative, volatility
from cfmat.infra.plotting import plt


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture(scope="module")
def bars():
    return data.ohlcv(300, seed=11)


@pytest.fixture(scope="module")
def returns():
    prices = data.universe(5, 600, seed=3)
    return prices.pct_change().dropna()


def _labels(ax):
    return set(ax.get_legend_handles_labels()[1])


def test_price_chart_draws_overlays_trades_markers_volume_and_panels(bars):
    trips = pd.DataFrame({"entry_time": [bars.index[250]], "entry_price": [bars["close"].iloc[250]],
                          "exit_time": [bars.index[270]], "exit_price": [bars["close"].iloc[270]],
                          "direction": ["LONG"], "net_pnl": [10.0]})
    fig = viz.price_chart(bars, overlays={"SMA 20": indicators.sma(bars["close"], 20),
                                          "Bollinger": indicators.bollinger_bands(bars["close"])},
                          trades=trips, markers={"inside bar": patterns.inside_bar(bars)},
                          panels={"RSI 14": indicators.rsi(bars["close"])}, last=120, title="test")
    price_ax = fig.axes[0]
    assert len(fig.axes) == 3                                      # price, volume, RSI
    assert {"SMA 20", "long entry", "exit", "inside bar"} <= _labels(price_ax)
    assert len(price_ax.patches) == 120                           # one candle body per bar
    assert fig.axes[-1].get_xticklabels()[0].get_text() != ""        # dates on the bottom panel


def test_price_chart_switches_to_a_line_for_long_histories(bars):
    fig = viz.price_chart(bars, volume=False)
    assert len(fig.axes) == 1 and len(fig.axes[0].patches) == 0 and "close" in _labels(fig.axes[0])


def test_performance_charts(returns):
    r, b = returns.iloc[:, 0], returns.iloc[:, 1]
    fig = viz.equity_chart(r, benchmark=b)
    assert {"strategy", "benchmark"} <= _labels(fig.axes[0])
    assert any(t.startswith("worst drawdown") for t in _labels(fig.axes[0]))
    heat = viz.monthly_heatmap(r)
    assert len(heat.axes[0].texts) >= 12
    assert len(viz.rolling_chart(r, 63, benchmark=b).axes) == 4
    dist = viz.distribution_chart(r)
    assert any("VaR" in t for t in _labels(dist.axes[0]))


def test_trade_chart_from_journal_round_trips():
    journal = trading.TradeJournal()
    t0 = datetime(2026, 1, 5, 9, 15)
    for i, (side, price) in enumerate([("BUY", 100), ("SELL", 104), ("SELL", 105), ("BUY", 107)]):
        journal.record(trading.Fill(i + 1, "ABC", side, 10, price, t0 + pd.Timedelta(minutes=10 * i), 0.0),
                       stop=98 if i == 0 else 106)
    fig = viz.trade_chart(journal.round_trips())
    assert len(fig.axes) == 4 and len(fig.axes[0].patches) == 2


def test_analysis_charts(returns):
    prices = (1 + returns).cumprod()
    fig = viz.correlation_heatmap(returns)
    assert len(fig.axes[0].texts) == 25
    bars = data.brownian_ohlc(300, seed=1)
    vol_fig = viz.volatility_chart(bars, 21, true_vol=bars["true_vol"])
    assert "true" in _labels(vol_fig.axes[0]) and "yang-zhang" in _labels(vol_fig.axes[0])
    cone = volatility.volatility_cone(bars["close"], windows=(10, 21, 63))
    assert "current" in _labels(viz.cone_chart(cone).axes[0])
    scores = momentum.momentum(prices, 126, 21).iloc[-1]
    assert len(viz.ranking_chart(scores).axes[0].patches) == 5
    bench = prices.mean(axis=1)
    ratio, mom = relative.relative_rotation(prices, bench, window=63, momentum_window=5)
    rrg = viz.rotation_chart(ratio, mom, tail=6)
    assert {t.get_text() for t in rrg.axes[0].texts} >= {"Leading", "Lagging", *prices.columns}
    frontier = viz.frontier_chart(returns)
    assert any(t.startswith("max Sharpe") for t in _labels(frontier.axes[0]))


def test_savefig_writes_png(tmp_path, monkeypatch, returns):
    monkeypatch.setenv("CFMAT_OUTPUT_DIR", str(tmp_path))
    path = viz.savefig(viz.equity_chart(returns.iloc[:, 0]), "equity")
    assert path.exists() and path.stat().st_size > 10_000
