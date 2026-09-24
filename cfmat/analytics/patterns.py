"""Candlestick and chart-structure patterns (Modules 5 and 17).

Every function returns a boolean Series that is True on the bar where the
pattern is *complete*, using only that bar and earlier bars, so it can drive a
decision at that bar's close.

Chart structures built on swing points need confirmation: a swing high is only
known ``k`` bars after it happens. ``swing_highs``/``swing_lows`` therefore mark
the swing on the bar where it becomes confirmed, never on the swing bar itself.
Plotting swings on the swing bar is fine for charts and look-ahead for trading.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import bollinger_bandwidth


def _parts(bars: pd.DataFrame):
    o, h, l, c = (bars[k] for k in ("open", "high", "low", "close"))
    body = (c - o).abs()
    rng = (h - l).replace(0.0, np.nan)
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    return o, h, l, c, body, rng, upper, lower


def _downtrend(close: pd.Series, n: int = 5) -> pd.Series:
    return close < close.shift(n)


def _uptrend(close: pd.Series, n: int = 5) -> pd.Series:
    return close > close.shift(n)


# ---------------------------------------------------------------------------
# Single-candle patterns
# ---------------------------------------------------------------------------

def doji(bars: pd.DataFrame, max_body: float = 0.1) -> pd.Series:
    """Open ≈ close: body at most ``max_body`` of the day's range (indecision)."""
    *_, body, rng, _, _ = _parts(bars)
    return (body <= max_body * rng).fillna(False)


def hammer(bars: pd.DataFrame) -> pd.Series:
    """Small body near the high, long lower shadow (≥ 2× body), after a decline."""
    o, h, l, c, body, rng, upper, lower = _parts(bars)
    shape = (lower >= 2 * body) & (upper <= 0.25 * rng) & (body > 0.05 * rng)
    return (shape & _downtrend(c)).fillna(False)


def shooting_star(bars: pd.DataFrame) -> pd.Series:
    """Small body near the low, long upper shadow (≥ 2× body), after a rise."""
    o, h, l, c, body, rng, upper, lower = _parts(bars)
    shape = (upper >= 2 * body) & (lower <= 0.25 * rng) & (body > 0.05 * rng)
    return (shape & _uptrend(c)).fillna(False)


def bullish_marubozu(bars: pd.DataFrame, min_body: float = 0.9) -> pd.Series:
    o, h, l, c, body, rng, _, _ = _parts(bars)
    return ((c > o) & (body >= min_body * rng)).fillna(False)


def bearish_marubozu(bars: pd.DataFrame, min_body: float = 0.9) -> pd.Series:
    o, h, l, c, body, rng, _, _ = _parts(bars)
    return ((c < o) & (body >= min_body * rng)).fillna(False)


# ---------------------------------------------------------------------------
# Two- and three-candle patterns
# ---------------------------------------------------------------------------

def bullish_engulfing(bars: pd.DataFrame) -> pd.Series:
    """Yesterday bearish, today bullish with a body covering yesterday's body."""
    o, h, l, c = (bars[k] for k in ("open", "high", "low", "close"))
    po, pc = o.shift(1), c.shift(1)
    return ((pc < po) & (c > o) & (o <= pc) & (c >= po) & _downtrend(c.shift(1))).fillna(False)


def bearish_engulfing(bars: pd.DataFrame) -> pd.Series:
    o, h, l, c = (bars[k] for k in ("open", "high", "low", "close"))
    po, pc = o.shift(1), c.shift(1)
    return ((pc > po) & (c < o) & (o >= pc) & (c <= po) & _uptrend(c.shift(1))).fillna(False)


def piercing_line(bars: pd.DataFrame) -> pd.Series:
    """Bearish day, then a bullish day opening below its low and closing above its midpoint."""
    o, h, l, c = (bars[k] for k in ("open", "high", "low", "close"))
    po, pc, pl = o.shift(1), c.shift(1), l.shift(1)
    return ((pc < po) & (o < pl) & (c > (po + pc) / 2) & (c < po)).fillna(False)


def dark_cloud_cover(bars: pd.DataFrame) -> pd.Series:
    o, h, l, c = (bars[k] for k in ("open", "high", "low", "close"))
    po, pc, ph = o.shift(1), c.shift(1), h.shift(1)
    return ((pc > po) & (o > ph) & (c < (po + pc) / 2) & (c > po)).fillna(False)


