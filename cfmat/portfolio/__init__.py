"""Risk measurement and portfolio construction (Modules 13, 14).

The package namespace re-exports the construction methods
(``from cfmat import portfolio; portfolio.hrp_weights(...)``).

    risk          VaR, expected shortfall, VaR backtests, position sizing, Kelly, stress tests
    construction  min-variance, max-Sharpe, risk parity, HRP, rolling strategy allocation
"""

from . import construction, risk
from .construction import (
    allocation_returns,
    efficient_frontier,
    hrp_weights,
    max_sharpe_weights,
    min_variance_weights,
    portfolio_stats,
    risk_contributions,
    risk_parity_weights,
    rolling_allocation,
)

__all__ = [
    "allocation_returns",
    "construction",
    "efficient_frontier",
    "hrp_weights",
    "max_sharpe_weights",
    "min_variance_weights",
    "portfolio_stats",
    "risk",
    "risk_contributions",
    "risk_parity_weights",
    "rolling_allocation",
]
