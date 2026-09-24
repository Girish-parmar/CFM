"""Trade journal: record fills, rebuild them into trades and review the trades (M17).

Fills are the raw record; notes (``setup``, ``stop``, ``target``, ``tags``,
``strategy``, free text) attach to them. ``TradeJournal.round_trips`` groups the
fills into trades. A trade runs from flat to flat, including scale-ins and
partial exits. A fill that reverses the position closes one trade and opens the
next, with its charges split pro rata. Each trade carries gross and net P&L,
holding time and the R-multiple against the planned stop. ``excursions`` adds
maximum adverse and favourable excursion (MAE/MFE) from price bars.
``trade_summary`` and ``trade_breakdown`` turn trades into the numbers a trading review
needs, and ``save``/``load`` keep the journal in CSV or SQLite.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .orders import BUY, SELL, Fill

FILL_COLUMNS = ("order_id", "symbol", "side", "qty", "price", "charges", "timestamp")
TRIP_COLUMNS = (
    "trip_id", "symbol", "direction", "status", "entry_time", "exit_time", "holding", "qty",
    "entry_price", "exit_price", "gross_pnl", "charges", "net_pnl", "return_pct", "stop", "target",
    "risk", "r_multiple", "setup", "strategy", "tags", "n_fills",
)
_NOTE_KEYS = ("setup", "strategy", "stop", "target", "tags", "note")

_SCHEMA = """CREATE TABLE IF NOT EXISTS journal_fills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER, symbol TEXT NOT NULL, side TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
    qty INTEGER NOT NULL CHECK (qty > 0), price REAL NOT NULL, charges REAL DEFAULT 0,
    timestamp TEXT, notes TEXT)"""


def _tags(value) -> tuple[str, ...]:
    """Tags from a list, a tuple or a ``"a;b"`` string; empty for missing values."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ()
    if isinstance(value, str):
        return tuple(t.strip() for t in value.split(";") if t.strip())
    return tuple(str(t) for t in value)


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


@dataclass
class TradeJournal:
    """Fills plus notes: what happened, and what you planned and thought."""
    rows: list[dict] = field(default_factory=list)

    @classmethod
    def from_fills(cls, fills: Iterable[Fill]) -> TradeJournal:
        """A journal holding these fills (for example ``PaperBroker.fills``)."""
        journal = cls()
        for fill in fills:
            journal.record(fill)
        return journal

    def record(self, fill: Fill, **notes) -> dict:
        """Store one fill, with optional notes such as ``setup``, ``stop`` or ``tags``; returns the row.

        Subscribe it to a broker to journal every fill as it happens:
        ``broker.add_fill_listener(journal.record)``.
        """
        row = {
            "order_id": fill.order_id,
            "symbol": fill.symbol,
            "side": fill.side,
            "qty": fill.qty,
            "price": round(fill.price, 4),
            "charges": round(fill.charges, 2),
            "timestamp": fill.timestamp.isoformat() if fill.timestamp else None,
        }
        row.update(notes)
        self.rows.append(row)
        return row

    def annotate(self, order_id: int, **notes) -> int:
        """Add notes to every fill of a broker order (plan before, review after); returns rows changed."""
        changed = 0
        for row in self.rows:
            if row["order_id"] == order_id:
                row.update(notes)
                changed += 1
        return changed

    def to_frame(self) -> pd.DataFrame:
        """The fills as a table, one row per fill, notes as extra columns."""
        frame = pd.DataFrame(self.rows)
        if frame.empty:
            return pd.DataFrame(columns=list(FILL_COLUMNS))
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        return frame

    def round_trips(self, include_open: bool = False) -> pd.DataFrame:
        """The fills grouped into flat-to-flat trades (see the module docstring)."""
        return round_trips(self.rows, include_open)

    # -- persistence -------------------------------------------------------------------
    def save(self, path: str | Path) -> Path:
        """Write every fill to ``.csv`` or to SQLite (``.sqlite``/``.db``), replacing the file's journal."""
        path = Path(path)
        if path.suffix == ".csv":
            rows = [dict(r, tags=";".join(_tags(r["tags"]))) if "tags" in r else r for r in self.rows]
            pd.DataFrame(rows).to_csv(path, index=False)
            return path
        with sqlite3.connect(path) as con:
            con.execute(_SCHEMA)
            con.execute("DELETE FROM journal_fills")
            con.executemany(
                f"INSERT INTO journal_fills ({', '.join(FILL_COLUMNS)}, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(*(r.get(c) for c in FILL_COLUMNS),
                  json.dumps({k: (list(v) if isinstance(v, tuple) else v) for k, v in r.items()
                              if k not in FILL_COLUMNS}, default=str))
                 for r in self.rows],
            )
        con.close()
        return path

    @classmethod
    def load(cls, path: str | Path) -> TradeJournal:
        """Read a journal written by ``save``."""
        path = Path(path)
        if path.suffix == ".csv":
            frame = pd.read_csv(path, dtype={"symbol": str, "side": str, "timestamp": str})
            rows = [{k: v for k, v in r.items() if not _is_missing(v)} for r in frame.to_dict("records")]
            for r in rows:
                r.setdefault("timestamp", None)
                r["order_id"], r["qty"] = int(r["order_id"]), int(r["qty"])
            return cls(rows)
        with sqlite3.connect(path) as con:
            con.row_factory = sqlite3.Row
            records = con.execute("SELECT * FROM journal_fills ORDER BY id").fetchall()
        con.close()
        rows = []
        for rec in records:
            row = {c: rec[c] for c in FILL_COLUMNS}
            row.update(json.loads(rec["notes"] or "{}"))
            rows.append(row)
        return cls(rows)


