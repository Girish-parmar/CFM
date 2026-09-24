import numpy as np
import pandas as pd
import pytest

from cfmat import data, indicators as ind, patterns as pt


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
