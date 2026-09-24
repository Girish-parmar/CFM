"""cfmat — course library for the Certificate in Financial Market and Algorithmic Trading.

Subpackages (course modules in brackets; see docs/REPO_MAP.md for the full map):

    data            synthetic generators with planted effects, loaders, packaged sample data   [M03, M05]
    analytics       metrics, technical indicators, candlestick and chart patterns               [M04, M06]
    derivatives     option pricing and Greeks, futures curves, option-structure backtests       [M08, M09]
    strategies      classic signal functions; the rule language, specs and templates            [M10, M12]
    backtesting     vectorised, event-driven and rule engines; optimisers; reports              [M11, M12]
    research        screener and segment (day/month/regime/pattern) analysis                     [M12, M23]
    portfolio       risk (VaR/ES, sizing, stress) and portfolio construction                     [M13, M14]
    microstructure  order book, execution schedules, impact, TCA, Indian statutory costs        [M01, M15]
    trading         orders, pre-trade risk checks, paper broker, journal                         [M17]
    automation      signal service and SQLite journal for n8n                                    [M18]
    ml              features, labels, purged CV, sizing, boosting/HPO, reinforcement learning    [M19-M21, M23]
    nlp             sentiment, retrieval-augmented generation, optional Claude answer step       [M22]
    econometrics    GARCH, Markov regimes, Kalman-filter pairs                                  [M13, M23]
    infra           parallel map, filesystem paths, chart saving

``cfmat.studio`` gathers the Strategy Creator workflow (rules, specs, templates,
backtest, optimisers) in one namespace.

Everything is written for teaching: small, readable and tested. It is not a
production trading system.
"""

__version__ = "2.0.0"
