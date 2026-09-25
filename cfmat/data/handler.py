"""Market-data handling: ticks to bars, validation, instruments, continuous futures, storage and replay (M16).

Ticks are a DataFrame in arrival order with ``ts`` (exchange time), ``seq``
(feed sequence number), ``symbol``, ``price`` and ``qty`` — the shape of
``data.tick_stream`` and of a broker's trade stream.

    validate_ticks      duplicates, out-of-order stamps, spikes, frozen prices and outages
    aggregate_bars      time, volume or dollar bars inside the trading session
    BarBuilder          the same time bars built one tick at a time, as a live handler does
    InstrumentMaster    lot sizes, tick sizes, expiries; price rounding, quantity checks, front month
    continuous_futures  one series across contract rolls: none, back-adjusted or ratio-adjusted
    store_ticks, load_ticks, replay
                        partitioned storage (Parquet if pyarrow is installed, else CSV) and
                        deterministic replay into any callback
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .synthetic import NSE_SESSION

TICK_COLUMNS = ["ts", "seq", "symbol", "price", "qty"]
BAR_COLUMNS = ["open", "high", "low", "close", "volume", "dollar", "ticks", "vwap"]


# -- validation ---------------------------------------------------------------------------

@dataclass
class TickReport:
    """What ``validate_ticks`` found: per-tick flags and the outage and stale periods."""
    ticks: pd.DataFrame
    flags: pd.DataFrame
    gaps: pd.DataFrame
    stale: pd.DataFrame

    def summary(self) -> dict[str, int]:
        """Counts of each problem."""
        return {**{k: int(v) for k, v in self.flags.sum().items()}, "outages": len(self.gaps),
                "stale_periods": len(self.stale)}

    def clean(self) -> pd.DataFrame:
        """Ticks without duplicates, spikes and frozen prices, in exchange-time order (late ticks slotted in)."""
        bad = self.flags[["duplicate", "spike", "stale"]].any(axis=1)
        return self.ticks[~bad.to_numpy()].sort_values(["ts", "seq"], kind="stable").reset_index(drop=True)


def validate_ticks(
    ticks: pd.DataFrame,
    tick_size: float = 0.05,
    spike_z: float = 10.0,
    spike_window: int = 50,
    confirm: int = 3,
    max_gap: str = "30s",
    stale_after: str = "30s",
    min_stale_ticks: int = 5,
    session: tuple[str, str] = NSE_SESSION,
) -> TickReport:
    """Check a tick stream in arrival order, the way a feed handler sees it.

    * duplicate: a sequence number seen before;
    * out_of_order: an exchange time earlier than one already received (kept, and re-sorted by ``clean``);
    * spike: a jump from the last accepted price of more than ``spike_z`` typical moves
      (robust: 1.48 × the median non-zero change over the last ``spike_window`` accepted
      ticks, at least two ticks), scaled up by √(time since the price last changed / typical
      spacing), so the first print after a quiet or frozen spell is not a spike. If
      ``confirm`` ticks in a row are out of line, the market really moved: they are
      accepted, not flagged;
    * stale: the same price for longer than ``stale_after`` over at least ``min_stale_ticks`` ticks;
    * gaps: no ticks for longer than ``max_gap`` inside the session.
    """
    n = len(ticks)
    ts = ticks["ts"].to_numpy().astype("datetime64[ns]").astype(np.int64) / 1e9
    seq = ticks["seq"].to_numpy()
    price = ticks["price"].to_numpy(dtype=float)
    dup, late, spike = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    seen: set = set()
    latest = -np.inf
    recent_p: deque[float] = deque(maxlen=spike_window)
    recent_t: deque[float] = deque(maxlen=spike_window)
    pending: list[int] = []
    step = spacing = 0.0
    since = -np.inf                  # when the accepted price last changed
    refresh = 0                      # recompute the robust scale every few accepted ticks

    def accept(j: int) -> None:
        nonlocal since, refresh
        if not recent_p or price[j] != recent_p[-1]:
            since = ts[j]
        recent_p.append(price[j])
        recent_t.append(ts[j])
        refresh -= 1

    for i in range(n):
        if seq[i] in seen:
            dup[i] = True
            continue
        seen.add(seq[i])
        if ts[i] < latest:
            late[i] = True
        else:
            latest = ts[i]
        if len(recent_p) >= 10:
            if refresh <= 0:
                moves = np.abs(np.diff(np.fromiter(recent_p, float)))
                moves = moves[moves > 0]
                step = max(1.4826 * np.median(moves), 2 * tick_size) if len(moves) else 2 * tick_size
                spacing = max(np.median(np.abs(np.diff(np.fromiter(recent_t, float)))), 1e-3)
                refresh = 8
            allowed = spike_z * step * np.sqrt(max(1.0, abs(ts[i] - since) / spacing))
            if abs(price[i] - recent_p[-1]) > allowed:
                pending.append(i)
                if len(pending) >= confirm:                    # a real move, not a bad print
                    recent_p.clear()
                    recent_t.clear()
                    for j in pending:
                        accept(j)
                    pending.clear()
                    refresh = 0
                continue
        for j in pending:                                      # the run ended: those were bad prints
            spike[j] = True
        pending.clear()
        accept(i)
    for j in pending:
        spike[j] = True

    good = ~(dup | spike)
    stale_flags, stale_rows = _stale_runs(ticks, good, pd.Timedelta(stale_after), min_stale_ticks)
    flags = pd.DataFrame({"duplicate": dup, "out_of_order": late, "spike": spike, "stale": stale_flags},
                         index=ticks.index)
    gaps = _gaps(ticks[good], pd.Timedelta(max_gap), session)
    return TickReport(ticks, flags, gaps, stale_rows)


def _stale_runs(ticks, good, after, min_ticks):
    flags = np.zeros(len(ticks), bool)
    columns = ["start", "end", "seconds", "detected_at"]
    idx = np.flatnonzero(good)
    if len(idx) == 0:
        return flags, pd.DataFrame(columns=columns)
    prices = ticks["price"].to_numpy()[idx]
    stamps = pd.DatetimeIndex(ticks["ts"].to_numpy()[idx])
    starts = np.flatnonzero(np.r_[True, prices[1:] != prices[:-1]])
    ends = np.r_[starts[1:], len(prices)] - 1
    long_runs = ((ends - starts + 1) >= min_ticks) & ((stamps[ends] - stamps[starts]) > after)
    rows = []
    for first, last in zip(starts[long_runs], ends[long_runs], strict=True):
        flags[idx[first:last + 1]] = True
        rows.append({"start": stamps[first], "end": stamps[last],
                     "seconds": (stamps[last] - stamps[first]).total_seconds(), "detected_at": stamps[first] + after})
    return flags, pd.DataFrame(rows, columns=columns)


def _gaps(ticks, max_gap, session):
    open_, close = (pd.Timedelta(f"{t}:00") for t in session)
    rows = []
    for day, group in ticks.sort_values("ts").groupby(ticks["ts"].dt.normalize()):
        stamps = pd.DatetimeIndex([day + open_, *group["ts"], day + close])
        steps = stamps[1:] - stamps[:-1]
        for k in np.flatnonzero(steps > max_gap):
            rows.append({"start": stamps[k], "end": stamps[k + 1], "seconds": steps[k].total_seconds()})
    return pd.DataFrame(rows, columns=["start", "end", "seconds"])


# -- bars -------------------------------------------------------------------------------------

def _in_session(ticks: pd.DataFrame, session: tuple[str, str]) -> pd.DataFrame:
    open_, close = (pd.Timedelta(f"{t}:00") for t in session)
    offset = ticks["ts"] - ticks["ts"].dt.normalize()
    return ticks[(offset >= open_) & (offset < close)]


def aggregate_bars(
    ticks: pd.DataFrame,
    kind: str = "time",
    size: str | float = "1min",
    session: tuple[str, str] = NSE_SESSION,
) -> pd.DataFrame:
    """OHLCV bars from clean ticks (see ``TickReport.clean``), never spanning two sessions.

    ``kind="time"``: ``size`` is a duration (``"1min"``, ``"15min"``); bars start at the
    session open and are labelled by their start; minutes without trades have no bar.
    ``kind="volume"`` or ``"dollar"``: a bar closes once ``size`` shares (or rupees) have
    traded; the tick that crosses the line stays whole in its bar, and the day's last bar may
    be short. These bars are labelled by their last tick's time. Columns: open, high, low,
    close, volume, dollar (traded value), ticks and vwap.
    """
    t = _in_session(ticks, session).sort_values(["ts", "seq"], kind="stable")
    if t.empty:
        return pd.DataFrame(columns=BAR_COLUMNS)
    value = t["price"] * t["qty"]
    day = t["ts"].dt.normalize()
    if kind == "time":
        open_ = pd.Timedelta(f"{session[0]}:00")
        step = pd.Timedelta(size)
        start = day + open_ + ((t["ts"] - day - open_) // step) * step
        key = start
    elif kind in ("volume", "dollar"):
        amount = t["qty"] if kind == "volume" else value
        before = amount.groupby(day).cumsum() - amount
        key = pd.Series(list(zip(day, (before // float(size)).astype(int), strict=True)), index=t.index)
    else:
        raise ValueError("kind must be time, volume or dollar")
    grouped = pd.DataFrame({"price": t["price"], "qty": t["qty"], "value": value, "ts": t["ts"]}).groupby(key, sort=True)
    bars = pd.DataFrame({
        "open": grouped["price"].first(), "high": grouped["price"].max(), "low": grouped["price"].min(),
        "close": grouped["price"].last(), "volume": grouped["qty"].sum(), "dollar": grouped["value"].sum(),
        "ticks": grouped["price"].size(),
    })
    bars["vwap"] = bars["dollar"] / bars["volume"]
    bars.index = pd.DatetimeIndex(bars.index if kind == "time" else grouped["ts"].last().to_numpy(), name="ts")
    return bars[BAR_COLUMNS]


class BarBuilder:
    """Time bars built one tick at a time, as a live feed handler builds them.

    ``update`` returns the bars that the new tick completes (usually none, or the previous
    bar); ``flush`` returns the bar still open at the end. Feed it clean ticks in time order:
    the result equals ``aggregate_bars(kind="time")``. Timestamps are exchange-local and naive.
    """

    _DAY = 86_400 * 10**9

    def __init__(self, size: str = "1min", session: tuple[str, str] = NSE_SESSION) -> None:
        self.step = pd.Timedelta(size).value
        self.open_, self.close_ = (pd.Timedelta(f"{t}:00").value for t in session)
        self.current: dict | None = None
        self._start = None

    def update(self, ts, price: float, qty: int) -> list[dict]:
        """Add one tick; returns completed bars."""
        ns = pd.Timestamp(ts).value if not isinstance(ts, int) else ts
        into_day = ns % self._DAY
        if not self.open_ <= into_day < self.close_:
            return []
        start = ns - into_day + self.open_ + (into_day - self.open_) // self.step * self.step
        done = []
        if self.current is not None and self._start != start:
            done.append(self._finish())
        if self.current is None:
            self._start = start
            self.current = {"ts": pd.Timestamp(start), "open": price, "high": price, "low": price,
                            "close": price, "volume": 0, "dollar": 0.0, "ticks": 0}
        bar = self.current
        if price > bar["high"]:
            bar["high"] = price
        if price < bar["low"]:
            bar["low"] = price
        bar["close"] = price
        bar["volume"] += qty
        bar["dollar"] += price * qty
        bar["ticks"] += 1
        return done

    def flush(self) -> list[dict]:
        """Close the open bar, if any."""
        return [self._finish()] if self.current is not None else []

    def _finish(self) -> dict:
        bar, self.current = self.current, None
        bar["vwap"] = bar["dollar"] / bar["volume"]
        return bar


# -- instruments and continuous futures ---------------------------------------------------------

@dataclass
class InstrumentMaster:
    """Reference data for tradable instruments, indexed by symbol.

    Columns: ``underlying``, ``segment`` (EQ, FUT, OPT ...), ``lot_size``, ``tick_size`` and
    ``expiry`` (missing for cash equities). Refresh it every morning from the broker's or
    exchange's instrument file: lot sizes, tick sizes and expiry rules change.
    """
    table: pd.DataFrame

    @classmethod
    def from_csv(cls, path: str | Path) -> InstrumentMaster:
        """Read a master saved by ``to_csv``."""
        table = pd.read_csv(path, index_col="symbol", parse_dates=["expiry"])
        return cls(table)

    def to_csv(self, path: str | Path) -> Path:
        """Save the master; returns the path."""
        self.table.to_csv(path, index_label="symbol")
        return Path(path)

    def get(self, symbol: str) -> pd.Series:
        """One instrument's row; ``KeyError`` names unknown symbols."""
        if symbol not in self.table.index:
            raise KeyError(f"{symbol} is not in the instrument master")
        return self.table.loc[symbol]

    def round_price(self, symbol: str, price: float) -> float:
        """The nearest valid price on the instrument's tick grid."""
        tick = float(self.get(symbol)["tick_size"])
        return round(round(price / tick) * tick, 6)

    def check_quantity(self, symbol: str, qty: int) -> str:
        """An empty string if ``qty`` is a positive whole number of lots, else the reason it is not."""
        lot = int(self.get(symbol)["lot_size"])
        if qty <= 0 or qty % lot:
            return f"{symbol} trades in lots of {lot}; {qty} is not a positive multiple"
        return ""

    def contracts(self, underlying: str, on: str | pd.Timestamp | None = None) -> pd.DataFrame:
        """Futures on ``underlying`` not yet expired on ``on`` (all if None), nearest expiry first."""
        t = self.table[(self.table["underlying"] == underlying) & (self.table["segment"] == "FUT")]
        if on is not None:
            t = t[t["expiry"] >= pd.Timestamp(on)]
        return t.sort_values("expiry")

    def front(self, underlying: str, on: str | pd.Timestamp, roll_days: int = 0) -> str:
        """The contract to hold on ``on``: the nearest whose expiry is more than ``roll_days`` business days away."""
        on = pd.Timestamp(on)
        for symbol, row in self.contracts(underlying, on).iterrows():
            if np.busday_count(on.date(), row["expiry"].date()) > roll_days:
                return symbol
        raise ValueError(f"no {underlying} contract beyond {roll_days} business days of {on:%Y-%m-%d}")


