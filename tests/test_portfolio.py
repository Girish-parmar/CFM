"""Tests for cfmat.portfolio: risk and construction."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data, portfolio
from cfmat.analytics.metrics import simple_returns
from cfmat.portfolio import risk


@pytest.mark.parametrize("method", ["equal", "inverse_vol", "risk_parity", "hrp"])
def test_rolling_allocation_uses_only_past_data(method):
    from cfmat import portfolio

    rng = np.random.default_rng(0)
    rets = pd.DataFrame(rng.normal(0, [0.01, 0.02, 0.005], size=(400, 3)), columns=list("abc"))
    w = portfolio.rolling_allocation(rets, method=method, lookback=100, rebalance=20)
    assert (w.iloc[:99] == 0).all().all()
    assert np.allclose(w.iloc[99:].sum(axis=1), 1.0)
    # changing future returns must not change today's weights
    shocked = rets.copy()
    shocked.iloc[300:] *= 5
    w2 = portfolio.rolling_allocation(shocked, method=method, lookback=100, rebalance=20)
    pd.testing.assert_frame_equal(w.iloc[:300], w2.iloc[:300], check_exact=False, rtol=1e-6, atol=1e-9)
    if method == "inverse_vol":
        assert w.iloc[-1]["c"] > w.iloc[-1]["a"] > w.iloc[-1]["b"]
    combined = portfolio.allocation_returns(rets, w)
    assert combined.iloc[:100].abs().sum() == 0


@pytest.fixture(scope="module")
def rets():
    return simple_returns(data.universe(6, 800, seed=21))


def test_var_ordering_and_es(rets):
    r = rets.mean(axis=1)
    var99 = risk.historical_var(r, 0.99)
    var95 = risk.historical_var(r, 0.95)
    assert var99 > var95 > 0
    assert risk.expected_shortfall(r, 0.99) >= var99
    assert risk.parametric_var(r, 0.99) == pytest.approx(var99, rel=0.35)


def test_position_sizing():
    assert risk.fixed_fractional_qty(1_000_000, 0.01, 500, 480) == 500
    assert risk.fixed_fractional_qty(1_000_000, 0.01, 500, 480, lot_size=75) == 450


def test_optimisers_are_valid(rets):
    mu, cov = rets.mean() * 252, rets.cov() * 252
    for w in (portfolio.min_variance_weights(cov), portfolio.max_sharpe_weights(mu, cov),
              portfolio.risk_parity_weights(cov), portfolio.hrp_weights(rets)):
        assert w.sum() == pytest.approx(1.0, abs=1e-6)
        assert (w >= -1e-8).all()
    rp = portfolio.risk_parity_weights(cov)
    assert np.allclose(portfolio.risk_contributions(rp, cov), 1 / 6, atol=1e-3)
    mv = portfolio.min_variance_weights(cov)
    eq = np.full(6, 1 / 6)
    assert portfolio.portfolio_stats(mv, mu, cov)["volatility"] <= portfolio.portfolio_stats(eq, mu, cov)["volatility"]
