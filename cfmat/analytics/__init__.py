"""Market analytics: returns and performance metrics, technical indicators,
candlestick and chart patterns, statistical tests and factor tools (M04, M06, M07).

    metrics      returns, Sharpe/Sortino/Calmar, drawdowns, PSR and deflated Sharpe
    indicators   SMA/EMA/RSI/MACD/Bollinger/ATR, ADX, Supertrend, Donchian, Hurst ...
    patterns     15 candlestick patterns, swing structure, double tops/bottoms, squeezes
    stats        HAC t-statistics, Benjamini-Hochberg q-values, event studies
    factors      cross-sectional factor tools: winsorise, z-score, neutralise, IC, quantiles
"""

from . import factors, indicators, metrics, patterns, stats

__all__ = ["factors", "indicators", "metrics", "patterns", "stats"]
