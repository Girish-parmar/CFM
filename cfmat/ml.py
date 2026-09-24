"""Machine learning for trading (Module 12).

Financial labels overlap in time (a 10-day label at t shares 9 days with the
label at t+1), so ordinary K-fold cross-validation leaks the future into the
past. This module provides the three fixes taught in class:

* ``triple_barrier_labels`` — path-dependent labels with profit-take,
  stop-loss and time barriers (López de Prado, 2018, ch. 3).
* ``purged_kfold`` — removes training samples whose labels overlap the test
  fold, plus an embargo after it (ch. 7).
* ``walk_forward_splits`` — train only on the past, always.
"""

from __future__ import annotations

from typing import Callable, Iterator

import numpy as np
import pandas as pd

from .indicators import atr, macd, rsi, sma


def make_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Features that use only information available at each bar's close."""
    close = bars["close"]
    logret = np.log(close).diff()
    feats = pd.DataFrame(index=bars.index)
    for lag in (1, 5, 10, 20):
        feats[f"ret_{lag}"] = close.pct_change(lag)
    feats["vol_20"] = logret.rolling(20).std()
    feats["vol_ratio"] = logret.rolling(5).std() / feats["vol_20"]
    feats["rsi_14"] = rsi(close, 14) / 100.0
    feats["dist_sma_20"] = close / sma(close, 20) - 1.0
    feats["dist_sma_50"] = close / sma(close, 50) - 1.0
    feats["macd_hist"] = macd(close)["histogram"] / close
    if {"high", "low"}.issubset(bars.columns):
        feats["atr_pct"] = atr(bars, 14) / close
    if "volume" in bars.columns:
        vol = bars["volume"].astype(float)
        feats["volume_z"] = (vol - vol.rolling(20).mean()) / vol.rolling(20).std()
    return feats.replace([np.inf, -np.inf], np.nan)


def triple_barrier_labels(
    close: pd.Series,
    horizon: int = 10,
    pt_mult: float = 1.0,
    sl_mult: float = 1.0,
    vol_window: int = 20,
    vertical: str = "sign",
) -> pd.DataFrame:
    """Label each bar by which barrier the price path touches first.

    Barrier width = volatility over the horizon (daily vol · sqrt(horizon)),
    scaled by ``pt_mult`` / ``sl_mult``. Returns columns ``label`` (+1 / −1,
    or 0 on the time barrier when ``vertical="zero"``), ``exit_pos`` (integer
    position of the exit bar) and ``ret`` (log return to exit).
    """
    logp = np.log(close.to_numpy(dtype=float))
    daily_vol = pd.Series(logp, index=close.index).diff().rolling(vol_window).std().to_numpy()
    n = len(close)
    labels = np.full(n, np.nan)
    exits = np.full(n, np.nan)
    rets = np.full(n, np.nan)
    for i in range(n - horizon):
        if np.isnan(daily_vol[i]):
            continue
        width = daily_vol[i] * np.sqrt(horizon)
        path = logp[i + 1 : i + horizon + 1] - logp[i]
        up = np.nonzero(path >= pt_mult * width)[0]
        down = np.nonzero(path <= -sl_mult * width)[0]
        first_up = up[0] if len(up) else horizon
        first_down = down[0] if len(down) else horizon
        if first_up < first_down:
            labels[i], j = 1, first_up
        elif first_down < first_up:
            labels[i], j = -1, first_down
        else:
            j = horizon - 1
            labels[i] = np.sign(path[j]) if vertical == "sign" else 0
        exits[i] = i + 1 + j
        rets[i] = path[j]
    return pd.DataFrame({"label": labels, "exit_pos": exits, "ret": rets}, index=close.index)


def purged_kfold(
    n_samples: int, n_splits: int = 5, horizon: int = 10, embargo: int = 5, exit_pos: np.ndarray | None = None
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """K-fold over contiguous blocks with purging and an embargo.

    Sample i's label spans positions [i, exit_pos[i]] (default i + horizon).
    Training samples whose span overlaps the test span are purged, and the
    ``embargo`` samples immediately after the test span are dropped too.
    """
    idx = np.arange(n_samples)
    ends = idx + horizon if exit_pos is None else np.asarray(exit_pos, dtype=float)
    for test in np.array_split(idx, n_splits):
        a = test[0]
        test_end = np.nanmax(ends[test])
        overlaps = (idx <= test_end) & (ends >= a)
        embargoed = (idx > test_end) & (idx <= test_end + embargo)
        train = idx[~overlaps & ~embargoed]
        yield train, test


def walk_forward_splits(
    n_samples: int, train_size: int, test_size: int, gap: int = 10, expanding: bool = True
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Train on the past, test on the next block. ``gap`` ≥ label horizon avoids leakage."""
    start = train_size + gap
    while start + test_size <= n_samples:
        train_end = start - gap
        train_start = 0 if expanding else train_end - train_size
        yield np.arange(train_start, train_end), np.arange(start, start + test_size)
        start += test_size


def out_of_fold_proba(
    make_model: Callable[[], object], X: pd.DataFrame, y: pd.Series, splits
) -> pd.Series:
    """Probability of the positive class for every sample that lands in a test fold."""
    proba = pd.Series(np.nan, index=X.index)
    for train, test in splits:
        if len(train) == 0 or len(np.unique(y.iloc[train])) < 2:
            continue
        model = make_model()
        model.fit(X.iloc[train], y.iloc[train])
        proba.iloc[test] = model.predict_proba(X.iloc[test])[:, 1]
    return proba


def proba_to_position(proba: pd.Series, threshold: float = 0.55) -> pd.Series:
    """Long above ``threshold``, short below 1 − threshold, flat otherwise."""
    pos = pd.Series(0.0, index=proba.index)
    pos[proba > threshold] = 1.0
    pos[proba < 1 - threshold] = -1.0
    return pos
