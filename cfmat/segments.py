"""Strategy optimisation by segment: calendar, regime and pattern (Module 16).

A strategy rarely works equally well every day. This module splits history into
*segments* (weekday, month, turn of month, expiry week, volatility regime, trend
regime, price patterns), measures performance per segment with proper
multiple-testing control, optimises parameters per segment, and turns segment
labels into features for a boosted model.

Timing rule: a label used for a decision at bar t's close must be known at that
close. Regime and pattern labels computed here use data up to t only. Calendar
labels describe the *next* session (``next_session=True``), which is fine
because the trading calendar is published in advance.
"""

from __future__ import annotations

from itertools import product
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats

from .backtest import vectorized_backtest
from .metrics import sharpe_ratio

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------------------------------------------------------------------------
# Segment labels
# ---------------------------------------------------------------------------

def calendar_segments(index: pd.DatetimeIndex, tom_days: tuple[int, int] = (1, 3), next_session: bool = True) -> pd.DataFrame:
    """Weekday, month and turn-of-month labels.

    ``turn_of_month`` is True for the last ``tom_days[0]`` and first
    ``tom_days[1]`` trading days of each month. With ``next_session=True`` each
    row describes the session *after* that row, i.e. the day a position taken at
    this close will be held.
    """
    idx = pd.DatetimeIndex(index)
    months = idx.to_period("M")
    ones = pd.Series(1, index=idx)
    from_start = ones.groupby(months).cumsum()
    from_end = ones.iloc[::-1].groupby(months[::-1]).cumsum().iloc[::-1]
    labels = pd.DataFrame({
        "weekday": [WEEKDAYS[d] for d in idx.weekday],
        "month": [MONTHS[m - 1] for m in idx.month],
        "turn_of_month": ((from_end <= tom_days[0]) | (from_start <= tom_days[1])).to_numpy(),
        "day_of_month": from_start.to_numpy(),
    }, index=idx)
    return labels.shift(-1) if next_session else labels


def expiry_week(index: pd.DatetimeIndex, weekday: int, next_session: bool = True) -> pd.Series:
    """True in the trading week that ends with the month's last ``weekday``
    (0 = Monday … 4 = Friday). Pass the expiry weekday currently set by your
    exchange for the contract you trade; exchanges change it by circular."""
    idx = pd.DatetimeIndex(index)
    months = idx.to_period("M")
    is_wd = pd.Series(idx.weekday == weekday, index=idx)
    last = is_wd[is_wd].groupby(months[is_wd.to_numpy()]).apply(lambda s: s.index.max())
    expiry = pd.Series(pd.NaT, index=idx)
    expiry[:] = [last.get(p, pd.NaT) for p in months]
    in_week = (expiry - idx).dt.days.between(0, 6) & (idx <= expiry)
    out = pd.Series(in_week.to_numpy(), index=idx, name="expiry_week")
    return out.shift(-1).fillna(False).astype(bool) if next_session else out


def volatility_regime(close: pd.Series, window: int = 20, lookback: int = 252) -> pd.Series:
    """'low' / 'mid' / 'high': where today's rolling volatility ranks within the
    trailing ``lookback`` days (terciles). Uses data up to each bar only."""
    vol = np.log(close).diff().rolling(window).std()
    rank = vol.rolling(lookback, min_periods=window * 2).rank(pct=True)
    labels = pd.cut(rank, [0, 1 / 3, 2 / 3, 1.0], labels=["low", "mid", "high"], include_lowest=True)
    return labels.astype(object).rename("vol_regime")


def trend_regime(close: pd.Series, window: int = 200) -> pd.Series:
    """'up' when the close is above its ``window``-day average, else 'down'."""
    sma = close.rolling(window).mean()
    out = pd.Series(np.where(close > sma, "up", "down"), index=close.index, dtype=object)
    return out.where(sma.notna()).rename("trend_regime")


def pattern_segments(bars: pd.DataFrame, streak: int = 3, breakout: int = 20) -> pd.DataFrame:
    """Price-pattern flags known at each close.

    down_streak / up_streak: the last ``streak`` closes all fell / rose.
    new_high / new_low: close at a ``breakout``-day extreme.
    big_up / big_down: a move beyond 2 standard deviations of the last 60 days.
    inside_day: today's range inside yesterday's. nr7: narrowest range of 7 days.
    gap_up / gap_down: open more than 0.5 standard deviations away from the prior close.
    """
    close = bars["close"]
    ret = close.pct_change()
    sd = ret.rolling(60).std()
    out = pd.DataFrame(index=bars.index)
    out["down_streak"] = (ret < 0).astype(int).rolling(streak).sum() == streak
    out["up_streak"] = (ret > 0).astype(int).rolling(streak).sum() == streak
    out["new_high"] = close >= close.rolling(breakout).max()
    out["new_low"] = close <= close.rolling(breakout).min()
    out["big_up"] = ret > 2 * sd
    out["big_down"] = ret < -2 * sd
    if {"high", "low"}.issubset(bars.columns):
        rng = bars["high"] - bars["low"]
        out["inside_day"] = (bars["high"] < bars["high"].shift(1)) & (bars["low"] > bars["low"].shift(1))
        out["nr7"] = rng <= rng.rolling(7).min()
    if "open" in bars.columns:
        gap = bars["open"] / close.shift(1) - 1
        out["gap_up"] = gap > 0.5 * sd
        out["gap_down"] = gap < -0.5 * sd
    return out.fillna(False).astype(bool)


