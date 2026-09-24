import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat import screener as sc


@pytest.fixture(scope="module")
def uni():
    return data.instrument_universe(30, seed=4)


def test_trend_fit_on_an_exact_exponential():
    idx = pd.bdate_range("2024-01-01", periods=300)
    close = pd.Series(100 * np.exp(0.001 * np.arange(300)), index=idx)
    slope, r2 = sc.trend_fit(close, 250)
    assert slope == pytest.approx(np.exp(0.252) - 1) and r2 == pytest.approx(1.0)


def test_instrument_metrics_values(uni):
    universe, _ = uni
    bars = next(iter(universe.values()))
    m = sc.instrument_metrics(bars)
    assert m["ret_1m"] == pytest.approx(bars["close"].iloc[-1] / bars["close"].iloc[-22] - 1)
    assert m["turnover_cr"] == pytest.approx((bars["close"] * bars["volume"]).iloc[-20:].mean() / 1e7)
    assert 0 <= m["bb_width_pctile"] <= 1 and 0 <= m["er_60"] <= 1 and m["max_dd_1y"] <= 0


def test_screen_parallel_matches_serial_and_classifies_most(uni):
    universe, meta = uni
    serial = sc.screen(universe, workers=1)
    parallel = sc.screen(universe, workers=2, backend="process")
    pd.testing.assert_frame_equal(serial, parallel)
    truth = {"uptrend": "trending_up", "downtrend": "trending_down", "range": "range_bound",
             "squeeze": "squeeze", "volatile": "volatile"}
    assert (meta["archetype"].map(truth) == serial["regime"]).mean() > 0.6
    assert {"beta_1y", "corr_1y", "suggested"} <= set(serial.columns)


def test_filters_rank_and_diversify(uni):
    universe, meta = uni
    table = sc.screen(universe)
    liquid = sc.apply_filters(table, ["liquid", "close > 100"])
    assert (liquid["turnover_cr"] >= 5).all() and (liquid["close"] > 100).all()
    ranked = sc.rank(table, {"ret_6m": 1.0, "vol_60": -0.5})
    assert ranked["score"].is_monotonic_decreasing
    rets = pd.DataFrame({s: b["close"].pct_change() for s, b in universe.items()})
    picks = sc.diversify(rets, ranked.index, n=6, max_corr=0.3)
    corr = rets[picks].iloc[-252:].corr().abs().to_numpy()
    assert len(picks) <= 6 and (corr[~np.eye(len(picks), dtype=bool)] < 0.3).all()


def test_classify_rules():
    base = {"bb_width_pctile": 0.5, "adx": 25, "vol_20": 0.2, "trend_r2_1y": 0.8, "trend_slope_1y": 0.4,
            "close": 110, "sma_50": 100, "er_60": 0.4}
    assert sc.classify(pd.Series(base)) == "trending_up"
    assert sc.classify(pd.Series({**base, "trend_slope_1y": -0.4, "close": 90})) == "trending_down"
    assert sc.classify(pd.Series({**base, "bb_width_pctile": 0.05})) == "squeeze"
    assert sc.classify(pd.Series({**base, "vol_20": 0.6})) == "volatile"
    assert sc.classify(pd.Series({**base, "trend_r2_1y": 0.1, "er_60": 0.1})) == "range_bound"


def test_pattern_scan_lists_only_instruments_with_hits(uni):
    universe, _ = uni
    hits = sc.pattern_scan(universe, ["inside_bar", "doji", "outside_bar"], lookback=5)
    assert hits.any(axis=1).all() and set(hits.columns) == {"inside_bar", "doji", "outside_bar"}
