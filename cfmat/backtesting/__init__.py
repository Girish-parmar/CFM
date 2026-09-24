"""Backtesting engines and reports (Modules 11, 12). Costs live in ``cfmat.microstructure.costs``.

vectorized     position x return backtests, grid search, walk-forward (signal functions)
event_driven   bar-by-bar engine with orders, broker and risk checks
rule_engine    trade-level engine for ``StrategySpec`` rules (stops, targets, trailing)
optimize       parallel sweeps, coarse-to-fine, walk-forward for ``StrategySpec``
report         trade statistics, monthly tables, comparisons and charts
"""

from . import event_driven, optimize, report, rule_engine, vectorized

__all__ = [
    "event_driven",
    "optimize",
    "report",
    "rule_engine",
    "vectorized",
]