class _Trip:
    """Accumulates the fills of one trade."""

    def __init__(self, trip_id: int, symbol: str, direction: int, notes: dict) -> None:
        self.trip_id, self.symbol, self.direction, self.notes = trip_id, symbol, direction, notes
        self.entry_qty = self.exit_qty = self.n_fills = 0
        self.entry_value = self.exit_value = self.charges = 0.0
        self.entry_time = self.exit_time = pd.NaT

    def add(self, qty: int, price: float, charges: float, ts, opening: bool) -> None:
        if opening:
            self.entry_qty += qty
            self.entry_value += qty * price
            if pd.isna(self.entry_time):
                self.entry_time = ts
        else:
            self.exit_qty += qty
            self.exit_value += qty * price
            self.exit_time = ts
        self.charges += charges
        self.n_fills += 1

    def row(self, closed: bool) -> dict:
        entry_price = self.entry_value / self.entry_qty
        exit_price = self.exit_value / self.exit_qty if self.exit_qty else np.nan
        gross = self.direction * (self.exit_value - self.exit_qty * entry_price)
        net = gross - self.charges
        stop = self.notes.get("stop")
        stop = None if _is_missing(stop) else float(stop)
        risk = abs(entry_price - stop) * self.entry_qty if stop is not None else np.nan
        target = self.notes.get("target")
        return {
            "trip_id": self.trip_id,
            "symbol": self.symbol,
            "direction": "LONG" if self.direction > 0 else "SHORT",
            "status": "CLOSED" if closed else "OPEN",
            "entry_time": self.entry_time,
            "exit_time": self.exit_time if closed else pd.NaT,
            "holding": (self.exit_time - self.entry_time) if closed else pd.NaT,
            "qty": self.entry_qty,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "gross_pnl": gross,
            "charges": self.charges,
            "net_pnl": net,
            "return_pct": 100 * net / self.entry_value,
            "stop": np.nan if stop is None else stop,
            "target": np.nan if _is_missing(target) else float(target),
            "risk": risk,
            "r_multiple": net / risk if risk and not np.isnan(risk) else np.nan,
            "setup": self.notes.get("setup") or "",
            "strategy": self.notes.get("strategy") or "",
            "tags": _tags(self.notes.get("tags")),
            "n_fills": self.n_fills,
        }


