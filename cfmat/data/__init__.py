"""Market data (M03, M05).

synthetic  reproducible generators with documented, planted properties
loaders    CSV and free-API loaders for real data
samples/   fictional headlines and filings used by the NLP labs (package data)
"""

from .loaders import (
    download_prices,
    load_ohlcv_csv,
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
    "SECTORS",
    "ar1_prices",
    "brownian_ohlc",
    "cointegrated_pair",
    "download_prices",
    "drifting_pair",
    "factor_panel",
    "garch_prices",
    "gbm_prices",
    "implied_vol_series",
    "instrument_universe",
    "intraday_volume_profile",
    "load_ohlcv_csv",
    "ohlcv",
    "ohlcv_from_close",
    "regime_prices",
    "seasonal_prices",
    "trading_days",
    "universe",
]
