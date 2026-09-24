"""Strategy Studio: one namespace for the Strategy Creator workflow (M12).

``from cfmat import studio`` gives the rule language, strategy specs, the
template library, the trade-level backtester and the optimisers together. The
code lives in:

    cfmat.strategies.rules        rule language (``Evaluator``, ``register``)
    cfmat.strategies.spec         ``StrategySpec``
    cfmat.strategies.templates    ``TEMPLATES``
    cfmat.backtesting.rule_engine ``backtest``, ``BacktestResult``, ``signals``
    cfmat.backtesting.optimize    ``sweep``, ``coarse_to_fine``, ``walk_forward``, ``strategy_matrix``
"""

from .backtesting.optimize import coarse_to_fine, expand_grid, strategy_matrix, sweep, walk_forward
from .backtesting.rule_engine import BacktestResult, backtest, signals
from .strategies.rules import FUNCTIONS, MAX_RULE_LENGTH, PRICE_FIELDS, Evaluator, available_functions, register
from .strategies.spec import StrategySpec
from .strategies.templates import TEMPLATES, templates

__all__ = [
    "FUNCTIONS",
    "MAX_RULE_LENGTH",
    "PRICE_FIELDS",
    "TEMPLATES",
    "BacktestResult",
    "Evaluator",
    "StrategySpec",
    "available_functions",
    "backtest",
    "coarse_to_fine",
    "expand_grid",
    "register",
    "signals",
    "strategy_matrix",
    "sweep",
    "templates",
    "walk_forward",
]
