"""Tiny HTTP service that the n8n workflows call (M18).

Endpoints
    GET  /health                          liveness probe
    GET  /signal?symbol=NIFTYDEMO&fast=20&slow=50
                                          latest SMA-crossover signal
    POST /sentiment  {"texts": [...]}     lexicon sentiment per text + average
    POST /journal    {fill fields}        store a fill in the SQLite trade journal
    GET  /journal                         last 50 journal rows

Run it:  python -m cfmat.automation.signal_service --port 8000

Prices come from ``data/<SYMBOL>.csv`` (see ``cfmat.infra.paths.user_data_dir``)
when that file exists, otherwise from a synthetic series seeded by the symbol
name, so the demo works offline. The service is for learning only: there is no
authentication, so bind it to localhost. Request bodies over ``MAX_BODY_BYTES``
are refused.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd

from ..analytics.indicators import sma
from ..data import gbm_prices, load_ohlcv_csv
from ..infra.paths import user_data_dir
from ..nlp import lexicon_sentiment
from .journal_store import init_journal, insert_fill, recent_fills

MAX_BODY_BYTES = 1_000_000
_SYMBOL = re.compile(r"^[A-Z0-9_.&-]{1,32}$")


def load_close(symbol: str) -> pd.Series:
    """Closing prices for ``symbol``: the learner's CSV if present, else synthetic."""
    if not _SYMBOL.match(symbol):
        raise ValueError("symbol must be 1-32 characters from A-Z, 0-9, _ . & -")
    path = user_data_dir() / f"{symbol}.csv"
    if path.exists():
        return load_ohlcv_csv(path)["close"]
    return gbm_prices(n=300, seed=zlib.crc32(symbol.encode()), start="2025-01-01")


def compute_signal(symbol: str, fast: int = 20, slow: int = 50) -> dict:
    """Latest SMA-crossover signal for ``symbol`` with the action it implies (enter, exit, hold, stay flat)."""
    if not 0 < fast < slow:
        raise ValueError("need 0 < fast < slow")
    close = load_close(symbol)
    if len(close) < slow + 2:
        raise ValueError(f"need at least {slow + 2} prices, have {len(close)}")
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


class _BadRequest(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def make_handler(db_path: str | Path):
    """Build the HTTP request handler class bound to the journal at ``db_path``."""
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
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                raise _BadRequest(400, "invalid Content-Length") from None
            if length < 0 or length > MAX_BODY_BYTES:
                raise _BadRequest(413, f"body must be at most {MAX_BODY_BYTES} bytes")
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise _BadRequest(400, "body must be JSON") from None
            if not isinstance(payload, dict):
                raise _BadRequest(400, "body must be a JSON object")
            return payload

        def do_GET(self):
            url = urlparse(self.path)
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                if url.path == "/health":
                    self._send(200, {"status": "ok"})
                elif url.path == "/signal":
                    self._send(
                        200,
                        compute_signal(
                            query.get("symbol", "NIFTYDEMO").upper(), int(query.get("fast", 20)), int(query.get("slow", 50))
                        ),
                    )
                elif url.path == "/journal":
                    self._send(200, recent_fills(db_path))
                else:
                    self._send(404, {"error": "not found"})
            except ValueError as exc:
                self._send(400, {"error": str(exc)})

        def do_POST(self):
            try:
                payload = self._json_body()
            except _BadRequest as exc:
                self._send(exc.status, {"error": str(exc)})
                return
            if self.path == "/sentiment":
                texts = payload.get("texts") or ([payload["text"]] if "text" in payload else [])
                if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
                    self._send(400, {"error": "texts must be a list of strings"})
                    return
                results = [{"text": t, **lexicon_sentiment(t)} for t in texts]
                avg = sum(r["score"] for r in results) / len(results) if results else 0.0
                self._send(200, {"count": len(results), "average_score": round(avg, 3), "items": results})
            elif self.path == "/journal":
                try:
                    total = insert_fill(db_path, payload)
                except ValueError as exc:
                    self._send(400, {"error": str(exc)})
                    return
                except sqlite3.IntegrityError as exc:
                    self._send(400, {"error": f"rejected by journal constraints: {exc}"})
                    return
                self._send(201, {"stored": True, "rows": total})
            else:
                self._send(404, {"error": "not found"})

    return Handler


def make_server(host: str = "127.0.0.1", port: int = 8000, db_path: str | Path = "trade_journal.sqlite") -> ThreadingHTTPServer:
    """Create the journal if needed and return a threaded HTTP server (call ``serve_forever``)."""
    init_journal(db_path)
    return ThreadingHTTPServer((host, port), make_handler(db_path))


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry point
    """Command-line entry point: ``python -m cfmat.automation.signal_service --port 8000``."""
    parser = argparse.ArgumentParser(description="CFMAT signal service for n8n workflows")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default="trade_journal.sqlite")
    args = parser.parse_args(argv)
    server = make_server(args.host, args.port, args.db)
    print(f"CFMAT signal service on http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":  # pragma: no cover
    main()
