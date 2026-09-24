import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat import futures as fu
from cfmat import options_backtest as ob
from cfmat.backtest import IndianCostModel, SegmentRates

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
    res = ob.backtest_options(spot, iv, "short_straddle", expiry, lot_size=50, strike_step=50, skew=0.0,
                              slippage_pct=0.0, cost_model=FREE)
    t = res.trades.iloc[0]
    strike = float(t["strikes"].split("/")[0])
    assert t["reason"] == "expiry" and t["entry"] == idx[0]         # first trading day of the first cycle
    assert t["pnl"] == pytest.approx(t["net_premium"] - abs(20400 - strike) * 50)


def test_defined_risk_and_undefined_risk_margins():
    legs, strikes = ob.OPTION_STRATEGIES["iron_condor"], [21000, 21500, 19000, 18500]
    net = -10_000.0
    assert ob._max_loss(legs, strikes, net, 50) == pytest.approx(500 * 50 - 10_000)
    assert ob._max_loss(ob.OPTION_STRATEGIES["short_straddle"], [20000, 20000], -30_000, 50) == float("inf")


def test_filters_targets_and_stops():
    m = data.regime_prices(400, seed=5)
    spot, iv = m["close"] * 240, data.implied_vol_series(m["close"] * 240, seed=1)
    exp = fu.weekly_expiries(spot.index, 1)
    none = ob.backtest_options(spot, iv, "iron_condor", exp, entry_filter=pd.Series(False, index=spot.index))
    assert len(none.trades) == 0
    res = ob.backtest_options(spot, iv, "short_strangle", exp, profit_take=0.3, stop_loss=1.0)
    reasons = set(res.trades["reason"])
    assert "profit target" in reasons and reasons <= {"profit target", "stop loss", "expiry"}
    assert {"delta", "gamma", "vega", "theta", "realised_pnl"} <= set(res.daily.columns)
    assert res.summary()["trades"] == len(res.trades)


def test_run_many_parallel_matches_serial():
    m = data.regime_prices(300, seed=6)
    spot, iv = m["close"] * 240, data.implied_vol_series(m["close"] * 240, seed=2)
    exp = fu.weekly_expiries(spot.index, 1)
    configs = {"condor": {"strategy": "iron_condor", "expiries": exp}, "straddle": {"strategy": "long_straddle", "expiries": exp}}
    serial = ob.run_many(spot, iv, configs, workers=1)
    procs = ob.run_many(spot, iv, configs, workers=2, backend="process")
    for k in configs:
        pd.testing.assert_frame_equal(serial[k].trades, procs[k].trades)
