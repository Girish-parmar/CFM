"""Tests for cfmat.research: screener and segment analysis."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data, strategies
from cfmat.research import screener as sc
from cfmat.research import segments as sg


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


@pytest.fixture(scope="module")
def market():
    return data.seasonal_prices(3000, seed=1)


def test_calendar_labels_describe_the_next_session():
    idx = pd.bdate_range("2026-01-01", periods=60)
    same = sg.calendar_segments(idx, next_session=False)
    nxt = sg.calendar_segments(idx, next_session=True)
    assert same["weekday"].iloc[0] == "Thu" and nxt["weekday"].iloc[0] == "Fri"
    assert nxt["weekday"].iloc[:-1].tolist() == same["weekday"].iloc[1:].tolist()
    per_month = same.groupby(idx.to_period("M"))["turn_of_month"].sum()
    assert (per_month == 4).all()          # last 1 + first 3 trading days


def test_expiry_week_flags_the_week_ending_on_expiry():
    idx = pd.bdate_range("2026-03-01", "2026-04-30")
    flags = sg.expiry_week(idx, weekday=3, next_session=False)   # Thursday expiry
    assert flags[pd.Timestamp("2026-03-26")] and flags[pd.Timestamp("2026-03-20")]
    assert not flags[pd.Timestamp("2026-03-19")] and not flags[pd.Timestamp("2026-03-27")]
    assert flags[pd.Timestamp("2026-04-30")]


def test_regime_and_pattern_labels_are_causal(market):
    part = market.iloc[:2000]
    pd.testing.assert_series_equal(sg.volatility_regime(market["close"]).iloc[:2000], sg.volatility_regime(part["close"]))
    pd.testing.assert_series_equal(sg.trend_regime(market["close"]).iloc[:2000], sg.trend_regime(part["close"]))
    pd.testing.assert_frame_equal(sg.pattern_segments(market).iloc[:2000], sg.pattern_segments(part))
    assert set(sg.volatility_regime(market["close"]).dropna().unique()) == {"low", "mid", "high"}


def test_pattern_flags_on_a_hand_made_series():
    idx = pd.bdate_range("2026-01-01", periods=8)
    close = pd.Series([100, 101, 100, 99, 98, 99, 100, 101], index=idx, dtype=float)
    bars = pd.DataFrame({"close": close, "high": close + 1, "low": close - 1})
    bars.loc[idx[6], ["high", "low"]] = [99.5, 98.5]   # inside yesterday's 98–100 range
    pats = sg.pattern_segments(bars, streak=3)
    assert pats["down_streak"].tolist() == [False, False, False, False, True, False, False, False]
    assert pats["up_streak"].iloc[7] and pats["inside_day"].iloc[6]


def test_benjamini_hochberg_matches_reference():
    p = pd.Series([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    expected = [0.01, 0.04, 0.084, 0.084, 0.084, 0.1, 0.10571, 0.216, 0.216, 0.216]
    np.testing.assert_allclose(sg.benjamini_hochberg(p), expected, atol=1e-4)


def test_segment_stats_find_planted_effects_and_control_decoys(market):
    r = market["close"].pct_change()
    cal = sg.calendar_segments(market.index)
    table = sg.segment_stats(r, cal[["weekday", "month", "turn_of_month"]].shift(1))
    significant = set(zip(table.loc[table["q_value"] < 0.1, "family"], table.loc[table["q_value"] < 0.1, "segment"]))
    assert ("weekday", "Fri") in significant and ("turn_of_month", "True") in significant
    assert not any(family == "month" for family, _ in significant)   # no month effect was planted


def test_per_segment_best_recovers_regime_dependent_direction(market):
    vr = sg.volatility_regime(market["close"])
    grid = {"lookback": [1], "direction": [1, -1]}
    _, best = sg.per_segment_best(market["close"], strategies.short_term_signal, grid, vr, slice(300, 3000))
    assert best["low"]["direction"] == 1 and best["high"]["direction"] == -1


def test_walk_forward_by_segment_is_out_of_sample(market):
    vr = sg.volatility_regime(market["close"])
    g, s, chosen = sg.walk_forward_by_segment(market["close"], strategies.short_term_signal,
                                              {"lookback": [1, 2], "direction": [1, -1]}, vr, train=1000, test=500)
    assert g.index.equals(s.index) and g.index[0] == market.index[1000]
    assert len(chosen) == 4


def test_segment_filter_positions_are_long_flat_and_causal(market):
    r = market["close"].pct_change()
    labels = sg.calendar_segments(market.index)[["weekday", "turn_of_month"]]
    pos, avoided = sg.segment_filter_positions(r, labels, train=1000, test=500)
    assert pos.iloc[:1000].isna().all() and set(pos.dropna().unique()) <= {0.0, 1.0}
    shocked = r.copy()
    shocked.iloc[2600:] = -0.05
    pos2, _ = sg.segment_filter_positions(shocked, labels, train=1000, test=500)
    pd.testing.assert_series_equal(pos.iloc[:2500], pos2.iloc[:2500])
    assert len(avoided) == 4


def test_segment_features_are_numeric_with_family_prefixes(market):
    feats = sg.segment_features(market)
    assert all(c.split("_")[0] in {"cal", "reg", "pat"} for c in feats.columns)
    assert all(np.issubdtype(t, np.number) for t in feats.dtypes)
    part = sg.segment_features(market.iloc[:2000])
    cols = [c for c in feats.columns if not c.startswith("cal_")]
    pd.testing.assert_frame_equal(feats[cols].iloc[:2000], part[cols])
