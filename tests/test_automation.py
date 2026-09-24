"""Tests for cfmat.automation: the signal service and trade journal."""

import json
import sqlite3
import threading
import urllib.error
import urllib.request

import pandas as pd
import pytest

from cfmat.automation import journal_store, signal_service


@pytest.fixture()
def server(tmp_path):
    srv = signal_service.make_server("127.0.0.1", 0, tmp_path / "j.sqlite")
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _call(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read())


def test_signal_server_endpoints(server):
    assert _call(f"{server}/health") == (200, {"status": "ok"})
    status, sig = _call(f"{server}/signal?symbol=niftydemo&fast=10&slow=30")
    assert status == 200 and sig["symbol"] == "NIFTYDEMO" and sig["signal"] in (0, 1)
    assert _call(f"{server}/signal?symbol=NIFTYDEMO")[1] == _call(f"{server}/signal?symbol=NIFTYDEMO")[1]
    status, sent = _call(f"{server}/sentiment", {"texts": ["record profit", "fraud probe"]})
    assert sent["count"] == 2 and sent["average_score"] == 0.0
    status, stored = _call(f"{server}/journal", {"symbol": "ABC", "side": "buy", "qty": 10, "price": 101.5})
    assert status == 201 and stored["rows"] == 1
    assert _call(f"{server}/journal")[1][0]["side"] == "BUY"
    with pytest.raises(urllib.error.HTTPError) as err:
        _call(f"{server}/journal", {"symbol": "ABC", "side": "HOLD", "qty": 1, "price": 1})
    assert err.value.code == 400


def _post_raw(url, body: bytes, headers=None):
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **(headers or {})})
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(req)
    return err.value.code, json.loads(err.value.read())


def test_signal_service_rejects_bad_requests(server):
    assert _post_raw(f"{server}/sentiment", b"[1, 2]")[0] == 400                 # not a JSON object
    assert _post_raw(f"{server}/sentiment", b"{not json")[0] == 400
    assert _post_raw(f"{server}/sentiment", json.dumps({"texts": "one"}).encode())[0] == 400
    code, body = _post_raw(f"{server}/journal", b"{}", {"Content-Length": str(signal_service.MAX_BODY_BYTES + 1)})
    assert code == 413 and "at most" in body["error"]
    with pytest.raises(urllib.error.HTTPError) as err:
        _call(f"{server}/signal?symbol=../../etc/passwd")
    assert err.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as err:
        _call(f"{server}/signal?fast=50&slow=20")
    assert err.value.code == 400


def test_journal_store_round_trip(tmp_path):
    db = tmp_path / "j.sqlite"
    journal_store.init_journal(db)
    assert journal_store.insert_fill(db, {"symbol": "ABC", "side": "sell", "qty": 5, "price": 10.0}) == 1
    assert journal_store.insert_fill(db, {"symbol": "XYZ", "side": "BUY", "qty": 1, "price": 99.0}) == 2
    rows = journal_store.recent_fills(db, limit=1)
    assert [r["symbol"] for r in rows] == ["XYZ"]
    with pytest.raises(ValueError, match="missing"):
        journal_store.insert_fill(db, {"symbol": "ABC"})
    with pytest.raises(sqlite3.IntegrityError):
        journal_store.insert_fill(db, {"symbol": "ABC", "side": "BUY", "qty": 0, "price": 1.0})


def test_user_price_file_overrides_synthetic(tmp_path, monkeypatch):
    idx = pd.bdate_range("2025-01-01", periods=80)
    close = pd.Series(range(100, 180), index=idx, dtype=float)
    frame = pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1000}, index=idx)
    frame.rename_axis("date").to_csv(tmp_path / "MYSTOCK.csv")
    monkeypatch.setenv("CFMAT_DATA_DIR", str(tmp_path))
    sig = signal_service.compute_signal("MYSTOCK", 5, 20)
    assert sig["close"] == 179.0 and sig["signal"] == 1 and sig["action"] == "HOLD_LONG"
