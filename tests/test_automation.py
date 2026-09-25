"""Tests for cfmat.automation: the signal service, trade journal and live monitoring."""

import json
import sqlite3
import threading
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest

from cfmat import trading
from cfmat.automation import journal_store, signal_service
from cfmat.automation import monitoring as mon


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


# -- live monitoring (M18) ----------------------------------------------------------------------


def test_heartbeat_gaps_find_a_dead_process_including_at_the_edges():
    beats = pd.date_range("2026-01-05 09:15", "2026-01-05 10:00", freq="10s")
    beats = beats[(beats < "2026-01-05 09:30") | (beats > "2026-01-05 09:33")]            # dead for 3 minutes
    gaps = mon.heartbeat_gaps(beats, every="10s", tolerance=3, end="2026-01-05 10:05")
    assert len(gaps) == 2                                                                  # the pause, and after 10:00
    assert gaps.iloc[0]["missed"] == 19 and gaps.iloc[0]["detected_at"] == pd.Timestamp("2026-01-05 09:30:20")
    assert mon.heartbeat_gaps(pd.date_range("2026-01-05 09:15", periods=100, freq="10s")).empty


def test_staleness_finds_the_outage_and_the_frozen_price_and_nothing_on_a_clean_day():
    from cfmat import data

    ticks, truth = data.tick_stream(seed=3)
    incidents = mon.staleness(ticks, check_every="5s", max_age="30s", frozen_after="30s")
    periods = truth["periods"].set_index("kind")
    assert sorted(incidents["kind"]) == ["frozen", "no_updates"]
    for kind, planted in (("no_updates", "outage"), ("frozen", "stale")):
        row = incidents.set_index("kind").loc[kind]
        assert periods.loc[planted, "start"] < row["start"] < periods.loc[planted, "end"] + pd.Timedelta("10s")
    clean, _ = data.tick_stream(seed=3, faults=False)
    assert mon.staleness(clean).empty


def test_drift_report_flags_planted_drift_and_passes_a_faithful_copy():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2026-01-01", periods=250)
    backtest = pd.Series(rng.normal(0.0006, 0.01, 250), idx)
    signals = pd.Series(rng.choice([-1, 0, 1], 250), idx)
    fills = pd.DataFrame({"side": rng.choice(["BUY", "SELL"], 200), "model_price": 1000.0})
    fair = fills.assign(fill_price=1000 * (1 + np.where(fills["side"] == "BUY", 1, -1) * rng.normal(2, 3, 200) / 1e4))
    faithful = mon.drift_report(backtest + rng.normal(0, 0.0005, 250), backtest, signals, signals, fair,
                                expected_slippage_bps=2)
    assert not faithful["drift"]
    worse = fills.assign(fill_price=1000 * (1 + np.where(fills["side"] == "BUY", 1, -1) * rng.normal(8, 3, 200) / 1e4))
    flipped = signals.copy()
    flipped.iloc[:30] = -flipped.iloc[:30]
    lagging = backtest - 0.002 + rng.normal(0, 0.0005, 250)                       # 20 bp a day behind
    drifted = mon.drift_report(lagging, backtest, flipped, signals, worse, expected_slippage_bps=2)
    assert drifted["tracking_drift"] and drifted["slippage_drift"] and drifted["signal_drift"]
    assert not drifted["distribution_drift"]        # a 0.2-sd shift is invisible to KS in a year; tracking sees it
    wilder = mon.drift_report(backtest * 2.0, backtest)                           # risk doubled
    assert wilder["distribution_drift"]


def test_pnl_attribution_adds_up_to_the_broker_equity_change():
    from cfmat import data
    from cfmat.microstructure.costs import IndianCostModel

    close = data.gbm_prices(30, s0=1000, seed=3, start="2026-01-05")
    broker = trading.PaperBroker(cash=1_000_000, slippage_bps=5, cost_model=IndianCostModel())
    rng, rows, equity = np.random.default_rng(1), [], []
    for day, c in close.items():
        decision = c * (1 + rng.normal(0, 0.004))
        ts = day + pd.Timedelta("10:00:00")
        broker.update_price("ABC", decision, ts)
        if rng.random() < 0.6:
            side, qty = ("BUY" if rng.random() < 0.5 else "SELL"), int(rng.integers(10, 60))
            broker.place_order(trading.Order("ABC", side, qty), ts)
            fill = broker.fills[-1]
            rows.append({"ts": ts, "symbol": "ABC", "side": side, "qty": qty, "decision_price": decision,
                         "fill_price": fill.price, "charges": fill.charges})
        broker.update_price("ABC", c, day + pd.Timedelta("15:29:00"))
        equity.append(broker.equity())
    parts = mon.pnl_attribution(pd.DataFrame(rows), close.rename("ABC"))
    change = pd.Series(equity, index=close.index).diff().fillna(equity[0] - 1_000_000)
    np.testing.assert_allclose(parts["total"], change, atol=1e-6)
    assert parts["execution"].sum() < 0 and parts["costs"].sum() < 0          # slippage and charges only ever cost


def test_alert_manager_fires_reminds_resolves_and_survives_a_broken_sink():
    received = []

    def broken(alert):
        raise ConnectionError("n8n is down")

    manager = mon.AlertManager([mon.AlertRule("stale feed", "feed_age_s", ">", 30, "critical", cooldown="5min"),
                                mon.AlertRule("slippage", "slippage_bps", ">", 10, "warning")],
                               sinks=[received.append, broken])
    t0 = pd.Timestamp("2026-01-05 11:00")
    statuses = []
    for minute, age in enumerate([5, 45, 50, 55, 60, 65, 70, 10]):
        alerts = manager.evaluate({"feed_age_s": age, "slippage_bps": 12 if minute == 1 else 3},
                                  t0 + pd.Timedelta(minutes=minute))
        statuses.append([(a.rule, a.status) for a in alerts])
    assert statuses[1] == [("stale feed", "firing"), ("slippage", "firing")]      # critical first
    assert statuses[2] == [("slippage", "resolved")] and statuses[3] == []          # de-duplicated
    assert statuses[6] == [("stale feed", "reminder")] and statuses[7] == [("stale feed", "resolved")]
    assert len(received) == len(manager.history) == 5 and len(manager.failures) == 5
    with pytest.raises(ValueError, match="op must be"):
        mon.AlertRule("bad", "x", "=>", 1)


def test_webhook_sink_posts_json(tmp_path):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    bodies = []

    class Hook(BaseHTTPRequestHandler):
        def do_POST(self):
            bodies.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Hook)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        sink = mon.webhook_sink(f"http://127.0.0.1:{server.server_address[1]}/webhook/cfmat-alert")
        mon.AlertManager([mon.AlertRule("loss", "day_pnl", "<", -1000, "critical")], [sink]).evaluate(
            {"day_pnl": -2500.0}, "2026-01-05 12:00")
    finally:
        server.shutdown()
    assert bodies[0]["rule"] == "loss" and bodies[0]["status"] == "firing" and bodies[0]["ts"].startswith("2026-01-05T12")
