"""Tests for cfmat.data: synthetic generators."""

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
