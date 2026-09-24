"""Time-series econometrics for trading (M13, M23).

kalman    Kalman-filter hedge ratio and pairs signals
garch     GARCH(1,1) fit, causal forecasts, volatility targeting
regimes   two-state Markov-switching regimes (filtered and smoothed)
"""

from .garch import (
    garch11_fit,
    garch11_forecast,
    vol_target_weights,
)
from .kalman import (
    kalman_hedge,
    kalman_pairs_signals,
)
from .regimes import (
    fit_markov_regimes,
    markov_regime_probabilities,
)

__all__ = [
    "fit_markov_regimes",
    "garch11_fit",
    "garch11_forecast",
    "kalman_hedge",
    "kalman_pairs_signals",
    "markov_regime_probabilities",
    "vol_target_weights",
]
