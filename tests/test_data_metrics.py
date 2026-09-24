import numpy as np
import pandas as pd
import pytest

from cfmat import data, metrics


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


def test_max_drawdown_known_path():
    equity = pd.Series([100, 120, 90, 130, 65, 140], dtype=float)
    assert metrics.max_drawdown(equity) == pytest.approx(-0.5)


def test_sharpe_and_cagr_on_constant_returns():
    r = pd.Series([0.001] * 252)
    assert metrics.cagr(r) == pytest.approx(1.001**252 - 1)
    assert metrics.sharpe_ratio(r) == 0.0  # zero volatility guard


def test_performance_summary_fields():
    r = metrics.simple_returns(data.gbm_prices(756, seed=5))
    s = metrics.performance_summary(r)
    for key in ("cagr", "sharpe", "max_drawdown", "sortino", "calmar"):
        assert key in s.index
    assert s["max_drawdown"] <= 0


def test_deflated_sharpe_penalises_many_trials():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.0008, 0.01, 1000))
    psr = metrics.probabilistic_sharpe_ratio(r)
    dsr = metrics.deflated_sharpe_ratio(r, n_trials=200, sr_variance=0.002)
    assert 0 <= dsr < psr <= 1
