"""Advanced strategy building blocks (Module 16).

* ``kalman_hedge`` / ``kalman_pairs_signals``: pairs trading with a hedge
  ratio that adapts over time (Kalman filter; Chan, 2013, ch. 3).
* ``garch11_fit`` / ``garch11_forecast`` / ``vol_target_weights``: forecast
  tomorrow's volatility with GARCH(1,1) and size positions to a volatility target
  (volatility-managed portfolios; Moreira & Muir, 2017).
* ``fit_markov_regimes`` / ``markov_regime_probabilities``: probability of a
  turbulent regime from a two-state Markov-switching model, *filtered* so it
  uses only past data.

Every function is causal: the value at bar t uses information up to bar t, so a
position decided at t's close can be backtested on t+1's return.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .strategies import _band_positions

TRADING_DAYS = 252


# ---------------------------------------------------------------------------
# Kalman-filter pairs trading
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GARCH(1,1) volatility forecasting
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Markov-switching regimes
# ---------------------------------------------------------------------------

def fit_markov_regimes(train_returns: pd.Series, seed: int = 0) -> pd.Series:
    """Fit a two-regime Markov-switching model (switching mean and variance)
    on a training period. Returns the parameter vector."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        np.random.seed(seed)  # statsmodels' search_reps draws random starting values
        model = MarkovRegression(train_returns.dropna() * 100.0, k_regimes=2, trend="c", switching_variance=True)
        return model.fit(search_reps=20, disp=False).params


def markov_regime_probabilities(returns: pd.Series, params: pd.Series, smoothed: bool = False) -> pd.DataFrame:
    """Probability of the high-volatility regime at each bar, with fixed ``params``.

    The default runs the Hamilton *filter*: the probability at t uses returns up
    to t only, so it can drive trading. ``smoothed=True`` runs the Kim smoother,
    which uses the whole sample: fine for describing history, look-ahead for
    trading.
    """
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    scaled = returns.dropna() * 100.0
    model = MarkovRegression(scaled, k_regimes=2, trend="c", switching_variance=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.smooth(params) if smoothed else model.filter(params)
    probs = result.smoothed_marginal_probabilities if smoothed else result.filtered_marginal_probabilities
    probs = pd.DataFrame(np.asarray(probs), index=scaled.index)
    variances = [params[f"sigma2[{k}]"] for k in range(2)]
    high = int(np.argmax(variances))
    return pd.DataFrame({
        "p_turbulent": probs[high],
        "vol_calm": np.sqrt(min(variances) * TRADING_DAYS) / 100.0,
        "vol_turbulent": np.sqrt(max(variances) * TRADING_DAYS) / 100.0,
    }, index=scaled.index)