def round_trips(fills: Iterable[dict] | pd.DataFrame, include_open: bool = False) -> pd.DataFrame:
    """Group fills into flat-to-flat trades per symbol.

    ``fills`` are journal rows (dicts with the ``FILL_COLUMNS``) or a frame of
    them. Fills are taken in time order; ties keep their recorded order. Notes
    come from the fill that opened the trade. ``risk`` is |average entry − stop|
    × quantity entered, and ``r_multiple`` is net P&L over that risk. Open
    trades show realised P&L only.
    """
    frame = fills.copy() if isinstance(fills, pd.DataFrame) else pd.DataFrame(list(fills))
    if frame.empty:
        return pd.DataFrame(columns=list(TRIP_COLUMNS))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["_order"] = np.arange(len(frame))
    frame = frame.sort_values(["timestamp", "_order"], kind="stable", na_position="first")
    notes_cols = [c for c in _NOTE_KEYS if c in frame.columns]
    trips, next_id = [], 1
    for symbol, group in frame.groupby("symbol", sort=False):
        pos, trip = 0, None
        for rec in group.to_dict("records"):
            side = str(rec["side"]).upper()
            if side not in (BUY, SELL):
                raise ValueError(f"unknown side {rec['side']!r}")
            sign = 1 if side == BUY else -1
            qty, price, ts = int(rec["qty"]), float(rec["price"]), rec["timestamp"]
            charges = 0.0 if _is_missing(rec.get("charges")) else float(rec["charges"])
            left = qty
            if pos and (pos > 0) != (sign > 0):                     # closes (part of) the position
                closing = min(qty, abs(pos))
                trip.add(closing, price, charges * closing / qty, ts, opening=False)
                pos += sign * closing
                left -= closing
                if pos == 0:
                    trips.append(trip.row(closed=True))
                    trip = None
            if left:                                                # opens or adds
                if trip is None:
                    notes = {k: rec[k] for k in notes_cols if not _is_missing(rec.get(k))}
                    trip = _Trip(next_id, symbol, sign, notes)
                    next_id += 1
                trip.add(left, price, charges * left / qty, ts, opening=True)
                pos += sign * left
        if trip is not None and include_open:
            trips.append(trip.row(closed=False))
    out = pd.DataFrame(trips, columns=list(TRIP_COLUMNS))
    return out.sort_values(["entry_time", "trip_id"], na_position="first").reset_index(drop=True)


