"""Market data (M03, M05, M16).

synthetic  reproducible generators with documented, planted properties
loaders    CSV and Yahoo Finance loaders; one standard OHLCV shape and data-quality checks
providers  historical bars from Alpaca (US) and Interactive Brokers (NSE, US, global)
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
    SECTORS,
    ar1_prices,
    brownian_ohlc,
    cointegrated_pair,
    drifting_pair,
    factor_panel,
    garch_prices,
    gbm_prices,
    implied_vol_series,
    instrument_universe,
    intraday_volume_profile,
    ohlcv,
    ohlcv_from_close,
    regime_prices,
    seasonal_prices,
    trading_days,
    universe,
)

__all__ = [
    "ARCHETYPES",
    "OHLCV",
    "SECTORS",
    "alpaca_bars",
    "ar1_prices",
    "brownian_ohlc",
    "cointegrated_pair",
    "download_prices",
    "drifting_pair",
    "factor_panel",
    "garch_prices",
    "gbm_prices",
    "ibkr_bars",
    "implied_vol_series",
    "instrument_universe",
    "intraday_volume_profile",
    "load_ohlcv_csv",
    "ohlcv",
    "ohlcv_from_close",
    "ohlcv_problems",
    "regime_prices",
    "seasonal_prices",
    "standardize_ohlcv",
    "trading_days",
    "universe",
]
