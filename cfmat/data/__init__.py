"""Market data (M03, M05, M16).

synthetic  reproducible generators with documented, planted properties
loaders    CSV and Yahoo Finance loaders; one standard OHLCV shape and data-quality checks
providers  historical bars from Alpaca (US) and Interactive Brokers (NSE, US, global)
handler    ticks to bars, tick validation, instrument master, continuous futures, storage, replay
fetch      command line: python -m cfmat.data.fetch {yahoo,alpaca,ibkr} SYMBOL ... → data/<SYMBOL>.csv
samples/   fictional headlines and filings used by the NLP labs (package data)
"""

from .loaders import (
    OHLCV,
    download_prices,
    load_ohlcv_csv,
    ohlcv_problems,
    standardize_ohlcv,
)
from .providers import (
    alpaca_bars,
    ibkr_bars,
)
from .synthetic import (
    ARCHETYPES,
    MACRO_MATURITIES,
    SECTORS,
    MacroData,
    ar1_prices,
    brownian_ohlc,
    cointegrated_pair,
    drifting_pair,
    factor_panel,
    futures_chain,
    garch_prices,
    gbm_prices,
    implied_vol_series,
    instrument_universe,
    intraday_volume_profile,
    macro_calendar,
    news_stream,
    ohlcv,
    ohlcv_from_close,
    regime_prices,
    seasonal_prices,
    tick_stream,
    trading_days,
    universe,
)

__all__ = [
    "ARCHETYPES",
    "MACRO_MATURITIES",
    "OHLCV",
    "SECTORS",
    "MacroData",
    "alpaca_bars",
    "ar1_prices",
    "brownian_ohlc",
    "cointegrated_pair",
    "download_prices",
    "drifting_pair",
    "factor_panel",
    "futures_chain",
    "garch_prices",
    "gbm_prices",
    "ibkr_bars",
    "implied_vol_series",
    "instrument_universe",
    "intraday_volume_profile",
    "load_ohlcv_csv",
    "macro_calendar",
    "news_stream",
    "ohlcv",
    "ohlcv_from_close",
    "ohlcv_problems",
    "regime_prices",
    "seasonal_prices",
    "standardize_ohlcv",
    "tick_stream",
    "trading_days",
    "universe",
]
