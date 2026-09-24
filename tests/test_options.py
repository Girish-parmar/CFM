import numpy as np
import pytest

from cfmat import options as opt


def test_black_scholes_textbook_values():
    # Hull: S=K=100, T=1, r=5%, sigma=20% -> call 10.4506, put 5.5735
    assert opt.bs_price(100, 100, 1, 0.05, 0.2, "call") == pytest.approx(10.4506, abs=1e-4)
    assert opt.bs_price(100, 100, 1, 0.05, 0.2, "put") == pytest.approx(5.5735, abs=1e-4)


def test_put_call_parity_holds_with_dividends():
    c = opt.bs_price(24500, 24000, 30 / 365, 0.065, 0.14, "call", q=0.012)
    p = opt.bs_price(24500, 24000, 30 / 365, 0.065, 0.14, "put", q=0.012)
    assert opt.put_call_parity_gap(c, p, 24500, 24000, 30 / 365, 0.065, q=0.012) == pytest.approx(0, abs=1e-8)


def test_implied_vol_round_trip():
    price = opt.bs_price(100, 110, 0.5, 0.06, 0.31, "put")
    assert opt.implied_volatility(price, 100, 110, 0.5, 0.06, "put") == pytest.approx(0.31, abs=1e-6)


def test_implied_vol_rejects_arbitrage_price():
    with pytest.raises(ValueError):
        opt.implied_volatility(0.0001, 150, 100, 1, 0.05, "call")


def test_greeks_match_finite_differences():
    S, K, T, r, s = 100, 105, 0.75, 0.04, 0.25
    g = opt.bs_greeks(S, K, T, r, s, "call")
    h = 1e-3
    delta = (opt.bs_price(S + h, K, T, r, s) - opt.bs_price(S - h, K, T, r, s)) / (2 * h)
    gamma = (opt.bs_price(S + h, K, T, r, s) - 2 * opt.bs_price(S, K, T, r, s) + opt.bs_price(S - h, K, T, r, s)) / h**2
    vega = (opt.bs_price(S, K, T, r, s + 0.01) - opt.bs_price(S, K, T, r, s - 0.01)) / 2
    theta = opt.bs_price(S, K, T - 1 / 365, r, s) - opt.bs_price(S, K, T, r, s)
    assert g.delta == pytest.approx(delta, rel=1e-5)
    assert g.gamma == pytest.approx(gamma, rel=1e-3)
    assert g.vega == pytest.approx(vega, rel=1e-3)
    assert g.theta == pytest.approx(theta, rel=2e-2)


def test_binomial_converges_to_black_scholes():
    bs = opt.bs_price(100, 100, 1, 0.05, 0.2, "call")
    assert opt.binomial_price(100, 100, 1, 0.05, 0.2, "call", steps=1000) == pytest.approx(bs, abs=0.01)


def test_american_put_worth_at_least_european():
    eu = opt.binomial_price(100, 110, 1, 0.08, 0.2, "put", steps=500)
    am = opt.binomial_price(100, 110, 1, 0.08, 0.2, "put", steps=500, american=True)
    assert am > eu


def test_straddle_payoff_shape():
    legs = [{"kind": "call", "strike": 100, "qty": 1, "premium": 5},
            {"kind": "put", "strike": 100, "qty": 1, "premium": 4}]
    pnl = opt.strategy_payoff(legs, np.array([80, 100, 120]), lot_size=75)
    assert list(pnl) == [11 * 75, -9 * 75, 11 * 75]


def test_futures_fair_value():
    assert opt.futures_fair_value(100, 1, 0.05) == pytest.approx(100 * np.exp(0.05))
