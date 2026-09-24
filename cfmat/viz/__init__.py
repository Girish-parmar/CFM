"""Charts for research, backtests and trading reviews (M06, M10, M11, M14, M17).

price        candles or line with overlays, trade and pattern markers, volume, indicator panels
performance  equity and drawdown, monthly heatmap, rolling metrics, return distribution, trade review
analysis     correlation heatmap, volatility estimators and cone, rankings, rotation graph, frontier

Every function returns a matplotlib figure. Save it with ``savefig(fig, name)``,
which writes ``<output dir>/<name>.png`` and closes the figure. Importing this
package selects a non-interactive backend outside notebooks.
"""

from ..infra.plotting import savefig
from .analysis import (
    cone_chart,
    correlation_heatmap,
    frontier_chart,
    ranking_chart,
    rotation_chart,
    volatility_chart,
)
from .performance import (
    distribution_chart,
    equity_chart,
    monthly_heatmap,
    rolling_chart,
    trade_chart,
)
from .price import (
    candlestick,
    price_chart,
)

__all__ = [
    "candlestick",
    "cone_chart",
    "correlation_heatmap",
    "distribution_chart",
    "equity_chart",
    "frontier_chart",
    "monthly_heatmap",
    "price_chart",
    "ranking_chart",
    "rolling_chart",
    "rotation_chart",
    "savefig",
    "trade_chart",
    "volatility_chart",
]
