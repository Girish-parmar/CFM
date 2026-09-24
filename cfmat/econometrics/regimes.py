"""Two-state Markov-switching regimes: fit on a training window, then filter
(no look-ahead) or smooth (look-ahead, for description only) (Module 23).
"""

from __future__ import annotations

import inspect
import warnings

import numpy as np
import pandas as pd

from ..analytics.metrics import TRADING_DAYS


def fit_markov_regimes(train_returns: pd.Series, seed: int = 0) -> pd.Series:
    """Fit a two-regime Markov-switching model (switching mean and variance)
    on a training period. Returns the parameter vector."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    model = MarkovRegression(train_returns.dropna() * 100.0, k_regimes=2, trend="c", switching_variance=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # search_reps draws random starting values. statsmodels >= 0.15 takes an explicit
        # ``rng``; older versions use NumPy's global state, which we seed and then restore
        # so that calling this function never changes the caller's random stream.
        if "rng" in inspect.signature(model.fit).parameters:
            return model.fit(search_reps=20, disp=False, rng=seed).params
        state = np.random.get_state()  # noqa: NPY002
        try:
            np.random.seed(seed)  # noqa: NPY002 - only way to seed statsmodels < 0.15
            return model.fit(search_reps=20, disp=False).params
        finally:
            np.random.set_state(state)  # noqa: NPY002


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
