"""cfmat — course library for the Certificate in Financial Market and Algorithmic Trading.

Each sub-module maps to one or more course modules:

    data        Synthetic and real market data (Modules 2, 4)
    metrics     Returns and performance statistics (Modules 2, 3, 8)
    indicators  Technical indicators (Module 5)
    options     Option pricing, Greeks, implied volatility (Module 6)
    strategies  Signal generators for classic strategies (Module 7)
    backtest    Vectorised backtester and Indian cost model (Module 8)
    engine      Event-driven backtester (Module 8)
    risk        VaR, expected shortfall, position sizing (Module 9)
    portfolio   Portfolio construction (Module 9)
    execution   Order book, TWAP/VWAP, Almgren–Chriss (Module 10)
    broker      Order management, pre-trade risk checks, paper broker (Module 11)
    ml          Features, triple-barrier labels, purged CV (Module 12)
    rl          Tabular Q-learning trading agent (Module 13)
    nlp         Financial sentiment, retrieval and RAG (Module 14)
    signal_server  HTTP endpoint used by the n8n workflows (Module 15)
    plotting    Saves lab charts to labs/output

Everything is written for teaching: small, readable, and tested. It is not a
production trading system.
"""

__version__ = "1.0.0"
