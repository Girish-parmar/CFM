import json
import threading
import urllib.request
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from cfmat import broker as brk
from cfmat import data, ml, nlp, rl, signal_server


def test_paper_broker_accounting_round_trip():
    b = brk.PaperBroker(cash=100_000, slippage_bps=0)
    b.update_price("ABC", 100.0)
    b.place_order(brk.Order("ABC", brk.BUY, 100))
    b.update_price("ABC", 110.0)
    assert b.equity() == pytest.approx(101_000)
    b.place_order(brk.Order("ABC", brk.SELL, 150))  # close 100, open short 50
    assert b.realized_pnl == pytest.approx(1_000) and b.position("ABC") == -50
    b.update_price("ABC", 100.0)
    assert b.equity() == pytest.approx(101_500)


def test_limit_orders_rest_then_fill():
    b = brk.PaperBroker(cash=100_000, slippage_bps=0)
    b.update_price("ABC", 100.0)
    o = b.place_order(brk.Order("ABC", brk.BUY, 10, brk.LIMIT, 98.0))
    assert o.status == "OPEN"
    b.update_price("ABC", 97.5)
    assert o.status == "FILLED" and b.fills[-1].price == 98.0


def test_risk_manager_blocks_bad_orders():
    limits = brk.RiskLimits(max_order_qty=100, max_order_value=50_000, max_position_qty=150,
                            max_orders_per_second=2, max_daily_loss=1_000)
    b = brk.PaperBroker(cash=1_000_000, risk=brk.RiskManager(limits), slippage_bps=0)
    b.update_price("ABC", 100.0)
    ts = datetime(2026, 1, 5, 10, 0, 0)
    assert "exceeds" in b.place_order(brk.Order("ABC", brk.BUY, 101), ts).reject_reason
    assert "fat-finger" in b.place_order(brk.Order("ABC", brk.BUY, 10, brk.LIMIT, 120.0), ts).reject_reason
    assert b.place_order(brk.Order("ABC", brk.BUY, 100), ts).status == "FILLED"
    assert b.place_order(brk.Order("ABC", brk.BUY, 40), ts).status == "FILLED"
    assert "throttled" in b.place_order(brk.Order("ABC", brk.BUY, 5), ts).reject_reason
    b.update_price("ABC", 90.0)  # loss of 1,400 > limit
    later = datetime(2026, 1, 5, 10, 0, 5)
    assert "kill switch" in b.place_order(brk.Order("ABC", brk.SELL, 10), later).reject_reason
    b.square_off_all()
    assert b.positions() == {}


def test_triple_barrier_labels_and_purged_cv():
    close = data.ar1_prices(600, seed=3)
    lab = ml.triple_barrier_labels(close, horizon=10)
    valid = lab.dropna()
    assert set(valid["label"].unique()) <= {-1.0, 1.0}
    assert (valid["exit_pos"] > np.arange(len(close))[lab["label"].notna()]).all()
    n, h, emb = 500, 10, 5
    for train, test in ml.purged_kfold(n, 5, horizon=h, embargo=emb):
        assert len(np.intersect1d(train, test)) == 0
        # no training label may overlap the test window
        assert not np.any((train + h >= test[0]) & (train <= test[-1] + h))


def test_walk_forward_splits_respect_gap():
    for train, test in ml.walk_forward_splits(300, 100, 50, gap=10):
        assert test[0] - train[-1] == 11


def test_ml_pipeline_runs_end_to_end():
    bars = data.ohlcv_from_close(data.ar1_prices(800, phi=0.15, seed=5), seed=5)
    X = ml.make_features(bars)
    lab = ml.triple_barrier_labels(bars["close"], horizon=5)
    df = X.join(lab).dropna()
    y = (df["label"] > 0).astype(int)
    splits = ml.walk_forward_splits(len(df), 300, 100, gap=5)
    proba = ml.out_of_fold_proba(lambda: LogisticRegression(max_iter=500), df[X.columns], y, splits)
    assert proba.notna().sum() == 400
    assert set(ml.proba_to_position(proba.dropna()).unique()) <= {-1.0, 0.0, 1.0}


def test_q_learning_learns_obvious_pattern():
    # Returns alternate sign: after an up day, the next day is down.
    r = pd.Series(np.tile([0.01, -0.01], 300))
    agent = rl.QLearningTrader(n_lags=1, epsilon=0.2, cost=0.0, seed=1).fit(r, episodes=30)
    pos = agent.positions(r)
    earned = (pos.shift(1) * r).sum()
    assert earned > 2.0


def test_lexicon_sentiment_with_negation():
    assert nlp.lexicon_sentiment("Profit surged to a record")["score"] == 1.0
    assert nlp.lexicon_sentiment("Company posts loss and faces probe")["score"] == -1.0
    assert nlp.lexicon_sentiment("Results were not strong")["score"] == -1.0
    assert nlp.lexicon_sentiment("Board meeting on Friday")["score"] == 0.0


def test_rag_retrieval_finds_right_filing():
    retriever = nlp.TfidfRetriever(nlp.load_filings(chunk_words=80, overlap=20))
    hits = retriever.search("Which plant received a USFDA warning letter?", k=3)
    assert hits[0][1].source == "deccan_pharma_fy26.md"
    prompt = nlp.build_rag_prompt("question?", hits)
    assert "[1]" in prompt and "deccan_pharma_fy26.md" in prompt
    assert "Visakhapatnam" in nlp.extractive_answer("Which plant received a USFDA warning letter?", hits)


def test_chunking_covers_all_words():
    text = " ".join(f"w{i}" for i in range(250))
    chunks = nlp.chunk_text(text, "t", chunk_words=100, overlap=20)
    seen = set(" ".join(c.text for c in chunks).split())
    assert seen == set(text.split())


@pytest.fixture()
def server(tmp_path):
    srv = signal_server.make_server("127.0.0.1", 0, tmp_path / "j.sqlite")
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
