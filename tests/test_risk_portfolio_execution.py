import numpy as np
import pytest

from cfmat import data, execution, portfolio, risk
from cfmat.metrics import simple_returns


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


def test_order_book_price_time_priority():
    book = execution.OrderBook()
    first, _ = book.add_limit("SELL", 101.0, 30)
    second, _ = book.add_limit("SELL", 101.0, 30)
    book.add_limit("SELL", 102.0, 50)
    book.add_limit("BUY", 99.0, 40)
    assert book.spread() == pytest.approx(2.0)
    trades = book.add_market("BUY", 45)
    assert [(t["maker_id"], t["qty"]) for t in trades] == [(first, 30), (second, 15)]
    assert book.cancel(second) and book.best_ask() == 102.0
    _, crossed = book.add_limit("SELL", 98.0, 60)  # sweeps the 99 bid, rests at 98
    assert crossed[0]["price"] == 99.0 and book.best_ask() == 98.0


def test_schedules_sum_exactly():
    assert execution.twap_schedule(1003, 10).sum() == 1003
    v = execution.vwap_schedule(50_000, data.intraday_volume_profile())
    assert v.sum() == 50_000 and v[0] > v[12]


def test_almgren_chriss_limits():
    twap = execution.almgren_chriss_trajectory(1e6, 1.0, 10, 0.95, 2.5e-6, risk_aversion=0)
    urgent = execution.almgren_chriss_trajectory(1e6, 1.0, 10, 0.95, 2.5e-6, risk_aversion=1e-5)
    assert twap[0] == urgent[0] == 1e6 and abs(urgent[-1]) < 1e-6
    assert urgent[1] < twap[1]  # risk-averse trader sells faster early
    c_twap = execution.almgren_chriss_cost(twap, 1.0, 0.95, 2.5e-6)
    c_urgent = execution.almgren_chriss_cost(urgent, 1.0, 0.95, 2.5e-6)
    assert c_urgent["expected_cost"] > c_twap["expected_cost"] and c_urgent["variance"] < c_twap["variance"]


def test_implementation_shortfall():
    res = execution.implementation_shortfall("BUY", 100.0, [(600, 100.5), (200, 101.0)], 1000, 102.0)
    assert res["avg_price"] == pytest.approx(100.625)
    assert res["execution_cost"] == pytest.approx(500.0)
    assert res["opportunity_cost"] == pytest.approx(400.0)
    assert res["total_bps"] == pytest.approx(90.0)
