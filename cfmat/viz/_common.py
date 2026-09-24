"""Shared chart styling and helpers for cfmat.viz."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..infra.plotting import plt

UP, DOWN, NEUTRAL = "#2e7d32", "#c62828", "#455a64"
ACCENT = ("#1565c0", "#ef6c00", "#6a1b9a", "#00838f", "#9e9d24", "#ad1457")
GRID = {"alpha": 0.25, "linewidth": 0.6}


def figure(nrows: int = 1, ncols: int = 1, **kwargs):
    """``plt.subplots`` with the house grid on every axis."""
    fig, axes = plt.subplots(nrows, ncols, **kwargs)
    for ax in np.atleast_1d(axes).ravel():
        ax.grid(True, **GRID)
    return fig, axes


def bar_positions(index: pd.Index, times) -> np.ndarray:
    """Integer bar position containing each time (the last bar starting at or before it); -1 if before the data."""
    return index.searchsorted(pd.DatetimeIndex(pd.to_datetime(times)), side="right") - 1


def date_ticks(ax, index: pd.Index, n: int = 8) -> None:
    """Label integer x positions 0..len-1 with their dates (bars are drawn on positions to skip closed days)."""
    if len(index) == 0:
        return
    positions = np.arange(0, len(index), max(1, len(index) // n))
    intraday = isinstance(index, pd.DatetimeIndex) and bool((index != index.normalize()).any())
    fmt = "%d %b %H:%M" if intraday else "%d %b %y"
    ax.set_xticks(positions)
    ax.set_xticklabels([pd.Timestamp(index[i]).strftime(fmt) if isinstance(index, pd.DatetimeIndex)
                        else str(index[i]) for i in positions], fontsize=8)
