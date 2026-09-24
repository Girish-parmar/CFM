"""Tests for cfmat.backtesting: vectorised and event-driven engines."""

import pandas as pd
import pytest

from cfmat import data, strategies
from cfmat.backtesting import vectorized as bt
from cfmat.backtesting.event_driven import SmaCrossStrategy, run_event_backtest


def test_backtest_shifts_positions_no_lookahead():
    close = pd.Series([100, 110, 99, 120], dtype=float)
    # A "perfect foresight" signal known at t cannot earn t's return.
    signal = pd.Series([1, 0, 1, 0], dtype=float)
    res = bt.vectorized_backtest(close, signal)
    assert res["position"].tolist() == [0, 1, 0, 1]
    assert res["strategy_return"].iloc[1] == pytest.approx(0.10)


def test_costs_reduce_returns_by_turnover():
    close = data.gbm_prices(300, seed=2)
    sig = strategies.sma_crossover(close, 10, 30)
    gross = bt.vectorized_backtest(close, sig, 0)
    net = bt.vectorized_backtest(close, sig, 10)
    diff = gross["strategy_return"].sum() - net["strategy_return"].sum()
    assert diff == pytest.approx(net["turnover"].sum() * 10 / 1e4)


def test_walk_forward_returns_only_out_of_sample():
    close = data.gbm_prices(1000, seed=9)
    grid = {"fast": [10, 20], "slow": [50, 100]}
    oos, chosen = bt.walk_forward(close, strategies.sma_crossover, grid, train=500, test=100)
    assert oos.index.min() == close.index[500]
    assert len(oos) == 500 and len(chosen) == 5


def test_event_engine_matches_expectations():
    bars = data.ohlcv(300, seed=6)
    table, broker = run_event_backtest(bars, SmaCrossStrategy(10, 30, qty=50), cash=100_000)
    assert set(table["position"].unique()) <= {0, 50}
    assert len(broker.fills) > 0
    # Fills happen at the open of the bar after the signal.
    first = broker.fills[0]
    assert first.price == pytest.approx(bars.loc[first.timestamp, "open"] * (1 + 2 / 1e4))
    assert table["equity"].iloc[-1] == pytest.approx(broker.equity())


def test_pairs_costs_use_the_price_the_trade_was_made_at():
    idx = pd.bdate_range("2025-01-01", periods=4)
    y = pd.Series([100.0, 200.0, 200.0, 200.0], index=idx)
    x = pd.Series([50.0, 50.0, 50.0, 50.0], index=idx)
    legs = pd.DataFrame({"y": [1.0, 1.0, 1.0, 1.0], "x": [0.0, 0.0, 0.0, 0.0], "beta": [0.0] * 4}, index=idx)
    out = bt.pairs_backtest(y, x, legs, capital=1_000.0, cost_bps=100)
    # 10 shares of y were bought at the first close (₹100), so the cost is 1% of ₹1,000, not of ₹2,000
    assert out["shares_y"].iloc[1] == 10 and out["cost"].iloc[1] == pytest.approx(10.0)
    assert out["pnl"].iloc[1] == pytest.approx(1_000.0)
