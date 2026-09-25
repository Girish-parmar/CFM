"""Tests for cfmat.analytics: metrics, indicators, patterns, stats, factors, momentum, volatility,
relative and performance analysis."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data
from cfmat.analytics import factors, metrics, stats
from cfmat.analytics import indicators as ind
from cfmat.analytics import patterns as pt


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


def candles(rows):
    idx = pd.bdate_range("2026-01-01", periods=len(rows))
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)


def falling(n=6, start=110.0):
    return [[start - i, start - i + 0.5, start - i - 1.5, start - i - 1.0] for i in range(n)]


def test_adx_and_di_on_a_clean_uptrend():
    idx = pd.bdate_range("2026-01-01", periods=120)
    close = pd.Series(np.linspace(100, 160, 120), index=idx)
    bars = pd.DataFrame({"open": close - 0.2, "high": close + 0.5, "low": close - 0.5, "close": close})
    a = ind.adx(bars).iloc[-1]
    assert a["adx"] > 50 and a["plus_di"] > a["minus_di"]


def test_supertrend_flips_with_the_trend():
    up = np.linspace(100, 150, 80)
    down = np.linspace(150, 100, 80)
    close = pd.Series(np.concatenate([up, down]), index=pd.bdate_range("2026-01-01", periods=160))
    bars = pd.DataFrame({"open": close, "high": close + 1, "low": close - 1, "close": close})
    st = ind.supertrend(bars, 10, 3)
    assert st["direction"].iloc[70] == 1 and st["direction"].iloc[-1] == -1
    assert (st["supertrend"].iloc[20:70] < close.iloc[20:70]).all()


def test_efficiency_ratio_and_hurst_separate_trend_from_noise():
    rng = np.random.default_rng(0)
    trend = pd.Series(np.linspace(0, 10, 300) + rng.normal(0, 0.005, 300))
    noise = pd.Series(rng.normal(0, 1, 300))
    assert ind.efficiency_ratio(trend, 20).iloc[-1] > 0.8 > ind.efficiency_ratio(noise, 20).iloc[-1]
    walk = np.cumsum(rng.normal(size=5000))
    reverting = np.zeros(5000)
    for t in range(1, 5000):
        reverting[t] = 0.5 * reverting[t - 1] + rng.normal()
    assert ind.hurst_exponent(walk) == pytest.approx(0.5, abs=0.1)
    assert ind.hurst_exponent(reverting) < 0.3


def test_bullish_engulfing_and_hammer():
    rows = falling(6) + [[103.5, 104.0, 102.0, 102.2], [101.8, 104.5, 101.5, 104.2]]
    bars = candles(rows)
    assert pt.bullish_engulfing(bars).iloc[-1] and not pt.bullish_engulfing(bars).iloc[-2]
    hammer_rows = falling(6) + [[103.5, 104.3, 99.0, 104.1]]
    assert pt.hammer(candles(hammer_rows)).iloc[-1]


def test_doji_marubozu_inside_outside():
    bars = candles([[100, 102, 98, 100.1], [99, 101, 99, 101], [100, 100.8, 99.5, 100.2], [99, 102, 98, 101]])
    assert pt.doji(bars).iloc[0] and pt.bullish_marubozu(bars).iloc[1]
    assert pt.inside_bar(bars).iloc[2] and pt.outside_bar(bars).iloc[3]


def test_morning_star_and_three_soldiers():
    base = [[100, 101, 99, 100.5]] * 10
    star = base + [[100, 100.5, 94, 94.5], [94.0, 94.8, 93.5, 94.2], [94.5, 99.0, 94.3, 98.5]]
    assert pt.morning_star(candles(star)).iloc[-1]
    soldiers = base + [[100, 102, 99.8, 101.8], [101, 103.5, 100.9, 103.2], [102.5, 105, 102.4, 104.8]]
    assert pt.three_white_soldiers(candles(soldiers)).iloc[-1]


def test_swings_are_confirmed_k_bars_later():
    close = [1, 2, 3, 6, 3, 2, 1, 2, 3]
    bars = candles([[c, c, c, c] for c in close])
    highs = pt.swing_highs(bars, k=2)
    assert np.isnan(highs.iloc[3]) and highs.iloc[5] == 6   # peak at bar 3, known at bar 5


def test_every_pattern_is_causal():
    bars = data.seasonal_prices(700, seed=3)
    full = pt.scan(bars)
    part = pt.scan(bars.iloc[:500])
    pd.testing.assert_frame_equal(full.iloc[:500], part)
    assert full.dtypes.eq(bool).all()


def test_double_bottom_completes_on_neckline_break():
    path = [110, 105, 100, 105, 108, 104, 100.5, 104, 107, 109, 111, 112]
    bars = candles([[p, p + 0.5, p - 0.5, p] for p in path])
    signal = pt.double_bottom(bars, k=2, tolerance=0.02, lookback=20)
    assert signal.sum() == 1 and signal.idxmax() == bars.index[9]   # first close above the 108.5 neckline


def test_rsi_bounds_and_all_gain_series():
    close = data.gbm_prices(400, seed=4)
    r = ind.rsi(close).dropna()
    assert r.between(0, 100).all()
    rising = pd.Series(np.arange(1, 50, dtype=float))
    assert ind.rsi(rising).dropna().eq(100).all()


def test_hac_tstat_shrinks_for_overlapping_returns():
    rng = np.random.default_rng(0)
    daily = pd.Series(rng.normal(0.0005, 0.01, 3000))
    overlapping = daily.rolling(20).sum().dropna()          # 20-day returns sampled daily
    naive = overlapping.mean() / overlapping.std() * np.sqrt(len(overlapping))
    assert abs(stats.hac_tstat(overlapping, lags=19)) < abs(naive) / 2.5


def test_event_study_has_correct_size_under_the_null():
    rejections = 0
    for seed in range(40):
        close = data.gbm_prices(800, seed=seed)
        events = pd.Series(np.random.default_rng(seed + 100).random(800) < 0.03, index=close.index)
        rejections += stats.event_study(close, events, horizons=(10,), n_perm=300)["p_value"].iloc[0] < 0.05
    assert rejections <= 6                                   # about 2 expected at a 5% level


def test_event_study_finds_a_planted_edge():
    close = data.gbm_prices(1500, sigma=0.15, seed=1)
    # random (not periodic) event dates: a circular shift of a periodic pattern would realign with it
    events = pd.Series(np.random.default_rng(2).random(len(close)) < 0.04, index=close.index)
    events.iloc[-10:] = False
    bumped = close.copy()
    for i in np.flatnonzero(events.to_numpy()):
        bumped.iloc[i + 1:] *= 1.01                         # +1% the day after every event
    table = stats.event_study(bumped, events, horizons=(1, 3))
    assert (table["p_value"] < 0.01).all() and (table["excess"] > 0.008).all()


def test_candles_carry_no_information_about_future_closes():
    # ohlcv_from_close must not reuse the price generator's random stream (same seed)
    bars = data.ohlcv_from_close(data.ar1_prices(3000, phi=0.0, seed=7), seed=7)
    gap = np.log(bars["open"] / bars["close"].shift(1))
    next_ret = np.log(bars["close"].shift(-1) / bars["close"])
    assert abs(gap.corr(next_ret)) < 0.05


def test_factor_tools_work_date_by_date():
    idx = pd.MultiIndex.from_product([pd.date_range("2024-01-31", periods=2, freq="ME"), list("abcd")],
                                     names=["date", "stock"])
    x = pd.Series([1.0, 2.0, 3.0, 100.0, 10.0, 20.0, 30.0, 40.0], index=idx)
    groups = pd.Series(["g1", "g1", "g2", "g2"] * 2, index=idx)
    w = factors.winsorize(x, 0.0, 0.75)
    assert w.loc["2024-01-31"].max() < 100 and w.loc["2024-02-29"].max() <= 40
    z = factors.zscore(x)
    assert np.allclose(z.groupby(level=0).mean(), 0) and np.allclose(z.groupby(level=0).std(), 1)
    n = factors.neutralize(x, groups)
    assert np.allclose(n.groupby([n.index.get_level_values(0), groups]).mean(), 0)
    fwd = x * 0.01
    assert np.allclose(factors.information_coefficient(x, fwd), 1.0)
    q = factors.quantile_returns(x, fwd, q=2)
    assert (q[2] > q[1]).all()
    assert factors.turnover(x, top=0.5).iloc[0] == 0.0


def test_factor_panel_rewards_sector_neutral_value():
    panel = data.factor_panel(n_stocks=150, n_months=96, premium_vol=0.0, seed=3)   # constant premia
    fwd, sector = panel["fwd_ret"], panel["sector"]
    raw = factors.information_coefficient(factors.zscore(panel["earnings_yield"]), fwd).mean()
    neutral = factors.information_coefficient(
        factors.zscore(factors.neutralize(factors.winsorize(panel["earnings_yield"], 0.025, 0.975), sector)), fwd).mean()
    assert neutral > raw + 0.01 and neutral > 0


# -- volatility --------------------------------------------------------------------------------

def test_range_estimators_are_accurate_and_more_efficient_than_close_to_close():
    from cfmat.analytics import volatility as vol

    bars = data.brownian_ohlc(1500, sigma=0.30, overnight_share=0.0, seed=2)
    table = vol.compare_estimators(bars, window=21).dropna()
    for name in ("parkinson", "garman_klass", "rogers_satchell", "yang_zhang"):
        assert table[name].mean() == pytest.approx(0.30, rel=0.07)          # discrete path: slight downward bias
        assert table[name].std() < 0.5 * table["close_to_close"].std()


def test_only_yang_zhang_among_range_estimators_captures_overnight_gaps():
    from cfmat.analytics import volatility as vol

    bars = data.brownian_ohlc(1500, sigma=0.30, overnight_share=0.4, seed=3)
    means = vol.compare_estimators(bars, window=63).mean()
    assert means["parkinson"] < 0.26 and means["garman_klass"] < 0.26        # ≈ 0.30 × √0.6
    assert means["yang_zhang"] == pytest.approx(0.30, rel=0.07)
    assert means["close_to_close"] == pytest.approx(0.30, rel=0.07)


def test_ewma_cone_percentile_and_regime_follow_a_volatility_shift():
    from cfmat.analytics import volatility as vol

    sigma = np.r_[np.full(400, 0.15), np.full(200, 0.45)]
    bars = data.brownian_ohlc(600, sigma=sigma, seed=4)
    ewma = vol.ewma_volatility(bars["close"])
    assert ewma.iloc[380] < 0.2 < 0.35 < ewma.iloc[-1]
    cone = vol.volatility_cone(bars["close"], windows=(21, 63))
    assert list(cone.columns) == ["min", "q25", "median", "q75", "max", "current"]
    assert (cone["min"] <= cone["median"]).all() and (cone["median"] <= cone["max"]).all()
    realised = vol.close_to_close(bars, 21)
    regime = vol.volatility_regime(realised, lookback=252)
    assert regime.iloc[:260].isna().all() and regime.iloc[425:500].eq("high").mean() > 0.9
    assert regime.iloc[-20:].ne("high").any()        # a lasting shift becomes the new normal
    assert vol.volatility_percentile(realised, 252).iloc[450] > 0.9
    with pytest.raises(ValueError):
        vol.ewma_volatility(bars["close"], lam=1.0)


def test_volatility_estimators_have_no_look_ahead():
    from cfmat.analytics import volatility as vol

    bars = data.brownian_ohlc(300, seed=5)
    full = vol.yang_zhang(bars, 21)
    cut = vol.yang_zhang(bars.iloc[:200], 21)
    pd.testing.assert_series_equal(full.iloc[:200], cut)


# -- momentum ----------------------------------------------------------------------------------

def test_momentum_windows_and_skip():
    from cfmat.analytics import momentum as mom

    close = pd.Series(np.arange(1.0, 301.0))
    m = mom.momentum(close, lookback=252, skip=21)
    assert m.iloc[-1] == pytest.approx(close.iloc[-22] / close.iloc[-253] - 1)
    assert m.iloc[:252].isna().all()
    with pytest.raises(ValueError):
        mom.momentum(close, lookback=21, skip=21)


def test_smooth_trend_beats_jumpy_trend_on_quality_scores():
    from cfmat.analytics import momentum as mom

    t = np.arange(300)
    noise = np.random.default_rng(0).normal(0, 0.002, 300)
    steps = 0.06 * np.isin(t, [30, 90, 150, 210, 270]).cumsum()       # same total gain, in five jumps
    both = pd.DataFrame({"smooth": 100 * np.exp(0.001 * t + noise), "jumpy": 100 * np.exp(steps + noise)})
    assert both.iloc[-1, 0] == pytest.approx(both.iloc[-1, 1], rel=0.01)
    assert mom.regression_momentum(both, 90).iloc[-1].idxmax() == "smooth"
    assert mom.risk_adjusted_momentum(both, 252, 21).iloc[-1].idxmax() == "smooth"
    discreteness = mom.information_discreteness(both, 252).iloc[-1]
    assert discreteness["smooth"] < discreteness["jumpy"]                  # continuous = more negative


def test_regression_momentum_recovers_a_known_growth_rate():
    from cfmat.analytics import momentum as mom

    close = pd.Series(100 * np.exp(0.0008 * np.arange(200)))
    assert mom.regression_momentum(close, 90).iloc[-1] == pytest.approx(np.exp(0.0008 * 252) - 1, rel=1e-6)


def test_tsmom_and_dual_momentum_positions():
    from cfmat.analytics import momentum as mom

    prices = data.universe(6, 600, seed=1)
    pos = mom.tsmom_position(prices, lookback=252, target_vol=0.10, max_leverage=1.5)
    assert pos.abs().max().max() <= 1.5 and pos.iloc[:252].isna().all().all()
    weights = mom.dual_momentum_weights(prices, top_n=2)
    assert (weights.sum(axis=1) <= 1.0 + 1e-12).all() and set(np.unique(weights)) <= {0.0, 0.5}
    ranks = mom.cross_sectional_rank(mom.momentum(prices), pct=False).iloc[-1]
    assert sorted(ranks) == [1, 2, 3, 4, 5, 6]


# -- relative performance ------------------------------------------------------------------------

def test_capm_recovers_planted_alpha_and_beta():
    from cfmat.analytics import relative as rel

    rng = np.random.default_rng(3)
    idx = pd.bdate_range("2020-01-01", periods=2000)
    bench = pd.Series(rng.normal(0.0004, 0.01, 2000), idx)
    strat = 0.0002 + 1.3 * bench + pd.Series(rng.normal(0, 0.004, 2000), idx)
    out = rel.capm(strat, bench)
    assert out["beta"] == pytest.approx(1.3, abs=0.03)
    assert out["alpha"] == pytest.approx(0.0002 * 252, abs=0.03) and out["alpha_tstat"] > 2
    assert out["up_capture"] > 1 and out["down_capture"] > 1
    rb = rel.rolling_beta(strat, bench, 126).dropna()
    assert rb.mean() == pytest.approx(1.3, abs=0.05)


def test_relative_strength_rating_and_rotation():
    from cfmat.analytics import relative as rel

    idx = pd.bdate_range("2022-01-03", periods=300)
    t = np.arange(300)
    bench = pd.Series(100 * np.exp(0.0003 * t), idx)
    close = pd.DataFrame({"LEAD": 100 * np.exp(0.0010 * t + 4e-6 * t**2),       # accelerating leader
                          "LAG": 100 * np.exp(-0.0005 * t - 4e-6 * t**2),
                          "FLAT": 100 * np.exp(0.0003 * t)}, index=idx)
    rs = rel.relative_strength(close, bench)
    assert rs.iloc[0].eq(1.0).all() and rs["LEAD"].iloc[-1] > 1 > rs["LAG"].iloc[-1]
    rating = rel.rs_rating(close).iloc[-1]
    assert rating["LEAD"] == 99 and rating["LAG"] == 1
    ratio, momentum = rel.relative_rotation(close, bench, window=63, momentum_window=10)
    quadrant = rel.rotation_quadrant(ratio.iloc[-1], momentum.iloc[-1])
    assert quadrant["LEAD"] == "Leading" and quadrant["LAG"] == "Lagging"
    assert rel.mansfield_rs(close, bench, 100)["LEAD"].iloc[-1] > 0


# -- performance analysis -----------------------------------------------------------------------

def test_underwater_counts_losses_from_the_starting_capital():
    from cfmat.analytics import performance as perf

    r = pd.Series([-0.10, 0.05, 0.10, -0.02], index=pd.bdate_range("2024-01-01", periods=4))
    dd = perf.underwater(r)
    assert dd.iloc[0] == pytest.approx(-0.10)                  # metrics.drawdown_series would show 0 here
    assert dd.iloc[2] == 0.0 and dd.iloc[3] == pytest.approx(-0.02)


def test_drawdown_periods_on_a_known_path():
    from cfmat.analytics import performance as perf

    idx = pd.bdate_range("2024-01-01", periods=9)
    r = pd.Series([0.10, -0.10, -0.10, 0.30, 0.02, -0.05, 0.01, 0.01, 0.0], index=idx)
    table = perf.drawdown_periods(r)
    first = table.iloc[0]
    assert first.depth == pytest.approx(0.81 - 1) and first.peak == idx[0] and first.trough == idx[2]
    assert first.recovery == idx[3] and (first.bars_to_trough, first.recovery_bars, first.total_bars) == (2, 1, 3)
    second = table.iloc[1]
    assert second.peak == idx[4] and pd.isna(second.recovery)       # still open at the end


def test_tearsheet_monthly_table_and_rolling_metrics():
    from cfmat.analytics import performance as perf

    prices = data.universe(2, 756, seed=8)
    r, b = prices.pct_change().dropna().T.to_numpy()
    idx = prices.index[1:]
    r, b = pd.Series(r, idx), pd.Series(b, idx)
    sheet = perf.tearsheet(r, b)
    assert list(sheet.columns) == ["strategy", "benchmark"]
    assert sheet.loc["sharpe", "strategy"] == pytest.approx(metrics.sharpe_ratio(r))
    assert sheet.loc["max_drawdown", "strategy"] <= 0 and sheet.loc["cvar_95", "strategy"] >= sheet.loc["var_95", "strategy"]
    assert pd.isna(sheet.loc["beta", "benchmark"]) and sheet.loc["beta", "strategy"] > 0
    table = perf.monthly_returns(r)
    assert table.loc[2023, "Year"] == pytest.approx(100 * perf.annual_returns(r)[2023])
    roll = perf.rolling_metrics(r, 63, benchmark=b).dropna()
    assert {"sharpe", "max_drawdown", "beta"} <= set(roll.columns) and (roll["max_drawdown"] <= 0).all()
    assert perf.omega_ratio(pd.Series([0.02, -0.01])) == pytest.approx(2.0)
    assert perf.tail_ratio(pd.Series(np.linspace(-1, 1, 101))) == pytest.approx(1.0)


def test_panel_event_study_keeps_its_size_with_correlated_stocks():
    rejections, trials = 0, 60
    for seed in range(trials):
        rng = np.random.default_rng(seed)
        market = rng.normal(0, 0.01, (400, 1))
        close = pd.DataFrame(100 * np.exp(np.cumsum(market + rng.normal(0, 0.01, (400, 8)), axis=0)),
                             index=pd.bdate_range("2024-01-01", periods=400))
        same_day = rng.random(400) < 0.03                                   # news days shared across stocks
        events = pd.DataFrame(np.repeat(same_day[:, None], 8, axis=1), index=close.index, columns=close.columns)
        rejections += stats.event_study(close, events, horizons=(5,), n_perm=200, seed=seed)["p_value"].iloc[0] < 0.05
    assert rejections / trials <= 0.12
