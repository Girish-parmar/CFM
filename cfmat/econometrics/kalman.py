"""Kalman-filter hedge ratios and pairs signals (Module 23; Chan, 2013, ch. 3).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..strategies.signals import _band_positions


def kalman_hedge(
    y: pd.Series,
    x: pd.Series,
    delta: float = 1e-6,
    obs_var: float = 10.0,
    prior_var: tuple[float, float] = (1.0, 1e4),
) -> pd.DataFrame:
    """Track y_t = beta_t · x_t + alpha_t + noise with a Kalman filter.

    The state (beta, alpha) follows a random walk whose variance is set by
    ``delta`` (larger = adapts faster, noisier); ``obs_var`` is the variance of
    the spread around the fitted line. ``prior_var`` is the starting uncertainty
    of (beta, alpha): it must be wide, or the filter spends years dragging an
    intercept that started at zero. Returns, per bar: ``beta`` and ``alpha``
    (updated with bar t), ``error`` (y_t minus the prediction made *before*
    seeing y_t) and ``error_std`` (its predicted standard deviation).
    """
    ys, xs = y.to_numpy(dtype=float), x.to_numpy(dtype=float)
    n = len(ys)
    theta = np.zeros(2)
    P = np.diag(np.asarray(prior_var, dtype=float))
    Vw = delta / (1 - delta) * np.eye(2)
    out = np.zeros((n, 4))
    for t in range(n):
        H = np.array([xs[t], 1.0])
        R = P + Vw                              # predict: state uncertainty grows
        e = ys[t] - H @ theta                   # forecast error with yesterday's state
        Q = H @ R @ H + obs_var                 # its predicted variance
        K = R @ H / Q                           # Kalman gain
        theta = theta + K * e                   # update with today's observation
        P = R - np.outer(K, H) @ R
        out[t] = (theta[0], theta[1], e, np.sqrt(Q))
    return pd.DataFrame(out, index=y.index, columns=["beta", "alpha", "error", "error_std"])


def kalman_pairs_signals(
    y: pd.Series,
    x: pd.Series,
    delta: float = 1e-6,
    obs_var: float = 10.0,
    entry_z: float = 1.5,
    exit_z: float = 0.25,
    warmup: int = 60,
) -> pd.DataFrame:
    """Trade the Kalman forecast error: short the spread when y is rich
    (error > entry·std), long when cheap, flat once the error normalises.

    Output columns match ``strategies.pairs_signals`` so it plugs into
    ``backtest.pairs_backtest``.
    """
    k = kalman_hedge(y, x, delta, obs_var)
    z = k["error"] / k["error_std"]
    z_trading = z.copy()
    z_trading.iloc[:warmup] = np.nan          # let the filter converge before trading
    spread_pos = _band_positions(z_trading, entry_z, exit_z)
    return pd.DataFrame({"y": spread_pos, "x": -spread_pos * k["beta"], "zscore": z, "beta": k["beta"]}, index=y.index)
