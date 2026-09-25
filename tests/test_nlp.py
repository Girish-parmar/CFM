"""Tests for cfmat.nlp: sentiment, retrieval-augmented generation and news signals."""

import numpy as np
import pandas as pd
import pytest

from cfmat import data, nlp
from cfmat.analytics import stats


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


# -- news to signals (M22) --------------------------------------------------------------------------

def test_news_events_dedupe_and_align_to_the_session_that_can_act():
    news, close, truth = data.news_stream(n_days=250, seed=5)
    events = nlp.news_events(news, close.index)
    assert len(events) == len(truth["events"]) < len(news)                       # re-publications dropped
    merged = events.merge(truth["events"], on=["ts", "symbol"])
    assert (merged["session_x"] == merged["session_y"]).all()
    friday_evening = pd.DataFrame({"ts": [pd.Timestamp("2024-01-05 18:00")], "symbol": ["X"],
                                   "headline": ["X posts record profit"]})
    assert nlp.news_events(friday_evening, close.index)["session"].iloc[0] == pd.Timestamp("2024-01-08")


def test_news_signal_is_causal_and_decays_with_its_half_life():
    days = pd.bdate_range("2024-01-01", periods=10)
    events = pd.DataFrame({"session": [days[2]], "symbol": ["X"], "score": [2.0]})
    signal = nlp.news_signal(events, days, ["X"], half_life=2.0)["X"]
    assert (signal.iloc[:2] == 0).all() and signal.iloc[2] == pytest.approx(2.0)
    assert signal.iloc[4] == pytest.approx(1.0)                                  # halved after two days
    early = nlp.news_signal(events, days[:5], ["X"], half_life=2.0)["X"]
    pd.testing.assert_series_equal(early, signal.iloc[:5])


def test_news_pipeline_recovers_the_planted_response_and_it_decays_with_delay():
    news, close, truth = data.news_stream(seed=22)
    events = nlp.news_events(news, close.index)
    market = close.pct_change().mean(axis=1)
    abnormal = (1 + close.pct_change().sub(market, axis=0).fillna(0)).cumprod()
    positive = (events[events["score"] > 0].pivot_table(index="session", columns="symbol", values="score",
                                                         aggfunc="size")
                .reindex(index=close.index, columns=close.columns).fillna(0) > 0)
    table = stats.event_study(abnormal, positive, horizons=(5,), n_perm=300)
    p = truth["params"]
    planted = p["drift"] * sum(0.5 ** (k / p["half_life"]) for k in range(5))
    assert table.loc["5d", "excess"] == pytest.approx(planted, rel=0.35) and table.loc["5d", "p_value"] < 0.05
    signal = nlp.news_signal(events, close.index, list(close.columns), half_life=p["half_life"])
    rets = close.pct_change().fillna(0)

    def sharpe(delay):
        w = np.sign(signal).shift(1 + delay).fillna(0)
        w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        r = (w * rets).sum(axis=1)
        return r.mean() / r.std() * np.sqrt(252)

    assert sharpe(0) > 1.0 and sharpe(2) < 0.6 * sharpe(0) and sharpe(5) < 0.2
