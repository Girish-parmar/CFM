"""Tests for cfmat.derivatives: option pricing, futures and option-structure backtests."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat.derivatives import futures as fu
from cfmat.derivatives import option_strategies
from cfmat.derivatives import options as opt
from cfmat.microstructure.costs import IndianCostModel, SegmentRates

FREE = IndianCostModel(segments={k: SegmentRates(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                                 for k in ("equity_delivery", "equity_intraday", "futures", "options")},
                       sebi_fee=0.0, gst=0.0)


def test_monthly_and_weekly_expiries():
    idx = pd.bdate_range("2026-01-01", "2026-03-31").drop(pd.Timestamp("2026-02-26"))   # a holiday on expiry Thursday
    monthly = fu.monthly_expiries(idx, weekday=3)
    assert list(monthly) == [pd.Timestamp("2026-01-29"), pd.Timestamp("2026-02-25"), pd.Timestamp("2026-03-26")]
    weekly = fu.weekly_expiries(idx, weekday=1)
    assert all(d.weekday() == 1 for d in weekly[1:]) and len(weekly) == len(set(idx.to_period("W-SUN")))


def test_futures_curve_converges_and_carries():
    spot = data.gbm_prices(400, s0=20000, seed=1)
    curve = fu.futures_curve(spot, r=0.07, q=0.01, basis_noise_bps=0.0, seed=0)
    exp = curve[curve["is_expiry"]]
    assert np.allclose(exp["near"], exp["spot"])
    assert (curve.loc[~curve["is_expiry"], "near"] > curve.loc[~curve["is_expiry"], "spot"]).all()
    assert (curve["next"] > curve["near"]).all()


def test_futures_backtest_pnl_rolls_and_margin():
    spot = data.gbm_prices(300, s0=20000, seed=2)
    curve = fu.futures_curve(spot, basis_noise_bps=0.0, seed=0)
    lots = pd.Series(2, index=curve.index)
    daily, summary = fu.backtest_futures(curve, lots, lot_size=50, capital=5_000_000, cost_model=FREE, slippage_bps=0)
    assert summary["rolls"] == int(curve["is_expiry"].iloc[:-1].sum() + curve["is_expiry"].iloc[-1])
    first_exp = curve.index[curve["is_expiry"]][0]
    pre = curve.loc[:first_exp]
    assert daily.loc[:first_exp, "pnl"].sum() == pytest.approx(2 * 50 * (pre["near"].iloc[-1] - pre["near"].iloc[0]))
    assert daily["margin"].iloc[5] == pytest.approx(2 * 50 * curve["near"].iloc[5] * 0.12)
    assert fu.lots_for_capital(1_000_000, 20000, 50, 0.12, max_margin_use=0.5) == 4


def test_basis_trade_captures_mispricing_before_costs():
    spot = data.gbm_prices(800, s0=20000, seed=3)
    curve = fu.futures_curve(spot, basis_noise_bps=15.0, seed=4)
    daily, trades = fu.basis_trade(curve, entry_bps=15, exit_bps=3, cost_model=FREE)
    assert len(trades) > 5 and trades["pnl"].sum() > 0
    assert daily["pnl"].sum() == pytest.approx(trades["pnl"].sum())
    _, costly = fu.basis_trade(curve, entry_bps=15, exit_bps=3)
    assert costly["pnl"].sum() < trades["pnl"].sum()


def test_short_straddle_held_to_expiry_matches_hand_calculation():
    idx = pd.bdate_range("2026-01-05", periods=10)
    spot = pd.Series(np.linspace(20000, 20400, 10), index=idx)
    iv = pd.Series(0.15, index=idx)
    expiry = pd.DatetimeIndex([idx[-1]])
    res = option_strategies.backtest_options(spot, iv, "short_straddle", expiry, lot_size=50, strike_step=50, skew=0.0,
                              slippage_pct=0.0, cost_model=FREE)
    t = res.trades.iloc[0]
    strike = float(t["strikes"].split("/")[0])
    assert t["reason"] == "expiry" and t["entry"] == idx[0]         # first trading day of the first cycle
    assert t["pnl"] == pytest.approx(t["net_premium"] - abs(20400 - strike) * 50)


def test_defined_risk_and_undefined_risk_margins():
    legs, strikes = option_strategies.OPTION_STRATEGIES["iron_condor"], [21000, 21500, 19000, 18500]
    net = -10_000.0
    assert option_strategies._max_loss(legs, strikes, net, 50) == pytest.approx(500 * 50 - 10_000)
    straddle = option_strategies.OPTION_STRATEGIES["short_straddle"]
    assert option_strategies._max_loss(straddle, [20000, 20000], -30_000, 50) == float("inf")


def test_filters_targets_and_stops():
    m = data.regime_prices(400, seed=5)
    spot, iv = m["close"] * 240, data.implied_vol_series(m["close"] * 240, seed=1)
    exp = fu.weekly_expiries(spot.index, 1)
    none = option_strategies.backtest_options(spot, iv, "iron_condor", exp, entry_filter=pd.Series(False, index=spot.index))
    assert len(none.trades) == 0
    res = option_strategies.backtest_options(spot, iv, "short_strangle", exp, profit_take=0.3, stop_loss=1.0)
    reasons = set(res.trades["reason"])
    assert "profit target" in reasons and reasons <= {"profit target", "stop loss", "expiry"}
    assert {"delta", "gamma", "vega", "theta", "realised_pnl"} <= set(res.daily.columns)
    assert res.summary()["trades"] == len(res.trades)


def test_run_many_parallel_matches_serial():
    m = data.regime_prices(300, seed=6)
    spot, iv = m["close"] * 240, data.implied_vol_series(m["close"] * 240, seed=2)
    exp = fu.weekly_expiries(spot.index, 1)
    configs = {"condor": {"strategy": "iron_condor", "expiries": exp}, "straddle": {"strategy": "long_straddle", "expiries": exp}}
    serial = option_strategies.run_many(spot, iv, configs, workers=1)
    procs = option_strategies.run_many(spot, iv, configs, workers=2, backend="process")
    for k in configs:
        pd.testing.assert_frame_equal(serial[k].trades, procs[k].trades)


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


# -- second-order Greeks and P&L attribution (M09) -------------------------------------------------

@pytest.mark.parametrize("S,K,T,sigma", [(24000, 24500, 30 / 365, 0.16), (24000, 22000, 7 / 365, 0.25),
                                         (100, 100, 1.0, 0.30), (100, 130, 0.25, 0.40)])
@pytest.mark.parametrize("kind", ["call", "put"])
def test_second_order_greeks_match_finite_differences(S, K, T, sigma, kind):
    r, q = 0.065, 0.012
    g = opt.bs_second_order_greeks(S, K, T, r, sigma, kind, q)

    def first(**kw):
        return opt.bs_greeks(**{**dict(S=S, K=K, T=T, r=r, sigma=sigma, kind=kind, q=q), **kw})

    hs, hv, ht = S * 1e-4, 1e-4, 1e-6
    fd = {"vanna": (first(sigma=sigma + hv).delta - first(sigma=sigma - hv).delta) / (2 * hv) / 100,
          "volga": (first(sigma=sigma + hv).vega - first(sigma=sigma - hv).vega) / (2 * hv) / 100,
          "charm": -(first(T=T + ht).delta - first(T=T - ht).delta) / (2 * ht) / 365,
          "speed": (first(S=S + hs).gamma - first(S=S - hs).gamma) / (2 * hs),
          "zomma": (first(sigma=sigma + hv).gamma - first(sigma=sigma - hv).gamma) / (2 * hv) / 100,
          "color": -(first(T=T + ht).gamma - first(T=T - ht).gamma) / (2 * ht) / 365}
    for name, value in fd.items():
        assert getattr(g, name) == pytest.approx(value, rel=1e-4), name


def test_second_order_greeks_call_put_relations():
    args = (24000, 24200, 45 / 365, 0.065, 0.18)
    call = opt.bs_second_order_greeks(*args, "call", q=0.012)
    put = opt.bs_second_order_greeks(*args, "put", q=0.012)
    for name in ("vanna", "volga", "speed", "zomma", "color"):
        assert getattr(call, name) == pytest.approx(getattr(put, name))
    assert call.charm - put.charm == pytest.approx(0.012 * np.exp(-0.012 * 45 / 365) / 365)   # from put-call parity


def test_greek_attribution_explains_a_short_straddle_through_a_sell_off():
    days = pd.bdate_range("2026-03-02", periods=16)
    rng = np.random.default_rng(9)
    path = pd.DataFrame({"spot": 24000 * np.exp(np.cumsum(np.r_[0, rng.normal(-0.012, 0.006, 15)])),
                         "iv": 0.14 + np.cumsum(np.r_[0, rng.normal(0.01, 0.004, 15)])}, index=days)
    legs = [{"kind": k, "strike": 24000, "qty": -50, "expiry": "2026-04-28"} for k in ("call", "put")]
    att = opt.greek_pnl_attribution(legs, path)
    gross = att[["delta", "gamma", "vega", "theta", "vanna", "volga", "charm", "speed"]].abs().sum(axis=1)
    assert (att["residual"].abs() < 0.05 * gross).all()
    assert att["residual"].abs().sum() < 0.02 * att["actual"].abs().sum()
    assert att["actual"].sum() < 0 and att["gamma"].sum() < 0 and att["vega"].sum() < 0 and att["theta"].sum() > 0
