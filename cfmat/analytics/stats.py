"""Statistical tests that research code needs again and again (M04, M06, M07, M23).

    hac_tstat            t-statistic of a mean with Newey-West (HAC) standard errors,
                         for overlapping forward returns or autocorrelated series
    benjamini_hochberg   false-discovery-rate adjusted p-values (q-values)
    event_study          forward returns after events vs other days: HAC t-statistic and
                         a random-date (circular-shift) permutation p-value
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def hac_tstat(x: pd.Series | np.ndarray, lags: int | None = None) -> float:
    """t-statistic of ``mean(x)`` with Newey-West standard errors (Bartlett kernel).

    Use it when observations overlap (for example 20-day forward returns sampled
    daily): the ordinary t-statistic then overstates significance roughly by the
    square root of the overlap. ``lags`` defaults to ``floor(4 (n/100)^(2/9))``.
    """
    v = pd.Series(x, dtype=float).dropna().to_numpy()
    n = len(v)
    if n < 3:
        return float("nan")
    if lags is None:
        lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    e = v - v.mean()
    long_run = e @ e / n
    for lag in range(1, min(lags, n - 1) + 1):
        weight = 1 - lag / (lags + 1)
        long_run += 2 * weight * (e[lag:] @ e[:-lag]) / n
    if long_run <= 0:
        return float("nan")
    return float(v.mean() / np.sqrt(long_run / n))


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


def event_study(
    close: pd.Series,
    events: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 10, 20),
    n_perm: int = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """Forward returns after event days compared with the other days.

    ``events`` is a boolean Series known at the close of each day; forward returns
    start from that close. For each horizon ``h``:

    * ``excess`` is the mean forward return after events minus the mean on other days;
    * ``t_hac`` regresses forward returns on an event dummy with Newey-West errors
      (``h - 1`` lags, because consecutive ``h``-day windows overlap);
    * ``p_value`` is a two-sided *random-date* permutation test: the event series is
      shifted circularly ``n_perm`` times, which keeps the events' clustering and the
      returns' autocorrelation. It stays honest when events are few, where HAC
      standard errors are too small.

    ``close`` and ``events`` may also be DataFrames with one column per stock: forward
    returns are pooled; every stock's events are shifted by the same amount in the
    permutation, which keeps same-day clustering across correlated stocks; ``t_hac``
    uses Newey-West errors within each stock.
    """
    import statsmodels.api as sm

    if isinstance(close, pd.DataFrame):
        return _panel_event_study(close, events, horizons, n_perm, seed)
    events = events.reindex(close.index).fillna(False).astype(bool)
    rng = np.random.default_rng(seed)
    rows = {}
    for h in horizons:
        fwd = (close.shift(-h) / close - 1).to_numpy()
        valid = ~np.isnan(fwd)
        y, ev = fwd[valid], events.to_numpy()[valid]
        n, k = len(y), int(ev.sum())
        row = {"events": k, "mean_after": y[ev].mean() if k else np.nan,
               "mean_other": y[~ev].mean() if k < n else np.nan,
               "hit_rate": (y[ev] > 0).mean() if k else np.nan}
        if k >= 2 and n - k >= 2:
            fit = sm.OLS(y, sm.add_constant(ev.astype(float))).fit(cov_type="HAC", cov_kwds={"maxlags": max(h - 1, 1)})
            observed = row["mean_after"] - row["mean_other"]
            idx = np.flatnonzero(ev)
            shifts = rng.integers(1, n, size=n_perm)
            total = y.sum()
            after = np.array([y[(idx + s) % n].mean() for s in shifts])
            perm = after - (total - after * k) / (n - k)
            p_value = (1 + np.sum(np.abs(perm) >= abs(observed))) / (1 + n_perm)
            row.update(excess=observed, t_hac=float(fit.tvalues[1]), p_value=float(p_value))
        else:
            row.update(excess=np.nan, t_hac=np.nan, p_value=np.nan)
        rows[f"{h}d"] = row
    return pd.DataFrame(rows).T[["events", "mean_after", "mean_other", "excess", "hit_rate", "t_hac", "p_value"]]


def _panel_event_study(close: pd.DataFrame, events: pd.DataFrame, horizons, n_perm: int, seed: int) -> pd.DataFrame:
    import statsmodels.api as sm

    events = events.reindex(index=close.index, columns=close.columns).fillna(False).astype(bool)
    rng = np.random.default_rng(seed)
    rows = {}
    for h in horizons:
        fwd = close.shift(-h) / close - 1
        keep = fwd.notna().all(axis=1).to_numpy()
        y, ev = fwd.to_numpy()[keep], events.to_numpy()[keep]
        n, k = y.shape[0], int(ev.sum())
        row = {"events": k, "mean_after": y[ev].mean() if k else np.nan,
               "mean_other": y[~ev].mean() if k < y.size else np.nan,
               "hit_rate": (y[ev] > 0).mean() if k else np.nan}
        if k >= 2 and y.size - k >= 2:
            groups = np.repeat(np.arange(y.shape[1]), n)
            fit = sm.OLS(y.T.ravel(), sm.add_constant(ev.T.ravel().astype(float))).fit(
                cov_type="hac-panel", cov_kwds={"groups": groups, "maxlags": max(h - 1, 1)})
            observed = row["mean_after"] - row["mean_other"]
            total = y.sum()
            perm = np.empty(n_perm)
            for i, shift in enumerate(rng.integers(1, n, size=n_perm)):
                after = y[np.roll(ev, shift, axis=0)].sum()
                perm[i] = after / k - (total - after) / (y.size - k)
            p_value = (1 + np.sum(np.abs(perm) >= abs(observed))) / (1 + n_perm)
            row.update(excess=observed, t_hac=float(fit.tvalues[1]), p_value=float(p_value))
        else:
            row.update(excess=np.nan, t_hac=np.nan, p_value=np.nan)
        rows[f"{h}d"] = row
    return pd.DataFrame(rows).T[["events", "mean_after", "mean_other", "excess", "hit_rate", "t_hac", "p_value"]]
