"""Cross-sectional factor research on a (date, asset) panel (M07).

Every function works date by date, so information from other dates never leaks
into a score. Inputs are Series indexed by a two-level MultiIndex ``(date, asset)``.

    winsorize                clip each date's values at quantiles
    zscore                   standardise each date's values (optionally within groups)
    neutralize               remove group means (e.g. sector) date by date
    information_coefficient  rank correlation of scores with next-period returns, per date
    quantile_returns         mean next-period return of each score quantile, per date
    factor_summary           mean IC, IC volatility, ICIR, t-statistic and hit rate
    turnover                 share of the top quantile replaced each period
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd

DATE = 0  # level of the date in the (date, asset) index


def _by_date(s: pd.Series):
    return s.groupby(level=DATE, group_keys=False)


def winsorize(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Clip each date's cross-section at its ``lower`` and ``upper`` quantiles."""
    return _by_date(s).apply(lambda x: x.clip(x.quantile(lower), x.quantile(upper)))


def zscore(s: pd.Series, groups: pd.Series | None = None) -> pd.Series:
    """Cross-sectional z-score per date, or per (date, group) when ``groups`` is given."""
    keys = [s.index.get_level_values(DATE)] + ([groups.reindex(s.index)] if groups is not None else [])
    grouped = s.groupby(keys, group_keys=False)
    std = grouped.transform("std").replace(0, np.nan)
    return (s - grouped.transform("mean")) / std


def neutralize(s: pd.Series, groups: pd.Series) -> pd.Series:
    """Subtract each (date, group) mean: the score no longer bets on groups (sectors)."""
    keys = [s.index.get_level_values(DATE), groups.reindex(s.index)]
    return s - s.groupby(keys).transform("mean")


def information_coefficient(scores: pd.Series, fwd_returns: pd.Series) -> pd.Series:
    """Spearman rank correlation between scores and next-period returns, one value per date."""
    both = pd.concat({"s": scores, "r": fwd_returns}, axis=1).dropna()
    return both.groupby(level=DATE).apply(lambda g: g["s"].rank().corr(g["r"].rank()) if len(g) > 2 else np.nan)


def quantile_returns(scores: pd.Series, fwd_returns: pd.Series, q: int = 5) -> pd.DataFrame:
    """Mean next-period return of each score quantile (1 = lowest), one row per date."""
    both = pd.concat({"s": scores, "r": fwd_returns}, axis=1).dropna()
    both["bucket"] = both.groupby(level=DATE)["s"].transform(
        lambda x: pd.qcut(x.rank(method="first"), q, labels=False) + 1
    )
    return both.groupby([both.index.get_level_values(DATE), "bucket"])["r"].mean().unstack("bucket")


def factor_summary(ic: pd.Series, periods_per_year: int = 12) -> pd.Series:
    """Headline statistics of an IC series."""
    ic = ic.dropna()
    mean, sd = ic.mean(), ic.std(ddof=1)
    return pd.Series({
        "mean_ic": mean,
        "ic_vol": sd,
        "icir_annual": mean / sd * np.sqrt(periods_per_year) if sd > 0 else np.nan,
        "t_stat": mean / sd * np.sqrt(len(ic)) if sd > 0 else np.nan,
        "hit_rate": (ic > 0).mean(),
        "periods": float(len(ic)),
    })


def turnover(scores: pd.Series, top: float = 0.2) -> pd.Series:
    """Fraction of the top-``top`` names on each date that were not in it the date before."""
    members = {}
    for date, x in scores.dropna().groupby(level=DATE):
        k = max(1, round(len(x) * top))
        members[date] = set(x.droplevel(DATE).nlargest(k).index)
    dates = sorted(members)
    out = {d: 1 - len(members[d] & members[p]) / len(members[d]) for p, d in pairwise(dates)}
    return pd.Series(out, dtype=float)