def morning_star(bars: pd.DataFrame) -> pd.Series:
    """Long bearish candle, small-bodied candle, then a bullish candle closing above
    the first candle's midpoint."""
    o, h, l, c, body, rng, _, _ = _parts(bars)
    avg_body = body.rolling(10).mean()
    first_bear = (c.shift(2) < o.shift(2)) & (body.shift(2) > avg_body.shift(2))
    small_mid = body.shift(1) < 0.5 * avg_body.shift(1)
    third_bull = (c > o) & (c > (o.shift(2) + c.shift(2)) / 2)
    return (first_bear & small_mid & third_bull).fillna(False)


def evening_star(bars: pd.DataFrame) -> pd.Series:
    o, h, l, c, body, rng, _, _ = _parts(bars)
    avg_body = body.rolling(10).mean()
    first_bull = (c.shift(2) > o.shift(2)) & (body.shift(2) > avg_body.shift(2))
    small_mid = body.shift(1) < 0.5 * avg_body.shift(1)
    third_bear = (c < o) & (c < (o.shift(2) + c.shift(2)) / 2)
    return (first_bull & small_mid & third_bear).fillna(False)


def three_white_soldiers(bars: pd.DataFrame) -> pd.Series:
    """Three rising bullish candles, each opening inside the previous body."""
    o, c = bars["open"], bars["close"]
    bull = c > o
    rising = (c > c.shift(1)) & (c.shift(1) > c.shift(2))
    opens_inside = (o > o.shift(1)) & (o < c.shift(1)) & (o.shift(1) > o.shift(2)) & (o.shift(1) < c.shift(2))
    return (bull & bull.shift(1, fill_value=False) & bull.shift(2, fill_value=False) & rising & opens_inside).fillna(False)


def three_black_crows(bars: pd.DataFrame) -> pd.Series:
    o, c = bars["open"], bars["close"]
    bear = c < o
    falling = (c < c.shift(1)) & (c.shift(1) < c.shift(2))
    opens_inside = (o < o.shift(1)) & (o > c.shift(1)) & (o.shift(1) < o.shift(2)) & (o.shift(1) > c.shift(2))
    return (bear & bear.shift(1, fill_value=False) & bear.shift(2, fill_value=False) & falling & opens_inside).fillna(False)


def inside_bar(bars: pd.DataFrame) -> pd.Series:
    return ((bars["high"] < bars["high"].shift(1)) & (bars["low"] > bars["low"].shift(1))).fillna(False)


def outside_bar(bars: pd.DataFrame) -> pd.Series:
    return ((bars["high"] > bars["high"].shift(1)) & (bars["low"] < bars["low"].shift(1))).fillna(False)


# ---------------------------------------------------------------------------
# Chart structure
# ---------------------------------------------------------------------------

def swing_highs(bars: pd.DataFrame, k: int = 3) -> pd.Series:
    """Price of each swing high (a high above the k highs on both sides), placed on
    the bar where it is *confirmed* (k bars later). NaN elsewhere."""
    h = bars["high"]
    centred = h.rolling(2 * k + 1, center=True).max()
    is_swing = h == centred
    return h.where(is_swing).shift(k)


def swing_lows(bars: pd.DataFrame, k: int = 3) -> pd.Series:
    low = bars["low"]
    centred = low.rolling(2 * k + 1, center=True).min()
    return low.where(low == centred).shift(k)


def higher_highs_lows(bars: pd.DataFrame, k: int = 3) -> pd.Series:
    """Uptrend structure: the last confirmed swing high and swing low are both
    above the ones before them."""
    sh = swing_highs(bars, k).dropna()
    sl = swing_lows(bars, k).dropna()
    hh = (sh > sh.shift(1)).reindex(bars.index).ffill()
    hl = (sl > sl.shift(1)).reindex(bars.index).ffill()
    return (hh.astype("boolean").fillna(False) & hl.astype("boolean").fillna(False)).astype(bool)


