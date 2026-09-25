"""Loading real market data from files and free APIs, and checking it (M03, M05, M16).

Every loader returns the same shape: a DataFrame indexed by a timezone-naive
``date`` in the exchange's local time, with lowercase ``open, high, low, close,
volume`` columns, sorted, without duplicate timestamps. Broker and vendor
feeds (Alpaca, Interactive Brokers) are in ``cfmat.data.providers``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

OHLCV = ["open", "high", "low", "close", "volume"]


def standardize_ohlcv(frame: pd.DataFrame, tz: str | None = None) -> pd.DataFrame:
    """Bring any OHLCV table to the library's shape.

    Lower-cases the column names and keeps ``open, high, low, close, volume``;
    converts a timezone-aware index to ``tz`` (the exchange's time zone) and
    drops the zone; sorts; keeps the last row of any duplicate timestamp and
    drops rows without a close.
    """
    df = frame.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in OHLCV if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns {missing}; have {list(df.columns)}")
    index = pd.to_datetime(df.index)
    if index.tz is not None:
        index = index.tz_convert(tz or "UTC").tz_localize(None)
    df.index = index
    df.index.name = "date"
    df = df[OHLCV].astype(float).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df.dropna(subset=["close"])


def ohlcv_problems(frame: pd.DataFrame) -> list[str]:
    """Plain-language list of data-quality problems; empty when the bars look sane.

    Checks non-positive prices, highs below lows, opens or closes outside the
    day's range, negative volume, duplicate or unsorted timestamps, and
    one-bar moves over 25% (splits applied without adjustment, or bad ticks).
    """
    problems = []
    if frame.empty:
        return ["no rows"]
    prices = frame[["open", "high", "low", "close"]]
    count = int((prices <= 0).any(axis=1).sum())
    if count:
        problems.append(f"{count} rows with a zero or negative price")
    count = int((frame["high"] < frame["low"]).sum())
    if count:
        problems.append(f"{count} rows with high below low")
    outside = (prices[["open", "close"]].max(axis=1) > frame["high"] * (1 + 1e-9)) | \
              (prices[["open", "close"]].min(axis=1) < frame["low"] * (1 - 1e-9))
    if outside.any():
        problems.append(f"{int(outside.sum())} rows with open or close outside the high-low range")
    if (frame["volume"] < 0).any():
        problems.append(f"{int((frame['volume'] < 0).sum())} rows with negative volume")
    if frame.index.duplicated().any():
        problems.append(f"{int(frame.index.duplicated().sum())} duplicate timestamps")
    if not frame.index.is_monotonic_increasing:
        problems.append("timestamps are not in order")
    jumps = frame["close"].pct_change().abs() > 0.25
    if jumps.any():
        first = frame.index[jumps.to_numpy()][0]
        problems.append(f"{int(jumps.sum())} one-bar moves over 25% (first on {first:%Y-%m-%d}): "
                        "check for unadjusted splits or bad ticks")
    return problems


def load_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV with a date column and OHLCV columns (any capitalisation)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    date_col = "date" if "date" in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    return df.set_index(date_col).sort_index()


def download_prices(ticker: str, start: str = "2018-01-01", end: str | None = None) -> pd.DataFrame:
    """Download split/dividend-adjusted daily OHLCV with yfinance.

    NSE symbols take a ``.NS`` suffix (``TCS.NS``), BSE ``.BO``; indices use
    ``^NSEI`` (Nifty 50) and ``^NSEBANK`` (Bank Nifty). Free data is fine for
    learning; licensed exchange data is needed for anything commercial.
    """
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError('Install the data extra: pip install -e ".[data]"') from exc

    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker!r}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return standardize_ohlcv(df)