def continuous_futures(
    prices: pd.DataFrame,
    master: InstrumentMaster | pd.DataFrame,
    underlying: str | None = None,
    roll_days: int = 2,
    method: str = "ratio",
) -> pd.DataFrame:
    """One price series across contract rolls.

    Holds the front contract until ``roll_days`` business days before its expiry, then the
    next. ``method``: ``none`` (raw prices: the roll shows up as a fake jump), ``back``
    (add each roll's price difference to history: point P&L is right, old prices can even go
    negative, percentage returns are distorted) or ``ratio`` (scale history by each roll's
    price ratio: percentage returns are right, point differences are not). Columns:
    ``price``, ``contract`` and ``roll`` (True on the first day of a new contract).
    """
    if method not in ("none", "back", "ratio"):
        raise ValueError("method must be none, back or ratio")
    table = master.table if isinstance(master, InstrumentMaster) else master
    im = InstrumentMaster(table)
    name = underlying or table["underlying"].iloc[0]
    active = []
    for day in prices.index:
        try:
            symbol = im.front(name, day, roll_days)
        except ValueError:
            symbol = None
        active.append(symbol if symbol in prices.columns and pd.notna(prices.at[day, symbol]) else None)
    out = pd.DataFrame({"contract": active}, index=prices.index).dropna()
    out["price"] = [prices.at[d, c] for d, c in out["contract"].items()]
    out["roll"] = out["contract"] != out["contract"].shift()
    out.iloc[0, out.columns.get_loc("roll")] = False
    adjusted = out["price"].astype(float).to_numpy().copy()
    if method != "none":
        positions = np.flatnonzero(out["roll"].to_numpy())
        for pos in positions[::-1]:
            day_before = out.index[pos - 1]
            old, new = prices.at[day_before, out["contract"].iloc[pos - 1]], prices.at[day_before, out["contract"].iloc[pos]]
            if method == "back":
                adjusted[:pos] += new - old
            else:
                adjusted[:pos] *= new / old
    out["price"] = adjusted
    return out[["price", "contract", "roll"]]


