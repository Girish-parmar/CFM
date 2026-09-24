"""Loading real market data from files and free APIs (M03, M05).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


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
        raise ImportError("Install the data extra: pip install yfinance") from exc

    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker!r}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    df.index.name = "date"
    return df[["open", "high", "low", "close", "volume"]]
