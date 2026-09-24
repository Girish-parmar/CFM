"""Strategies as code and as data (Modules 10, 12).

The package namespace re-exports the classic signal generators from ``signals``
(``from cfmat import strategies; strategies.sma_crossover(...)``).

    signals      vectorised signal functions: crossovers, momentum, mean reversion, pairs
    rules        the Strategy Creator's rule language (safe ``ast`` evaluator)
    spec         ``StrategySpec``: a strategy as data, with JSON round-trip
    templates    library of ready-made ``StrategySpec`` strategies
"""

from . import rules, signals, spec, templates
from .signals import (
    bollinger_mean_reversion,
    cross_sectional_momentum,
    hedge_ratio,
    pairs_signals,
    rolling_hedge_ratio,
    rsi_reversal,
    short_term_signal,
    sma_crossover,
    time_series_momentum,
)

__all__ = [
    "bollinger_mean_reversion",
    "cross_sectional_momentum",
    "hedge_ratio",
    "pairs_signals",
    "rolling_hedge_ratio",
    "rsi_reversal",
    "rules",
    "short_term_signal",
    "signals",
    "sma_crossover",
    "spec",
    "templates",
    "time_series_momentum",
]
