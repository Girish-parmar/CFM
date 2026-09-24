"""Market analytics: returns and performance metrics, technical indicators,
candlestick and chart patterns (Modules 4, 6).

    metrics      returns, Sharpe/Sortino/Calmar, drawdowns, PSR and deflated Sharpe
    indicators   SMA/EMA/RSI/MACD/Bollinger/ATR, ADX, Supertrend, Donchian, Hurst ...
    patterns     15 candlestick patterns, swing structure, double tops/bottoms, squeezes
"""

from . import indicators, metrics, patterns

__all__ = [
    "indicators",
    "metrics",
    "patterns",
]
