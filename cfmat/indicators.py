"""Technical indicators, written out so learners can see every step."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's Relative Strength Index (0–100)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # A window with no losses has RSI 100 by definition.
    return out.where(avg_loss != 0, 100.0).where(avg_gain.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "histogram": line - sig})


def bollinger_bands(close: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = sma(close, window)
    sd = close.rolling(window).std(ddof=0)
    return pd.DataFrame({"middle": mid, "upper": mid + n_std * sd, "lower": mid - n_std * sd})


def true_range(ohlc: pd.DataFrame) -> pd.Series:
    prev_close = ohlc["close"].shift(1)
    ranges = pd.concat(
        [ohlc["high"] - ohlc["low"], (ohlc["high"] - prev_close).abs(), (ohlc["low"] - prev_close).abs()],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range with Wilder smoothing."""
    return true_range(ohlc).ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window).mean()
    sd = series.rolling(window).std(ddof=0)
    return (series - mean) / sd.replace(0.0, np.nan)


def rolling_volatility(close: pd.Series, window: int = 20, periods: int = 252) -> pd.Series:
    """Annualised volatility of log returns over a rolling window."""
    return np.log(close).diff().rolling(window).std() * np.sqrt(periods)
