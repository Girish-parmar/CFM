"""Momentum measures: time-series, cross-sectional and trend quality (M10, M12).

Every score at date t uses prices up to t only; trade on it from t + 1.

    momentum                 return from ``lookback`` to ``skip`` days ago (12-1 by default)
    risk_adjusted_momentum   the same log return divided by its volatility (a t-statistic)
    regression_momentum      annualised exponential-regression slope x R² (trend quality)
    information_discreteness sign(return) x (%down days − %up days): smooth vs jumpy trends
    acceleration             change in momentum over the last ``window`` days
    tsmom_position           sign of past return scaled to a volatility target
    cross_sectional_rank     rank of each asset's score among its peers on each date
    dual_momentum_weights    top-N by relative momentum, only if absolute momentum is positive
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import TRADING_DAYS

Frame = pd.Series | pd.DataFrame


def momentum(close: Frame, lookback: int = 252, skip: int = 21) -> Frame:
    """Simple return from ``lookback`` days ago to ``skip`` days ago.

    Skipping the most recent month (``skip=21``) avoids the short-term reversal
    that otherwise contaminates 12-month momentum.
    """
    if not 0 <= skip < lookback:
        raise ValueError("need 0 <= skip < lookback")
    return close.shift(skip) / close.shift(lookback) - 1.0


def risk_adjusted_momentum(close: Frame, lookback: int = 252, skip: int = 21) -> Frame:
    """Log return over the momentum window divided by σ·√n over the same window.

    Ranks a steady climber above a stock that got the same return in one jump.
    """
    logp = np.log(close.astype(float))
    n = lookback - skip
    ret = logp.shift(skip) - logp.shift(lookback)
    vol = logp.diff().rolling(n).std().shift(skip)
    return ret / (vol * np.sqrt(n))


def _slope_r2(logp: pd.Series, window: int) -> tuple[pd.Series, pd.Series]:
    t = pd.Series(np.arange(len(logp), dtype=float), index=logp.index)
    slope = logp.rolling(window).cov(t) / t.rolling(window).var()
    r2 = logp.rolling(window).corr(t) ** 2
    return slope, r2


def regression_momentum(close: Frame, window: int = 90, periods: int = TRADING_DAYS) -> Frame:
    """Annualised slope of a regression of log price on time, times the fit's R².

    High scores need both a steep and a smooth trend (Clenow's momentum score).
    """
    def one(s: pd.Series) -> pd.Series:
        slope, r2 = _slope_r2(np.log(s.astype(float)), window)
        return (np.exp(slope * periods) - 1.0) * r2

    return close.apply(one) if isinstance(close, pd.DataFrame) else one(close)


def information_discreteness(close: Frame, lookback: int = 252) -> Frame:
    """sign(return) × (share of down days − share of up days) over ``lookback`` (Da, Gurun, Warachka 2014).

    Negative values mean the move came in many small steps ("frog in the pan"),
    which the paper finds persists better than momentum from a few big jumps.
    """
    r = close.pct_change()
    up = (r > 0).astype(float).rolling(lookback).mean()
    down = (r < 0).astype(float).rolling(lookback).mean()
    total = close / close.shift(lookback) - 1.0
    return np.sign(total) * (down - up)


def acceleration(close: Frame, window: int = 63) -> Frame:
    """Momentum over the last ``window`` days minus momentum over the ``window`` before it."""
    recent = close / close.shift(window) - 1.0
    return recent - recent.shift(window)


def tsmom_position(
    close: Frame,
    lookback: int = 252,
    target_vol: float = 0.15,
    vol_window: int = 63,
    max_leverage: float = 2.0,
    periods: int = TRADING_DAYS,
) -> Frame:
    """Time-series momentum (Moskowitz, Ooi, Pedersen 2012): long after gains, short after losses.

    Position = sign(return over ``lookback``) × ``target_vol`` / realised
    volatility, capped at ``max_leverage``. Apply it to the next day's return.
    """
    direction = np.sign(close / close.shift(lookback) - 1.0)
    vol = np.log(close.astype(float)).diff().rolling(vol_window).std() * np.sqrt(periods)
    leverage = (target_vol / vol).clip(upper=max_leverage)
    return direction * leverage


def cross_sectional_rank(scores: pd.DataFrame, pct: bool = True) -> pd.DataFrame:
    """Rank each column's score among all columns on each date (1 = best when ``pct`` is False)."""
    return scores.rank(axis=1, pct=pct, ascending=pct)


def dual_momentum_weights(
    close: pd.DataFrame,
    lookback: int = 252,
    skip: int = 21,
    top_n: int = 3,
    absolute_threshold: float = 0.0,
) -> pd.DataFrame:
    """Equal weights in the ``top_n`` assets by momentum whose momentum also beats ``absolute_threshold``.

    Relative momentum picks the leaders; absolute momentum moves the slot to
    cash (weight 0) when even a leader is falling (Antonacci's dual momentum).
    Rows before enough history are all zero.
    """
    score = momentum(close, lookback, skip)
    rank = score.rank(axis=1, ascending=False)
    chosen = (rank <= top_n) & (score > absolute_threshold)
    return chosen.astype(float) / top_n
