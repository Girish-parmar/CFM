"""Tests for cfmat.analytics: metrics, indicators and patterns."""

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
