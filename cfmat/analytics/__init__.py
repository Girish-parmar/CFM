"""Market analytics: returns and performance, indicators, patterns, momentum and volatility,
relative performance, statistical tests and factor tools (M04, M06, M07, M10, M11).

    metrics      returns, Sharpe/Sortino/Calmar, drawdowns, PSR and deflated Sharpe
    performance  tearsheet, drawdown periods, rolling metrics, monthly and annual tables
    indicators   SMA/EMA/RSI/MACD/Bollinger/ATR, ADX, Supertrend, Donchian, Hurst ...
    patterns     15 candlestick patterns, swing structure, double tops/bottoms, squeezes
    momentum     12-1, risk-adjusted and regression momentum, TSMOM, dual momentum, ranks
    volatility   Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang, EWMA, cones, regimes
    relative     CAPM alpha/beta, rolling beta, relative strength, RS rating, rotation (RRG)
    stats        HAC t-statistics, Benjamini-Hochberg q-values, event studies
    factors      cross-sectional factor tools: winsorise, z-score, neutralise, IC, quantiles
"""

from . import factors, indicators, metrics, momentum, patterns, performance, relative, stats, volatility

__all__ = ["factors", "indicators", "metrics", "momentum", "patterns", "performance", "relative", "stats",
           "volatility"]
