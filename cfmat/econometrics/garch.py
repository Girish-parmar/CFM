"""GARCH(1,1) volatility: maximum-likelihood fit, causal forecast and volatility-target
weights (Modules 13, 23).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from ..analytics.metrics import TRADING_DAYS


def _garch_variance(eps: np.ndarray, omega: float, alpha: float, beta: float, init: float) -> np.ndarray:
    var = np.empty(len(eps) + 1)
    var[0] = init
    for t in range(len(eps)):
        var[t + 1] = omega + alpha * eps[t] ** 2 + beta * var[t]
    return var  # var[t] = variance for eps[t]; var[-1] = forecast for the next period


def garch11_fit(returns: pd.Series) -> dict[str, float]:
    """Maximum-likelihood GARCH(1,1) with a constant mean (Gaussian errors).

    Returns ``mu``, ``omega``, ``alpha``, ``beta`` for daily returns plus the
    log-likelihood and the implied long-run annual volatility.
    """
    r = returns.dropna().to_numpy(dtype=float) * 100.0          # percent units for numerical stability
    mu = r.mean()
    eps = r - mu
    init = eps.var()

    def nll(p: np.ndarray) -> float:
        omega, alpha, beta = p
        var = _garch_variance(eps, omega, alpha, beta, init)[:-1]
        return 0.5 * float(np.sum(np.log(2 * np.pi) + np.log(var) + eps**2 / var))

    res = minimize(nll, x0=np.array([0.05 * init, 0.05, 0.90]), method="SLSQP",
                   bounds=[(1e-8, 10 * init), (0.0, 0.5), (0.0, 0.999)],
                   constraints=[{"type": "ineq", "fun": lambda p: 0.999 - p[1] - p[2]}])
    omega, alpha, beta = res.x
    long_run = omega / (1 - alpha - beta)
    return {"mu": mu / 100.0, "omega": omega / 1e4, "alpha": float(alpha), "beta": float(beta),
            "loglik": -float(res.fun), "long_run_vol": float(np.sqrt(long_run * TRADING_DAYS) / 100.0)}


def garch11_forecast(returns: pd.Series, params: dict[str, float]) -> pd.Series:
    """One-step-ahead volatility forecast (daily) known at each bar's close.

    Uses fixed ``params`` (fit them on a training period only).
    """
    r = returns.fillna(0.0).to_numpy(dtype=float)
    eps = r - params["mu"]
    init = params["omega"] / max(1e-12, 1 - params["alpha"] - params["beta"])
    var = _garch_variance(eps, params["omega"], params["alpha"], params["beta"], init)[1:]
    return pd.Series(np.sqrt(var), index=returns.index, name="garch_vol")


def vol_target_weights(daily_vol_forecast: pd.Series, target_vol: float = 0.12, max_leverage: float = 2.0) -> pd.Series:
    """Exposure that targets ``target_vol`` (annual) given a daily vol forecast."""
    annual = daily_vol_forecast * np.sqrt(TRADING_DAYS)
    return (target_vol / annual).clip(upper=max_leverage).fillna(0.0)