# -- storage and replay -----------------------------------------------------------------------------

def _parquet_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("pyarrow") is not None


def store_ticks(ticks: pd.DataFrame, root: str | Path, fmt: str = "auto") -> list[Path]:
    """Write ticks partitioned as ``root/date=YYYY-MM-DD/symbol=XXX/ticks.parquet`` (or ``.csv``).

    ``fmt`` is ``parquet``, ``csv`` or ``auto`` (Parquet when pyarrow is installed).
    Existing partitions for the same date and symbol are replaced.
    """
    fmt = ("parquet" if _parquet_available() else "csv") if fmt == "auto" else fmt
    root = Path(root)
    paths = []
    for (day, symbol), group in ticks.groupby([ticks["ts"].dt.normalize(), "symbol"], sort=True):
        folder = root / f"date={day:%Y-%m-%d}" / f"symbol={symbol}"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"ticks.{fmt}"
        group = group[TICK_COLUMNS]
        if fmt == "parquet":
            group.to_parquet(path, index=False)
        else:
            group.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S.%f")
        paths.append(path)
    return paths


def load_ticks(root: str | Path, symbols: Iterable[str] | None = None,
               start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Read stored ticks, opening only the partitions for the wanted symbols and dates, in (ts, seq) order."""
    wanted = set(symbols) if symbols is not None else None
    lo = pd.Timestamp(start) if start else None
    hi = pd.Timestamp(end) if end else None
    frames = []
    for path in sorted(Path(root).glob("date=*/symbol=*/ticks.*")):
        day = pd.Timestamp(path.parent.parent.name.split("=", 1)[1])
        symbol = path.parent.name.split("=", 1)[1]
        if (wanted is not None and symbol not in wanted) or (lo is not None and day < lo) or (hi is not None and day > hi):
            continue
        frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, parse_dates=["ts"])
        frame["symbol"] = frame["symbol"].astype(str)
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=TICK_COLUMNS)
    ticks = pd.concat(frames, ignore_index=True)
    return ticks.sort_values(["ts", "seq"], kind="stable").reset_index(drop=True)


def replay(ticks: pd.DataFrame, on_tick: Callable[[pd.Timestamp, str, float, int], None]) -> int:
    """Call ``on_tick(ts, symbol, price, qty)`` for every tick in (ts, seq) order; returns the count.

    The same ticks always arrive in the same order, so a strategy replayed twice
    produces the same orders: the basis for testing live code against history.
    """
    ordered = ticks.sort_values(["ts", "seq"], kind="stable")
    stamps = ordered["ts"].tolist()
    for ts, symbol, price, qty in zip(stamps, ordered["symbol"].tolist(), ordered["price"].tolist(),
                                      ordered["qty"].tolist(), strict=True):
        on_tick(ts, symbol, float(price), int(qty))
    return len(ordered)
