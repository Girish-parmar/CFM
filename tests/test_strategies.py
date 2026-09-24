"""Tests for cfmat.strategies: classic signal functions."""

import numpy as np
import pytest

from cfmat import data, strategies
from cfmat.backtesting import vectorized as bt


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
