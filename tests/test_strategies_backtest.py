import numpy as np
import pandas as pd
import pytest

from cfmat import backtest as bt
from cfmat import data, indicators, strategies
from cfmat.engine import SmaCrossStrategy, run_event_backtest


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


def test_rsi_bounds_and_all_gain_series():
    close = data.gbm_prices(400, seed=4)
    r = indicators.rsi(close).dropna()
    assert r.between(0, 100).all()
    rising = pd.Series(np.arange(1, 50, dtype=float))
    assert indicators.rsi(rising).dropna().eq(100).all()


def test_sma_crossover_validates_windows():
    with pytest.raises(ValueError):
        strategies.sma_crossover(data.gbm_prices(100, seed=1), 50, 20)


def test_pairs_strategy_profits_on_cointegrated_pair():
    pair = data.cointegrated_pair(1000, seed=11)
    legs = strategies.pairs_signals(pair["y"], pair["x"], formation=250, window=30)
    assert legs["beta"].iloc[0] == pytest.approx(1.5, abs=0.15)
    assert (legs[["y", "x"]].iloc[:250] == 0).all().all()  # no trading in formation
    res = bt.pairs_backtest(pair["y"], pair["x"], legs, capital=1_000_000, cost_bps=2)
    assert res["net_pnl"].sum() > 0


def test_cross_sectional_momentum_weights_sum_to_one():
    prices = data.universe(8, 400, seed=3)
    w = strategies.cross_sectional_momentum(prices, lookback=126, skip=21, top_n=3)
    live = w.iloc[200:]
    assert np.allclose(live.sum(axis=1), 1.0)
    assert ((live > 0).sum(axis=1) == 3).all()


def test_indian_cost_model_components():
    model = bt.IndianCostModel()
    buy = model.charges("buy", 100, 1000, "equity_delivery")
    sell = model.charges("sell", 100, 1000, "equity_delivery")
    assert buy["stt"] == pytest.approx(100) and sell["stt"] == pytest.approx(100)
    assert buy["stamp"] == pytest.approx(15) and sell["stamp"] == 0
    assert buy["brokerage"] == 0
    intraday = model.charges("buy", 1000, 2000, "equity_intraday")
    assert intraday["brokerage"] == 20  # capped at ₹20
    assert 0 < model.round_trip_bps(1000, 2000, "equity_intraday") < 10


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