def segment_features(bars: pd.DataFrame, tom_days: tuple[int, int] = (1, 3)) -> pd.DataFrame:
    """All segment labels as numeric features for a model (known at each close).

    Calendar columns describe the next session; regime and pattern columns use
    data up to the current bar. Column prefixes (``cal_``, ``reg_``, ``pat_``)
    let you measure importance by family.
    """
    close = bars["close"]
    cal = calendar_segments(bars.index, tom_days=tom_days, next_session=True)
    feats = pd.DataFrame(index=bars.index)
    feats["cal_weekday"] = cal["weekday"].map({d: i for i, d in enumerate(WEEKDAYS)})
    feats["cal_month"] = cal["month"].map({m: i + 1 for i, m in enumerate(MONTHS)})
    feats["cal_turn_of_month"] = cal["turn_of_month"].astype(float)
    feats["cal_day_of_month"] = cal["day_of_month"].astype(float)
    feats["reg_vol"] = volatility_regime(close).map({"low": 0, "mid": 1, "high": 2}).astype(float)
    feats["reg_trend_up"] = trend_regime(close).map({"down": 0, "up": 1}).astype(float)
    for name, col in pattern_segments(bars).items():
        feats[f"pat_{name}"] = col.astype(float)
    return feats


# ---------------------------------------------------------------------------
# Statistics per segment
# ---------------------------------------------------------------------------

