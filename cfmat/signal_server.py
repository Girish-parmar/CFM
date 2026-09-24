"""Tiny HTTP service that the n8n workflows call (Module 15).

Endpoints
    GET  /health                          liveness probe
    GET  /signal?symbol=NIFTYDEMO&fast=20&slow=50
                                          latest SMA-crossover signal
    POST /sentiment  {"texts": [...]}     lexicon sentiment per text + average
    POST /journal    {fill fields}        store a fill in the SQLite trade journal
    GET  /journal                         last 50 journal rows

Run it:  python -m cfmat.signal_server --port 8000

Prices come from ``data/<SYMBOL>.csv`` when that file exists, otherwise from a
synthetic series seeded by the symbol name, so the demo works offline. The
service is for learning only: no authentication, bind it to localhost.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import zlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from .data import DATA_DIR, gbm_prices, load_ohlcv_csv
from .indicators import sma
from .nlp import lexicon_sentiment

JOURNAL_COLUMNS = ("order_id", "symbol", "side", "qty", "price", "charges", "timestamp", "strategy")


def load_close(symbol: str) -> pd.Series:
    path = DATA_DIR / f"{symbol}.csv"
    if path.exists():
        return load_ohlcv_csv(path)["close"]
    return gbm_prices(n=300, seed=zlib.crc32(symbol.encode()), start="2025-01-01")


def compute_signal(symbol: str, fast: int = 20, slow: int = 50) -> dict:
    if not 0 < fast < slow:
        raise ValueError("need 0 < fast < slow")
    close = load_close(symbol)
    f, s = sma(close, fast), sma(close, slow)
    signal = (f > s).astype(int)
    return {
        "symbol": symbol,
        "date": close.index[-1].strftime("%Y-%m-%d"),
        "close": round(float(close.iloc[-1]), 2),
        "fast_sma": round(float(f.iloc[-1]), 2),
        "slow_sma": round(float(s.iloc[-1]), 2),
        "signal": int(signal.iloc[-1]),
        "previous_signal": int(signal.iloc[-2]),
        "changed": bool(signal.iloc[-1] != signal.iloc[-2]),
        "action": _action(int(signal.iloc[-2]), int(signal.iloc[-1])),
    }


def _action(prev: int, cur: int) -> str:
    if cur > prev:
        return "ENTER_LONG"
    if cur < prev:
        return "EXIT_LONG"
    return "HOLD_LONG" if cur else "STAY_FLAT"


def init_journal(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS trade_journal (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   order_id INTEGER, symbol TEXT NOT NULL, side TEXT NOT NULL CHECK (side IN ('BUY','SELL')),
                   qty INTEGER NOT NULL CHECK (qty > 0), price REAL NOT NULL, charges REAL DEFAULT 0,
                   timestamp TEXT, strategy TEXT, received_at TEXT NOT NULL)"""
        )


def make_handler(db_path: str | Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep test output quiet
            pass

        def _send(self, status: int, payload) -> None:
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")

        def do_GET(self):
            url = urlparse(self.path)
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                if url.path == "/health":
                    self._send(200, {"status": "ok"})
                elif url.path == "/signal":
                    self._send(200, compute_signal(query.get("symbol", "NIFTYDEMO").upper(),
                                                   int(query.get("fast", 20)), int(query.get("slow", 50))))
                elif url.path == "/journal":
                    with sqlite3.connect(db_path) as con:
                        con.row_factory = sqlite3.Row
                        rows = con.execute("SELECT * FROM trade_journal ORDER BY id DESC LIMIT 50").fetchall()
                    self._send(200, [dict(r) for r in rows])
                else:
                    self._send(404, {"error": "not found"})
            except ValueError as exc:
                self._send(400, {"error": str(exc)})

        def do_POST(self):
            try:
                payload = self._json_body()
            except json.JSONDecodeError:
                self._send(400, {"error": "body must be JSON"})
                return
            if self.path == "/sentiment":
                texts = payload.get("texts") or ([payload["text"]] if "text" in payload else [])
                results = [{"text": t, **lexicon_sentiment(t)} for t in texts]
                avg = sum(r["score"] for r in results) / len(results) if results else 0.0
                self._send(200, {"count": len(results), "average_score": round(avg, 3), "items": results})
            elif self.path == "/journal":
                missing = [k for k in ("symbol", "side", "qty", "price") if k not in payload]
                if missing:
                    self._send(400, {"error": f"missing fields: {missing}"})
                    return
                row = {k: payload.get(k) for k in JOURNAL_COLUMNS}
                row["side"] = str(row["side"]).upper()
                try:
                    with sqlite3.connect(db_path) as con:
                        con.execute(
                            f"INSERT INTO trade_journal ({', '.join(JOURNAL_COLUMNS)}, received_at) "
                            f"VALUES ({', '.join('?' * len(JOURNAL_COLUMNS))}, ?)",
                            (*row.values(), datetime.now(timezone.utc).isoformat()),
                        )
                        total = con.execute("SELECT COUNT(*) FROM trade_journal").fetchone()[0]
                except sqlite3.IntegrityError as exc:
                    self._send(400, {"error": f"rejected by journal constraints: {exc}"})
                    return
                self._send(201, {"stored": True, "rows": total})
            else:
                self._send(404, {"error": "not found"})

    return Handler


def make_server(host: str = "127.0.0.1", port: int = 8000, db_path: str | Path = "trade_journal.sqlite") -> ThreadingHTTPServer:
    init_journal(db_path)
    return ThreadingHTTPServer((host, port), make_handler(db_path))


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description="CFMAT signal service for n8n workflows")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="trade_journal.sqlite")
    args = parser.parse_args()
    server = make_server(args.host, args.port, args.db)
    print(f"CFMAT signal service on http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover
    main()
