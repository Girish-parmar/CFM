"""Signal generators for the classic strategy families in Module 7.

Every function returns a *target position* series (+1 long, −1 short, 0 flat)
computed from information available at the close of each bar. The backtester
shifts positions by one bar before applying returns, so no look-ahead occurs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import rolling_zscore, rsi, sma


def sma_crossover(close: pd.Series, fast: int = 20, slow: int = 50, allow_short: bool = False) -> pd.Series:
    """Trend following: long when the fast average is above the slow one."""
    if fast >= slow:
        raise ValueError("fast window must be shorter than slow window")
    f, s = sma(close, fast), sma(close, slow)
    pos = pd.Series(np.where(f > s, 1.0, -1.0 if allow_short else 0.0), index=close.index)
    return pos.where(s.notna(), 0.0)


def time_series_momentum(close: pd.Series, lookback: int = 126, allow_short: bool = True) -> pd.Series:
    """Moskowitz, Ooi & Pedersen (2012): trade the sign of the trailing return."""
    past = close.pct_change(lookback)
    pos = np.sign(past)
    if not allow_short:
        pos = pos.clip(lower=0.0)
    return pos.fillna(0.0)


def bollinger_mean_reversion(
    close: pd.Series, window: int = 20, entry_z: float = 2.0, exit_z: float = 0.5
) -> pd.Series:
    """Fade stretched moves: short above +entry_z, long below −entry_z,
    flatten once |z| falls back under ``exit_z``."""
    z = rolling_zscore(close, window)
    return _band_positions(z, entry_z, exit_z)


def rsi_reversal(close: pd.Series, period: int = 14, low: float = 30, high: float = 70) -> pd.Series:
    """Long when RSI is oversold, short when overbought, flat in between."""
    r = rsi(close, period)
    pos = pd.Series(0.0, index=close.index)
    pos[r < low] = 1.0
    pos[r > high] = -1.0
    return pos


def hedge_ratio(y: pd.Series, x: pd.Series) -> tuple[float, float]:
    """OLS of y on x. Returns (beta, alpha)."""
    beta, alpha = np.polyfit(x.to_numpy(dtype=float), y.to_numpy(dtype=float), 1)
    return float(beta), float(alpha)


def rolling_hedge_ratio(y: pd.Series, x: pd.Series, window: int = 60) -> pd.Series:
    """Rolling OLS beta so the pair can be traded without look-ahead."""
    cov = y.rolling(window).cov(x)
    var = x.rolling(window).var()
    return cov / var


def pairs_signals(
    y: pd.Series,
    x: pd.Series,
    formation: int = 250,
    window: int = 30,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    beta_window: int | None = None,
) -> pd.DataFrame:
    """Statistical-arbitrage pair on the spread y − beta·x.

    Gatev, Goetzmann & Rouwenhorst (2006) style: estimate the hedge ratio by
    OLS on the first ``formation`` bars, then trade only after them. Pass
    ``beta_window`` to re-estimate beta on a rolling window instead (noisier).
    Short the spread (−1 y, +beta x) when z > entry, long it when z < −entry.
    Returns positions per leg (units of y and x), the z-score and beta.
    """
    if beta_window:
        beta = rolling_hedge_ratio(y, x, beta_window)
    else:
        b, _ = hedge_ratio(y.iloc[:formation], x.iloc[:formation])
        beta = pd.Series(b, index=y.index)
    spread = y - beta * x
    z = rolling_zscore(spread, window)
    z_trading = z.copy()
    z_trading.iloc[:formation] = np.nan   # no positions (or carried state) from the formation period
    spread_pos = _band_positions(z_trading, entry_z, exit_z)
    return pd.DataFrame(
        {"y": spread_pos, "x": -spread_pos * beta.fillna(0.0), "zscore": z, "beta": beta},
        index=y.index,
    )


def cross_sectional_momentum(prices: pd.DataFrame, lookback: int = 126, skip: int = 21, top_n: int = 3) -> pd.DataFrame:
    """Jegadeesh & Titman style: each day hold the ``top_n`` best performers over
    ``lookback`` days, skipping the most recent ``skip`` days. Equal weights."""
    score = prices.shift(skip) / prices.shift(lookback) - 1.0
    ranks = score.rank(axis=1, ascending=False)
    weights = (ranks <= top_n).astype(float)
    weights = weights.div(weights.sum(axis=1).replace(0.0, np.nan), axis=0)
    return weights.fillna(0.0)


def _band_positions(z: pd.Series, entry: float, exit_: float) -> pd.Series:
    """Stateful entry/exit bands shared by the mean-reversion strategies."""
    pos = np.zeros(len(z))
    current = 0.0
    for i, value in enumerate(z.to_numpy()):
        if np.isnan(value):
            current = 0.0
        elif current == 0.0:
            if value > entry:
                current = -1.0
            elif value < -entry:
                current = 1.0
        elif abs(value) < exit_:
            current = 0.0
        pos[i] = current
    return pd.Series(pos, index=z.index)
