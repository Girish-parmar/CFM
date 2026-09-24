"""SQLite trade journal used by the signal service and the n8n workflows (M18).

Constraints live in the schema (side must be BUY/SELL, qty > 0), so bad rows are
rejected by the database even if a caller skips validation.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

JOURNAL_COLUMNS = ("order_id", "symbol", "side", "qty", "price", "charges", "timestamp", "strategy")
REQUIRED_FIELDS = ("symbol", "side", "qty", "price")

_SCHEMA = """CREATE TABLE IF NOT EXISTS trade_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER, symbol TEXT NOT NULL, side TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
    qty INTEGER NOT NULL CHECK (qty > 0), price REAL NOT NULL, charges REAL DEFAULT 0,
    timestamp TEXT, strategy TEXT, received_at TEXT NOT NULL)"""


def init_journal(db_path: str | Path) -> None:
    """Create the journal table if it does not exist."""
    with sqlite3.connect(db_path) as con:
        con.execute(_SCHEMA)


def insert_fill(db_path: str | Path, payload: dict) -> int:
    """Store one fill and return the new row count.

    Raises ``ValueError`` for missing fields and ``sqlite3.IntegrityError`` for rows
    the schema rejects.
    """
    missing = [k for k in REQUIRED_FIELDS if k not in payload]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    row = {k: payload.get(k) for k in JOURNAL_COLUMNS}
    row["side"] = str(row["side"]).upper()
    with sqlite3.connect(db_path) as con:
        con.execute(
            f"INSERT INTO trade_journal ({', '.join(JOURNAL_COLUMNS)}, received_at) "
            f"VALUES ({', '.join('?' * len(JOURNAL_COLUMNS))}, ?)",
            (*row.values(), datetime.now(timezone.utc).isoformat()),
        )
        return con.execute("SELECT COUNT(*) FROM trade_journal").fetchone()[0]


def recent_fills(db_path: str | Path, limit: int = 50) -> list[dict]:
    """The newest ``limit`` journal rows, newest first."""
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM trade_journal ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    return [dict(r) for r in rows]
