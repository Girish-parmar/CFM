"""Market analytics: returns and performance, indicators, patterns, momentum and volatility,
relative performance, statistical tests, factor tools, rates and macro (M02, M04, M06, M07, M10, M11).

    metrics      returns, Sharpe/Sortino/Calmar, drawdowns, PSR and deflated Sharpe
    performance  tearsheet, drawdown periods, rolling metrics, monthly and annual tables
    indicators   SMA/EMA/RSI/MACD/Bollinger/ATR, ADX, Supertrend, Donchian, Hurst ...
    patterns     15 candlestick patterns, swing structure, double tops/bottoms, squeezes
    momentum     12-1, risk-adjusted and regression momentum, TSMOM, dual momentum, ranks
    volatility   Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang, EWMA, cones, regimes
    relative     CAPM alpha/beta, rolling beta, relative strength, RS rating, rotation (RRG)
    stats        HAC t-statistics, Benjamini-Hochberg q-values, event studies
    factors      cross-sectional factor tools: winsorise, z-score, neutralise, IC, quantiles
    rates        bond price, duration and convexity; Nelson-Siegel curve fits; inversion episodes
    macro        release sessions, data vintages and growth x inflation regimes without look-ahead
"""

from . import factors, indicators, macro, metrics, momentum, patterns, performance, rates, relative, stats, volatility

__all__ = ["factors", "indicators", "macro", "metrics", "momentum", "patterns", "performance", "rates", "relative",
           "stats", "volatility"]
