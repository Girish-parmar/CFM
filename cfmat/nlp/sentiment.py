"""Financial sentiment: a Loughran-McDonald-style lexicon with negation, and a
TF-IDF + logistic-regression baseline classifier (M22).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ..infra.paths import SAMPLE_DATA_DIR

# A small teaching lexicon in the spirit of Loughran & McDonald (2011): words
# chosen for their meaning in *financial* text. For research, use the full
# Loughran–McDonald dictionary under its licence terms.
POSITIVE = {
    "beat", "beats", "surge", "surged", "record", "growth", "grew", "upgrade", "upgraded", "profit",
    "profits", "gain", "gains", "strong", "robust", "outperform", "outperformed", "expansion",
    "improved", "improvement", "dividend", "buyback", "rally", "rallied", "wins", "win", "won",
    "approval", "approved", "higher", "exceeds", "exceeded", "bullish", "margin-expansion", "rebound",
}


NEGATIVE = {
    "miss", "missed", "misses", "loss", "losses", "decline", "declined", "downgrade", "downgraded",
    "weak", "fraud", "default", "defaults", "penalty", "fine", "fined", "probe", "slump", "slumped",
    "plunge", "plunged", "lawsuit", "impairment", "writedown", "lower", "bearish", "resigns",
    "resigned", "delay", "delayed", "shortfall", "breach", "halt", "halted", "crash", "pledge",
}


UNCERTAIN = {
    "may", "might", "uncertain", "uncertainty", "volatile", "volatility", "risk", "risks", "possible",
    "pending", "unclear", "approximately", "depends", "contingent", "could",
}


NEGATORS = {"not", "no", "never", "without", "neither", "nor"}


_TOKEN = re.compile(r"[a-z][a-z\-']*")


def tokenize(text: str) -> list[str]:
    """Lower-case word tokens (letters and apostrophes)."""
    return _TOKEN.findall(text.lower())


def lexicon_sentiment(text: str) -> dict[str, float]:
    """Count lexicon hits; a negator in the previous two tokens flips polarity.

    ``score`` = (pos − neg) / (pos + neg), in [−1, 1]; 0 when neither appears.
    """
    tokens = tokenize(text)
    pos = neg = unc = 0
    for i, tok in enumerate(tokens):
        negated = any(t in NEGATORS for t in tokens[max(0, i - 2) : i])
        if tok in POSITIVE:
            neg, pos = (neg + 1, pos) if negated else (neg, pos + 1)
        elif tok in NEGATIVE:
            pos, neg = (pos + 1, neg) if negated else (pos, neg + 1)
        if tok in UNCERTAIN:
            unc += 1
    total = pos + neg
    return {"positive": pos, "negative": neg, "uncertainty": unc,
            "score": (pos - neg) / total if total else 0.0}


def load_headlines(path: str | Path | None = None) -> pd.DataFrame:
    """Labelled sample headlines (fictional companies) with columns headline, label."""
    return pd.read_csv(path or SAMPLE_DATA_DIR / "sample_headlines.csv")


def sentiment_classifier(C: float = 2.0) -> Pipeline:
    """TF-IDF (uni + bigrams) → logistic regression. The classic strong baseline
    before reaching for FinBERT or an LLM."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(C=C, max_iter=1000)),
    ])
