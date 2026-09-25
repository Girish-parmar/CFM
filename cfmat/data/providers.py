"""Historical bars from Alpaca and Interactive Brokers (M16, M17).

Both return the library's standard shape (see ``cfmat.data.loaders``): indexed
by a timezone-naive ``date`` in the exchange's local time, with lowercase
``open, high, low, close, volume`` columns.

Alpaca (US stocks only; no NSE or BSE)
    ``pip install -e ".[alpaca]"``. Keys come from the environment, never from
    code: ``ALPACA_API_KEY`` and ``ALPACA_SECRET_KEY`` (or ``APCA_API_KEY_ID``
    and ``APCA_API_SECRET_KEY``). A free paper account is enough. The free plan
    has real-time data from one exchange (IEX) only and delays the latest
    15 minutes of consolidated (SIP) data, so ``feed="sip"`` requests end 16
    minutes ago unless you pass ``end``.

Interactive Brokers (US, NSE and other markets)
    ``pip install -e ".[ibkr]"``. TWS or IB Gateway must be running and
    logged in with API access enabled (ports: TWS paper 7497, Gateway paper
    4002). The API returns history only for instruments with a live market-data
    subscription, and limits requests (about 60 per 10 minutes): ``chunks``
    pauses between requests to stay inside that. Check volume units against
    another source before using volume-based signals.

Data from both is licensed for personal use: keep files in ``data/`` (git-ignored).
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Iterable

import pandas as pd

from .loaders import standardize_ohlcv

ALPACA_KEY_VARS = ("ALPACA_API_KEY", "APCA_API_KEY_ID")
ALPACA_SECRET_VARS = ("ALPACA_SECRET_KEY", "APCA_API_SECRET_KEY")

_UNITS = {
    "min": "Minute", "mins": "Minute", "minute": "Minute", "minutes": "Minute", "m": "Minute", "t": "Minute",
    "hour": "Hour", "hours": "Hour", "h": "Hour",
    "day": "Day", "days": "Day", "d": "Day",
    "week": "Week", "weeks": "Week", "w": "Week",
    "month": "Month", "months": "Month", "mo": "Month",
}


def parse_timeframe(text: str) -> tuple[int, str]:
    """``"5Min"``, ``"1h"``, ``"1Day"``, ``"1 week"`` → ``(amount, unit)`` with unit Minute/Hour/Day/Week/Month."""
    match = re.fullmatch(r"\s*(\d+)\s*([A-Za-z]+)\s*", text)
    unit = _UNITS.get(match.group(2).lower()) if match else None
    if unit is None:
        raise ValueError(f"cannot read timeframe {text!r}; use for example 1Day, 1Hour, 15Min, 1Week")
    return int(match.group(1)), unit


def alpaca_credentials() -> tuple[str, str]:
    """The Alpaca key pair from the environment; a clear error if it is missing."""
    key = next((os.environ[v] for v in ALPACA_KEY_VARS if os.environ.get(v)), None)
    secret = next((os.environ[v] for v in ALPACA_SECRET_VARS if os.environ.get(v)), None)
    if not key or not secret:
        raise RuntimeError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY (from the Alpaca dashboard, paper account) "
                           "as environment variables; never put keys in code")
    return key, secret


def alpaca_bars(
    symbols: str | Iterable[str],
    start: str | pd.Timestamp,
    end: str | pd.Timestamp | None = None,
    timeframe: str = "1Day",
    adjustment: str = "all",
    feed: str = "sip",
    tz: str = "America/New_York",
    client=None,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """US stock bars from Alpaca: one frame for one symbol, a dict of frames for several.

    ``adjustment`` is ``raw``, ``split``, ``dividend`` or ``all`` (use ``all``
    for backtests); ``feed`` is ``sip`` (every exchange) or ``iex`` (one
    exchange: its volume is a small share of the total). Naive ``start`` and
    ``end`` are read as UTC. Pass ``client`` to reuse a
    ``StockHistoricalDataClient``.
    """
    try:
        from alpaca.data.enums import Adjustment, DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    except ImportError as exc:
        raise ImportError('Alpaca needs its SDK: pip install -e ".[alpaca]"') from exc
    if client is None:
        from alpaca.data.historical import StockHistoricalDataClient

        client = StockHistoricalDataClient(*alpaca_credentials())
    names = [symbols] if isinstance(symbols, str) else list(symbols)
    if end is None and feed.lower() == "sip":
        end = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=16)     # the free plan delays recent SIP data
    amount, unit = parse_timeframe(timeframe)
    request = StockBarsRequest(
        symbol_or_symbols=names,
        start=_utc(start),
        end=None if end is None else _utc(end),
        timeframe=TimeFrame(amount, getattr(TimeFrameUnit, unit)),
        adjustment=getattr(Adjustment, adjustment.upper()),
        feed=getattr(DataFeed, feed.upper()),
    )
    frame = client.get_stock_bars(request).df
    found = set(frame.index.get_level_values("symbol")) if len(frame) else set()
    out = {}
    for name in names:
        if name not in found:
            raise ValueError(f"Alpaca returned no bars for {name!r} (check the symbol, dates and your data plan)")
        out[name] = standardize_ohlcv(frame.xs(name, level="symbol"), tz=tz)
    return out[names[0]] if isinstance(symbols, str) else out


def ibkr_bars(
    symbol: str,
    exchange: str = "NSE",
    currency: str = "INR",
    sec_type: str = "STK",
    duration: str = "5 Y",
    bar_size: str = "1 day",
    what_to_show: str = "TRADES",
    use_rth: bool = True,
    end: str | pd.Timestamp | None = None,
    chunks: int = 1,
    pause_s: float = 10.5,
    tz: str = "Asia/Kolkata",
    host: str = "127.0.0.1",
    port: int = 7497,
    client_id: int = 17,
    ib=None,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Bars for one instrument from Interactive Brokers through a running TWS or IB Gateway.

    ``duration`` (``"5 Y"``, ``"6 M"``, ``"10 D"``) and ``bar_size`` (``"1 day"``,
    ``"1 hour"``, ``"5 mins"``) use IBKR's own spellings; ``end`` (exchange time
    when naive) returns bars before it, default up to now. ``chunks`` > 1 walks
    backwards, one ``duration`` per request, pausing ``pause_s`` seconds between
    requests (IBKR allows about 60 historical requests per 10 minutes). Use
    ``sec_type="IND"`` for an index. ``what_to_show="ADJUSTED_LAST"`` gives
    split- and dividend-adjusted daily bars but only up to now, in one request.
    Connects read-only (no orders) unless you pass a connected ``ib``.
    """
    if what_to_show.upper() == "ADJUSTED_LAST" and (end is not None or chunks > 1):
        raise ValueError("IBKR serves ADJUSTED_LAST only up to now: leave end empty and use chunks=1")
    if chunks < 1:
        raise ValueError("chunks must be at least 1")
    try:
        from ib_async import IB, Contract
    except ImportError as exc:
        raise ImportError('Interactive Brokers needs ib_async: pip install -e ".[ibkr]"') from exc
    own = ib is None
    if own:
        ib = IB()
        ib.connect(host, port, clientId=client_id, readonly=True)
    try:
        qualified = ib.qualifyContracts(Contract(secType=sec_type, symbol=symbol, exchange=exchange, currency=currency))
        if not qualified or not getattr(qualified[0], "conId", 0):
            raise ValueError(f"IBKR does not recognise {sec_type} {symbol!r} on {exchange} in {currency}; "
                             "look the contract up in TWS")
        contract = qualified[0]
        until = "" if end is None else _aware(end, tz).to_pydatetime()
        rows, earliest = [], None
        for i in range(chunks):
            if i:
                sleep(pause_s)
            bars = ib.reqHistoricalData(contract, endDateTime=until, durationStr=duration, barSizeSetting=bar_size,
                                        whatToShow=what_to_show, useRTH=use_rth, formatDate=2)
            if not bars:
                break
            first = bars[0].date
            if earliest is not None and not first < earliest:
                break                                       # no older bars: the history is exhausted
            earliest = first
            rows += [{"date": b.date, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                      "volume": b.volume} for b in bars]
            until = first
    finally:
        if own:
            ib.disconnect()
    if not rows:
        raise ValueError(f"IBKR returned no bars for {symbol!r}: check the market-data subscription and dates")
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])     # dates for daily bars, UTC datetimes for intraday
    return standardize_ohlcv(frame.set_index("date"), tz=tz)


def _utc(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return (ts.tz_localize("UTC") if ts.tz is None else ts.tz_convert("UTC")).to_pydatetime()


def _aware(value, tz: str) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize(tz) if ts.tz is None else ts
