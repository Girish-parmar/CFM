"""Validation for overlapping financial labels: purged K-fold with embargo,
walk-forward splits and out-of-fold predictions (M19).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import numpy as np
import pandas as pd


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
