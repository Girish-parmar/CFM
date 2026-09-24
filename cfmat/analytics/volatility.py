"""Volatility estimators, cones and regimes (M10, M13).

Range-based estimators use the day's open, high and low as well as the close,
so they extract more information per day than close-to-close volatility:

    close_to_close   standard deviation of daily log returns
    parkinson        high-low range; about 5x as efficient, but ignores gaps and drift
    garman_klass     range plus open-to-close; ignores overnight gaps
    rogers_satchell  unbiased under drift; ignores gaps
    yang_zhang       overnight + open-to-close + Rogers-Satchell: handles gaps and drift

All return annualised volatility over a rolling ``window`` of daily bars. Real
data breaks their assumptions in known ways: discrete trading makes the observed
range too small (a downward bias), and jumps inflate every estimator.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .indicators import atr, rolling_volatility
from .metrics import TRADING_DAYS


def _logs(ohlc: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    o, h, lo, c = (np.log(ohlc[k].astype(float)) for k in ("open", "high", "low", "close"))
    return o, h, lo, c


def close_to_close(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.Series:
    """Annualised standard deviation of daily log close-to-close returns."""
    return rolling_volatility(ohlc["close"], window, periods)


def parkinson(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.Series:
    """Parkinson (1980): σ² = mean[(ln H/L)²] / (4 ln 2)."""
    _, h, lo, _ = _logs(ohlc)
    daily = (h - lo) ** 2 / (4.0 * np.log(2.0))
    return np.sqrt(daily.rolling(window).mean() * periods)


def garman_klass(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.Series:
    """Garman–Klass (1980): σ² = mean[½(ln H/L)² − (2 ln 2 − 1)(ln C/O)²]."""
    o, h, lo, c = _logs(ohlc)
    daily = 0.5 * (h - lo) ** 2 - (2.0 * np.log(2.0) - 1.0) * (c - o) ** 2
    return np.sqrt(daily.rolling(window).mean().clip(lower=0) * periods)


def rogers_satchell(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.Series:
    """Rogers–Satchell (1991): σ² = mean[ln(H/C)·ln(H/O) + ln(L/C)·ln(L/O)]; drift-independent."""
    o, h, lo, c = _logs(ohlc)
    daily = (h - c) * (h - o) + (lo - c) * (lo - o)
    return np.sqrt(daily.rolling(window).mean().clip(lower=0) * periods)


def yang_zhang(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.Series:
    """Yang–Zhang (2000): σ² = σ²_overnight + k·σ²_open-to-close + (1 − k)·σ²_RS.

    k = 0.34 / (1.34 + (n + 1)/(n − 1)) minimises the estimator's variance.
    """
    o, h, lo, c = _logs(ohlc)
    overnight = (o - c.shift(1)).rolling(window).var()
    open_close = (c - o).rolling(window).var()
    rs = ((h - c) * (h - o) + (lo - c) * (lo - o)).rolling(window).mean()
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    return np.sqrt((overnight + k * open_close + (1 - k) * rs).clip(lower=0) * periods)


ESTIMATORS = {
    "close_to_close": close_to_close,
    "parkinson": parkinson,
    "garman_klass": garman_klass,
    "rogers_satchell": rogers_satchell,
    "yang_zhang": yang_zhang,
}


def compare_estimators(ohlc: pd.DataFrame, window: int = 21, periods: int = TRADING_DAYS) -> pd.DataFrame:
    """Every range estimator side by side, one column each."""
    return pd.DataFrame({name: f(ohlc, window, periods) for name, f in ESTIMATORS.items()})


def ewma_volatility(close: pd.Series, lam: float = 0.94, periods: int = TRADING_DAYS) -> pd.Series:
    """RiskMetrics EWMA: σ²_t = λ·σ²_{t−1} + (1 − λ)·r²_t (zero-mean log returns).

    The value at t uses the return of day t, so it is the forecast for day t + 1.
    """
    if not 0 < lam < 1:
        raise ValueError("lam must be between 0 and 1")
    r2 = np.log(close.astype(float)).diff() ** 2
    return np.sqrt(r2.ewm(alpha=1 - lam, adjust=False).mean() * periods)


def atr_percent(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average true range as a percentage of the close (normalised ATR), comparable across prices."""
    return 100 * atr(ohlc, period) / ohlc["close"]


def volatility_cone(
    close: pd.Series,
    windows: tuple[int, ...] = (10, 21, 63, 126, 252),
    quantiles: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0),
    periods: int = TRADING_DAYS,
) -> pd.DataFrame:
    """Distribution of realised volatility for each window length, with today's value.

    Rows are windows; columns are the quantiles (``min``, ``q25``, ``median``,
    ``q75``, ``max`` for the defaults) and ``current``. Windows overlap, so the
    long-window quantiles rest on few independent observations.
    """
    names = {0.0: "min", 0.5: "median", 1.0: "max"}
    rows = {}
    for w in windows:
        vol = rolling_volatility(close, w, periods).dropna()
        row = {names.get(q, f"q{round(q * 100)}"): float(vol.quantile(q)) for q in quantiles}
        row["current"] = float(vol.iloc[-1]) if len(vol) else np.nan
        rows[w] = row
    table = pd.DataFrame(rows).T
    table.index.name = "window"
    return table


def volatility_percentile(vol: pd.Series, lookback: int = 252) -> pd.Series:
    """Where today's volatility sits within its own trailing ``lookback`` history (0–1)."""
    return vol.rolling(lookback).rank(pct=True)


def volatility_regime(vol: pd.Series, lookback: int = 252, low: float = 0.25, high: float = 0.75) -> pd.Series:
    """Label each day ``low``, ``normal`` or ``high`` from its trailing percentile (no look-ahead).

    Days without a full ``lookback`` of history are left missing. The labels
    adapt: once high volatility has lasted for most of the lookback it becomes
    the norm and is labelled ``normal`` again. Use fixed thresholds instead if
    you need an absolute risk level.
    """
    pct = volatility_percentile(vol, lookback)
    labels = pd.Series(np.where(pct <= low, "low", np.where(pct >= high, "high", "normal")),
                       index=vol.index, dtype=object)
    return labels.where(pct.notna())


def vol_of_vol(vol: pd.Series, window: int = 63) -> pd.Series:
    """Coefficient of variation of volatility over ``window``: how unstable the risk level is."""
    return vol.rolling(window).std() / vol.rolling(window).mean()