def lower_highs_lows(bars: pd.DataFrame, k: int = 3) -> pd.Series:
    sh = swing_highs(bars, k).dropna()
    sl = swing_lows(bars, k).dropna()
    lh = (sh < sh.shift(1)).reindex(bars.index).ffill()
    ll = (sl < sl.shift(1)).reindex(bars.index).ffill()
    return (lh.astype("boolean").fillna(False) & ll.astype("boolean").fillna(False)).astype(bool)


def double_bottom(bars: pd.DataFrame, k: int = 3, tolerance: float = 0.02, lookback: int = 60) -> pd.Series:
    """Two confirmed swing lows within ``tolerance`` of each other inside
    ``lookback`` bars, completed when the close breaks above the highest high
    between them (the neckline)."""
    lows = swing_lows(bars, k)
    close, high = bars["close"].to_numpy(), bars["high"].to_numpy()
    out = np.zeros(len(bars), dtype=bool)
    pts = [(i, v) for i, v in enumerate(lows.to_numpy()) if not np.isnan(v)]
    for j in range(1, len(pts)):
        (i1, v1), (i2, v2) = pts[j - 1], pts[j]
        if i2 - i1 > lookback or abs(v2 / v1 - 1) > tolerance:
            continue
        neckline = high[i1 - k : i2 - k + 1].max()
        for t in range(i2, min(len(bars), i2 + lookback)):
            if close[t] > neckline:
                out[t] = True
                break
    return pd.Series(out, index=bars.index)


def double_top(bars: pd.DataFrame, k: int = 3, tolerance: float = 0.02, lookback: int = 60) -> pd.Series:
    highs = swing_highs(bars, k)
    close, low = bars["close"].to_numpy(), bars["low"].to_numpy()
    out = np.zeros(len(bars), dtype=bool)
    pts = [(i, v) for i, v in enumerate(highs.to_numpy()) if not np.isnan(v)]
    for j in range(1, len(pts)):
        (i1, v1), (i2, v2) = pts[j - 1], pts[j]
        if i2 - i1 > lookback or abs(v2 / v1 - 1) > tolerance:
            continue
        neckline = low[i1 - k : i2 - k + 1].min()
        for t in range(i2, min(len(bars), i2 + lookback)):
            if close[t] < neckline:
                out[t] = True
                break
    return pd.Series(out, index=bars.index)


def consolidation(bars: pd.DataFrame, window: int = 20, max_width: float = 0.06) -> pd.Series:
    """Range-bound box: the last ``window`` bars fit inside ``max_width`` of price."""
    width = (bars["high"].rolling(window).max() - bars["low"].rolling(window).min()) / bars["close"]
    return (width <= max_width).fillna(False)


def squeeze(bars: pd.DataFrame, window: int = 20, lookback: int = 120, tolerance: float = 1.05) -> pd.Series:
    """Bollinger bandwidth within ``tolerance`` of its ``lookback``-bar low:
    volatility is compressed and a breakout (either way) often follows."""
    bw = bollinger_bandwidth(bars["close"], window)
    return (bw <= bw.rolling(lookback).min() * tolerance).fillna(False)


CANDLESTICK_PATTERNS = {
    "doji": doji, "hammer": hammer, "shooting_star": shooting_star,
    "bullish_marubozu": bullish_marubozu, "bearish_marubozu": bearish_marubozu,
    "bullish_engulfing": bullish_engulfing, "bearish_engulfing": bearish_engulfing,
    "piercing_line": piercing_line, "dark_cloud_cover": dark_cloud_cover,
    "morning_star": morning_star, "evening_star": evening_star,
    "three_white_soldiers": three_white_soldiers, "three_black_crows": three_black_crows,
    "inside_bar": inside_bar, "outside_bar": outside_bar,
}
CHART_PATTERNS = {
    "higher_highs_lows": higher_highs_lows, "lower_highs_lows": lower_highs_lows,
    "double_bottom": double_bottom, "double_top": double_top,
    "consolidation": consolidation, "squeeze": squeeze,
}
ALL_PATTERNS = {**CANDLESTICK_PATTERNS, **CHART_PATTERNS}


def scan(bars: pd.DataFrame, names: list[str] | None = None) -> pd.DataFrame:
    """Evaluate many patterns at once (one boolean column each)."""
    names = names or list(ALL_PATTERNS)
    return pd.DataFrame({n: ALL_PATTERNS[n](bars) for n in names}, index=bars.index)
