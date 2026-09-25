"""Tests for cfmat.data: synthetic generators."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat.analytics import metrics


def test_regime_generator_labels_states():
    m = data.regime_prices(3000, seed=1)
    calm = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 0]
    wild = metrics.simple_returns(m["close"])[m["regime"].iloc[1:] == 1]
    assert wild.std() > 2 * calm.std()


def test_gbm_is_reproducible_and_positive():
    a = data.gbm_prices(500, seed=7)
    b = data.gbm_prices(500, seed=7)
    pd.testing.assert_series_equal(a, b)
    assert (a > 0).all() and len(a) == 500 and a.iloc[0] == 100.0


def test_gbm_volatility_is_close_to_input():
    close = data.gbm_prices(5000, sigma=0.25, seed=1)
    vol = metrics.annualized_volatility(metrics.log_returns(close))
    assert vol == pytest.approx(0.25, rel=0.05)


def test_ohlcv_bars_are_consistent():
    bars = data.ohlcv(300, seed=3)
    assert (bars["high"] >= bars[["open", "close"]].max(axis=1)).all()
    assert (bars["low"] <= bars[["open", "close"]].min(axis=1)).all()
    assert (bars["volume"] > 0).all()


def test_volume_profile_sums_to_one_and_is_u_shaped():
    p = data.intraday_volume_profile(25)
    assert p.sum() == pytest.approx(1.0)
    assert p[0] > p[12] < p[-1]


def test_universe_can_draw_a_volatility_per_stock():
    def vol_ratio(prices):
        vol = np.log(prices).diff().std() * np.sqrt(252)
        return vol.max() / vol.min()

    assert vol_ratio(data.universe(20, 1000, idio_vol=(0.10, 0.50), seed=1)) > 2.0
    assert vol_ratio(data.universe(20, 1000, idio_vol=0.20, seed=1)) < 1.6


def test_brownian_ohlc_is_consistent_and_carries_the_true_volatility():
    sigma = np.r_[np.full(50, 0.1), np.full(50, 0.4)]
    bars = data.brownian_ohlc(100, sigma=sigma, seed=7)
    assert (bars["high"] >= bars[["open", "close"]].max(axis=1)).all()
    assert (bars["low"] <= bars[["open", "close"]].min(axis=1)).all()
    assert bars["true_vol"].tolist() == sigma.tolist()
    no_gaps = data.brownian_ohlc(100, overnight_share=0.0, seed=7)
    assert np.allclose(no_gaps["open"].iloc[1:].to_numpy(), no_gaps["close"].iloc[:-1].to_numpy())
    assert not np.allclose(bars["open"].iloc[1:].to_numpy(), bars["close"].iloc[:-1].to_numpy())
    with pytest.raises(ValueError):
        data.brownian_ohlc(10, overnight_share=1.0)