def benjamini_hochberg(pvalues: pd.Series) -> pd.Series:
    """False-discovery-rate adjusted p-values (q-values)."""
    p = pvalues.to_numpy(dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(q, 0, 1)
    return pd.Series(out, index=pvalues.index)


def segment_stats(returns: pd.Series, labels: pd.DataFrame, min_obs: int = 30) -> pd.DataFrame:
    """Performance of ``returns`` inside each segment versus all other days.

    ``labels`` has one column per segment family (values = segment names, or
    booleans for flags). For each segment: observations, mean return (bp),
    hit rate, annualised Sharpe, Welch t-test against the rest of the sample,
    raw p-value and Benjamini–Hochberg q-value across *every* segment tested.
    """
    rows = []
    r = returns.dropna()
    lab = labels.reindex(r.index)
    for family in lab.columns:
        col = lab[family]
        values = [True] if col.dropna().isin([True, False]).all() else sorted(col.dropna().unique(), key=str)
        for value in values:
            mask = (col == value).to_numpy()
            inside, outside = r[mask], r[~mask & col.notna().to_numpy()]
            if len(inside) < min_obs or len(outside) < min_obs:
                continue
            t, p = stats.ttest_ind(inside, outside, equal_var=False)
            rows.append({"family": family, "segment": str(value), "n": len(inside),
                         "mean_bp": inside.mean() * 1e4, "rest_bp": outside.mean() * 1e4,
                         "hit_rate": (inside > 0).mean(), "sharpe": sharpe_ratio(inside), "t_stat": t, "p_value": p})
    table = pd.DataFrame(rows)
    if len(table):
        table["q_value"] = benjamini_hochberg(table["p_value"])
    return table.sort_values("p_value", ignore_index=True)


# ---------------------------------------------------------------------------
# Optimisation per segment
# ---------------------------------------------------------------------------

def _grid(grid: dict[str, list]) -> list[dict]:
    keys = list(grid)
    return [dict(zip(keys, values)) for values in product(*(grid[k] for k in keys))]


def per_segment_best(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    segment: pd.Series,
    rows: slice | np.ndarray,
    cost_bps: float = 0.0,
    min_obs: int = 60,
) -> tuple[dict, dict]:
    """Best parameters overall and for each segment value, judged on ``rows`` only.

    Returns (global_best, {segment_value: best_params}). A segment with fewer
    than ``min_obs`` observations falls back to the global best.
    """
    candidates = _grid(grid)
    returns = {i: vectorized_backtest(close, strategy(close, **p), cost_bps)["strategy_return"]
               for i, p in enumerate(candidates)}
    window = close.index[rows]
    seg = segment.reindex(window)
    held_seg = segment.shift(1).reindex(window)          # the return at t belongs to the segment decided at t−1
    global_i = max(returns, key=lambda i: sharpe_ratio(returns[i].loc[window]))
    best = {}
    for value in seg.dropna().unique():
        days = window[(held_seg == value).to_numpy()]
        if len(days) < min_obs:
            best[value] = candidates[global_i]
            continue
        best[value] = candidates[max(returns, key=lambda i: sharpe_ratio(returns[i].loc[days]))]
    return candidates[global_i], best


def segmented_signal(
    close: pd.Series, strategy: Callable[..., pd.Series], params_by_segment: dict, segment: pd.Series, default: dict
) -> pd.Series:
    """Each day use the signal of the parameter set assigned to that day's segment."""
    cache: dict[tuple, pd.Series] = {}
    out = pd.Series(0.0, index=close.index)
    seg = segment.reindex(close.index)
    for value in list(params_by_segment) + [None]:
        params = params_by_segment.get(value, default) if value is not None else default
        key = tuple(sorted(params.items()))
        if key not in cache:
            cache[key] = strategy(close, **params)
        mask = seg.isna() if value is None else (seg == value)
        out[mask.to_numpy()] = cache[key][mask.to_numpy()]
    return out


def walk_forward_by_segment(
    close: pd.Series,
    strategy: Callable[..., pd.Series],
    grid: dict[str, list],
    segment: pd.Series,
    train: int = 1000,
    test: int = 250,
    cost_bps: float = 0.0,
    min_obs: int = 60,
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """Walk-forward comparison of one global parameter set vs one per segment.

    Returns (global out-of-sample returns, per-segment out-of-sample returns,
    table of the choices made in each window).
    """
    glob, seg_r, chosen = [], [], []
    for start in range(0, len(close) - train - test + 1, test):
        train_rows = slice(start, start + train)
        test_idx = close.index[start + train : start + train + test]
        g_best, s_best = per_segment_best(close.iloc[: start + train], strategy, grid, segment,
                                          train_rows, cost_bps, min_obs)
        upto = close.iloc[: start + train + test]
        g_sig = strategy(upto, **g_best)
        s_sig = segmented_signal(upto, strategy, s_best, segment, g_best)
        glob.append(vectorized_backtest(upto, g_sig, cost_bps)["strategy_return"].loc[test_idx])
        seg_r.append(vectorized_backtest(upto, s_sig, cost_bps)["strategy_return"].loc[test_idx])
        chosen.append({"test_start": test_idx[0], "global": g_best,
                       **{f"seg={k}": v for k, v in sorted(s_best.items(), key=lambda kv: str(kv[0]))}})
    if not glob:
        raise ValueError("series too short for the requested train/test windows")
    return pd.concat(glob), pd.concat(seg_r), pd.DataFrame(chosen)


def segment_filter_positions(
    returns: pd.Series,
    labels: pd.DataFrame,
    train: int = 1000,
    test: int = 250,
    q_max: float = 0.10,
    min_obs: int = 30,
    expanding: bool = True,
) -> tuple[pd.Series, pd.DataFrame]:
    """Walk-forward long/flat rule: in each training window, find segments whose
    mean return is significantly different from the rest (BH q-value < ``q_max``)
    *and* negative, and stay flat in them during the next test window; be long
    otherwise. (A segment that merely earns less than average still earns
    money, so a long/flat strategy should keep holding it.)

    With ``expanding=True`` each training window runs from the first bar (more
    data, more power to detect small calendar effects); otherwise it is the last
    ``train`` bars.

    ``labels`` must describe the session being held (e.g. calendar labels with
    ``next_session=True``, or regime/pattern labels at the decision close).
    Returns positions (decided at each close) and the segments avoided per window.
    """
    pos = pd.Series(np.nan, index=returns.index)
    avoided = []
    for start in range(0, len(returns) - train - test + 1, test):
        first = 1 if expanding else start + 1
        tr = returns.index[first : start + train]                      # returns earned in the training window
        decided = labels.shift(1).reindex(tr)                          # label decided the close before
        table = segment_stats(returns.loc[tr], decided, min_obs=min_obs)
        bad = table[(table["q_value"] < q_max) & (table["mean_bp"] < 0)] if len(table) else table
        test_idx = returns.index[start + train : start + train + test]
        flat = pd.Series(False, index=test_idx)
        lab_test = labels.reindex(test_idx)
        for _, row in bad.iterrows():
            col = lab_test[row["family"]]
            flat |= (col.astype(str) == row["segment"]).to_numpy()
        pos.loc[test_idx] = np.where(flat, 0.0, 1.0)
        avoided.append({"test_start": test_idx[0],
                        "avoid": ", ".join(f"{r.family}={r.segment}" for r in bad.itertuples()) or "none"})
    return pos, pd.DataFrame(avoided)
