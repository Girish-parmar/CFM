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


def adx(ohlc: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Wilder's Average Directional Index with +DI and −DI.

    ADX measures trend *strength* (above ~20–25 = trending), +DI/−DI its direction.
    """
    up = ohlc["high"].diff()
    down = -ohlc["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=ohlc.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=ohlc.index)
    smooth = lambda s: s.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()  # noqa: E731
    atr_ = smooth(true_range(ohlc))
    plus_di = 100 * smooth(plus_dm) / atr_
    minus_di = 100 * smooth(minus_dm) / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return pd.DataFrame({"adx": smooth(dx), "plus_di": plus_di, "minus_di": minus_di})


def supertrend(ohlc: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Supertrend: an ATR trailing line that flips sides when price closes through it.

    Returns the line and ``direction`` (+1 uptrend, −1 downtrend).
    """
    hl2 = ((ohlc["high"] + ohlc["low"]) / 2).to_numpy()
    close = ohlc["close"].to_numpy()
    a = atr(ohlc, period).to_numpy()
    n = len(close)
    upper, lower = hl2 + multiplier * a, hl2 - multiplier * a
    line = np.full(n, np.nan)
    direction = np.zeros(n)
    for i in range(n):
        if np.isnan(a[i]):
            continue
        if i == 0 or np.isnan(line[i - 1]):
            direction[i] = 1.0
            line[i] = lower[i]
            continue
        if direction[i - 1] == 1:
            lower[i] = max(lower[i], lower[i - 1]) if not np.isnan(lower[i - 1]) else lower[i]
            if close[i] < lower[i]:
                direction[i], line[i] = -1.0, upper[i]
            else:
                direction[i], line[i] = 1.0, lower[i]
        else:
            upper[i] = min(upper[i], upper[i - 1]) if not np.isnan(upper[i - 1]) else upper[i]
            if close[i] > upper[i]:
                direction[i], line[i] = 1.0, lower[i]
            else:
                direction[i], line[i] = -1.0, upper[i]
    out = pd.DataFrame({"supertrend": line, "direction": direction}, index=ohlc.index)
    out.loc[out["supertrend"].isna(), "direction"] = np.nan
    return out


def donchian(ohlc: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Highest high and lowest low of the last ``window`` bars (including today)."""
    return pd.DataFrame({"upper": ohlc["high"].rolling(window).max(), "lower": ohlc["low"].rolling(window).min()})


def bollinger_bandwidth(close: pd.Series, window: int = 20, n_std: float = 2.0) -> pd.Series:
    """(upper − lower) / middle. Low values mark a volatility squeeze."""
    bands = bollinger_bands(close, window, n_std)
    return (bands["upper"] - bands["lower"]) / bands["middle"]


def efficiency_ratio(close: pd.Series, window: int = 20) -> pd.Series:
    """Kaufman efficiency ratio: net move / total path length, in [0, 1].
    Near 1 = clean trend, near 0 = choppy, range-bound."""
    net = (close - close.shift(window)).abs()
    path = close.diff().abs().rolling(window).sum()
    return net / path.replace(0.0, np.nan)


def stochastic(ohlc: pd.DataFrame, k: int = 14, d: int = 3) -> pd.DataFrame:
    """Stochastic oscillator %K and %D (0–100)."""
    lowest = ohlc["low"].rolling(k).min()
    highest = ohlc["high"].rolling(k).max()
    pct_k = 100 * (ohlc["close"] - lowest) / (highest - lowest).replace(0.0, np.nan)
    return pd.DataFrame({"k": pct_k, "d": pct_k.rolling(d).mean()})


def rate_of_change(close: pd.Series, window: int = 10) -> pd.Series:
    return close.pct_change(window) * 100


def hurst_exponent(series: pd.Series | np.ndarray, max_lag: int = 50) -> float:
    """Hurst exponent of a (log) price series from the scaling of lagged differences.

    ≈ 0.5 random walk, > 0.5 trending (persistent), < 0.5 mean-reverting.
    """
    x = np.asarray(series, dtype=float)
    lags = np.arange(2, min(max_lag, len(x) // 4))
    tau = np.array([np.std(x[lag:] - x[:-lag]) for lag in lags])
    ok = tau > 0
    if ok.sum() < 3:
        return float("nan")
    return float(np.polyfit(np.log(lags[ok]), np.log(tau[ok]), 1)[0])