def excursions(trips: pd.DataFrame, bars: pd.DataFrame | dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Add MAE and MFE (per share, in price units and in R) from high/low bars.

    ``bars`` is one OHLC frame (single symbol) or a dict of frames by symbol.
    The window runs from the entry bar to the exit bar inclusive; with daily
    bars the entry day's full range counts, which overstates excursions for
    intraday entries. Also adds ``exit_efficiency``: the share of the best
    favourable move the trade kept.
    """
    out = trips.copy()
    mae, mfe = np.full(len(out), np.nan), np.full(len(out), np.nan)
    for i, t in enumerate(out.itertuples()):
        frame = bars[t.symbol] if isinstance(bars, dict) else bars
        if pd.isna(t.entry_time) or frame is None or frame.empty:
            continue
        daily = bool((frame.index == frame.index.normalize()).all())
        start = t.entry_time.normalize() if daily else t.entry_time
        end = t.exit_time if not pd.isna(t.exit_time) else frame.index[-1]
        window = frame.loc[start:end]
        if window.empty:
            continue
        lo, hi = float(window["low"].min()), float(window["high"].max())
        if t.direction == "LONG":
            mae[i], mfe[i] = min(lo - t.entry_price, 0.0), max(hi - t.entry_price, 0.0)
        else:
            mae[i], mfe[i] = min(t.entry_price - hi, 0.0), max(t.entry_price - lo, 0.0)
    out["mae"], out["mfe"] = mae, mfe
    per_share_risk = (out["entry_price"] - out["stop"]).abs()
    out["mae_r"] = out["mae"] / per_share_risk
    out["mfe_r"] = out["mfe"] / per_share_risk
    per_share_gross = out["gross_pnl"] / out["qty"]
    out["exit_efficiency"] = (per_share_gross / out["mfe"]).where(out["mfe"] > 0)
    return out


def _closed(trips: pd.DataFrame) -> pd.DataFrame:
    return trips[trips["status"] == "CLOSED"] if "status" in trips else trips


def trade_summary(trips: pd.DataFrame) -> dict[str, float]:
    """Review numbers for closed trades: hit rate, payoff, expectancy (₹ and R), SQN, costs, streaks.

    SQN (System Quality Number) is √min(N, 100) × mean(R) / std(R): a rough
    signal-to-noise score for a set of R-multiples, not a significance test.
    """
    t = _closed(trips)
    n = len(t)
    if n == 0:
        return {"trades": 0}
    pnl = t["net_pnl"]
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    streak = longest = 0
    for x in pnl:
        streak = streak + 1 if x <= 0 else 0
        longest = max(longest, streak)
    r = t["r_multiple"].dropna()
    out = {
        "trades": n,
        "win_rate": float((pnl > 0).mean()),
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "payoff_ratio": float(wins.mean() / -losses.mean()) if len(wins) and losses.mean() < 0 else float("inf"),
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
        "expectancy": float(pnl.mean()),
        "net_pnl": float(pnl.sum()),
        "gross_pnl": float(t["gross_pnl"].sum()),
        "charges": float(t["charges"].sum()),
        "largest_win": float(pnl.max()),
        "largest_loss": float(pnl.min()),
        "max_consecutive_losses": int(longest),
        "avg_holding_hours": float(t["holding"].mean() / pd.Timedelta(hours=1)) if t["holding"].notna().any()
        else float("nan"),
        "trades_with_stop": len(r),
        "expectancy_r": float(r.mean()) if len(r) else float("nan"),
        "sqn": float(np.sqrt(min(len(r), 100)) * r.mean() / r.std()) if len(r) > 1 and r.std() > 0
        else float("nan"),
    }
    if "mae" in t and t["mae"].notna().any():
        out["edge_ratio"] = float(t["mfe"].mean() / -t["mae"].mean()) if t["mae"].mean() < 0 else float("inf")
    return out


def trade_breakdown(trips: pd.DataFrame, by: str) -> pd.DataFrame:
    """Closed-trade statistics per group.

    ``by`` is a trade column (``setup``, ``symbol``, ``direction``,
    ``strategy`` ...) or one of ``tags`` (a trade counts once per tag),
    ``weekday`` or ``hour`` (of entry).
    """
    t = _closed(trips).copy()
    if by == "tags":
        t = t.explode("tags")
        t["tags"] = t["tags"].fillna("(untagged)")
    elif by == "weekday":
        t["weekday"] = pd.Categorical(t["entry_time"].dt.day_name(),
                                      ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    elif by == "hour":
        t["hour"] = t["entry_time"].dt.hour
    grouped = t.groupby(by, observed=True)
    table = pd.DataFrame({
        "trades": grouped.size(),
        "win_rate": grouped["net_pnl"].apply(lambda s: float((s > 0).mean())),
        "net_pnl": grouped["net_pnl"].sum(),
        "expectancy": grouped["net_pnl"].mean(),
        "avg_r": grouped["r_multiple"].mean(),
        "profit_factor": grouped["net_pnl"].apply(
            lambda s: float(s[s > 0].sum() / -s[s <= 0].sum()) if s[s <= 0].sum() < 0 else float("inf")),
    })
    return table.sort_values("net_pnl", ascending=False)
