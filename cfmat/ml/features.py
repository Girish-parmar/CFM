"""Leakage-free features for trading models (M19).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..analytics.indicators import atr, macd, rsi, sma


def make_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Features that use only information available at each bar's close."""
    close = bars["close"]
    logret = np.log(close).diff()
    feats = pd.DataFrame(index=bars.index)
    for lag in (1, 5, 10, 20):
        feats[f"ret_{lag}"] = close.pct_change(lag)
    feats["vol_20"] = logret.rolling(20).std()
    feats["vol_ratio"] = logret.rolling(5).std() / feats["vol_20"]
    feats["rsi_14"] = rsi(close, 14) / 100.0
    feats["dist_sma_20"] = close / sma(close, 20) - 1.0
    feats["dist_sma_50"] = close / sma(close, 50) - 1.0
    feats["macd_hist"] = macd(close)["histogram"] / close
    if {"high", "low"}.issubset(bars.columns):
        feats["atr_pct"] = atr(bars, 14) / close
    if "volume" in bars.columns:
        vol = bars["volume"].astype(float)
        feats["volume_z"] = (vol - vol.rolling(20).mean()) / vol.rolling(20).std()
    return feats.replace([np.inf, -np.inf], np.nan)
