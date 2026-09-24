"""NLP, LLMs and Retrieval-Augmented Generation for financial research (Module 14).

Pipeline taught in class:

    documents → chunk → index (TF-IDF here; embeddings + vector DB in the
    advanced lab) → retrieve top-k → build a grounded prompt → LLM answer
    with citations.

Everything except ``answer_with_claude`` runs offline. That function needs
``pip install anthropic`` and an ``ANTHROPIC_API_KEY``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

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
    return pd.read_csv(path or DATA_DIR / "sample_headlines.csv")


def sentiment_classifier(C: float = 2.0) -> Pipeline:
    """TF-IDF (uni + bigrams) → logistic regression. The classic strong baseline
    before reaching for FinBERT or an LLM."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)),
        ("clf", LogisticRegression(C=C, max_iter=1000)),
    ])


# ---------------------------------------------------------------------------
# Retrieval-Augmented Generation
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    source: str
    chunk_id: int
    text: str
    title: str = ""


_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if s.strip()]


def chunk_text(text: str, source: str, chunk_words: int = 120, overlap: int = 30, title: str = "") -> list[Chunk]:
    """Pack whole sentences into chunks of about ``chunk_words`` words.

    Consecutive chunks share trailing sentences worth up to ``overlap`` words, so
    a fact near a boundary appears intact in at least one chunk.
    """
    if overlap >= chunk_words:
        raise ValueError("overlap must be smaller than chunk_words")
    sentences = split_sentences(text)
    chunks: list[Chunk] = []
    current: list[str] = []
    for sentence in sentences:
        if current and len(" ".join(current + [sentence]).split()) > chunk_words:
            chunks.append(Chunk(source, len(chunks), " ".join(current), title))
            carry: list[str] = []
            for prev in reversed(current):
                if len(" ".join([prev] + carry).split()) > overlap:
                    break
                carry.insert(0, prev)
            current = carry
        current.append(sentence)
    if current:
        chunks.append(Chunk(source, len(chunks), " ".join(current), title))
    return chunks


def load_filings(directory: str | Path | None = None, **chunk_kwargs) -> list[Chunk]:
    """Chunk every .md/.txt file in ``directory`` (default: data/filings).

    The first ``# heading`` becomes the document title and is attached to every
    chunk (a "contextual chunk header"), so a chunk about net debt still knows
    which company it belongs to. Other heading lines are dropped from the body.
    """
    directory = Path(directory or DATA_DIR / "filings")
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*")):
        if path.suffix not in (".md", ".txt"):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        title = next((ln.lstrip("# ").strip() for ln in lines if ln.startswith("# ")), path.stem)
        body = " ".join(ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#"))
        chunks += chunk_text(body, path.name, title=title, **chunk_kwargs)
    return chunks


class TfidfRetriever:
    """Sparse retriever. Swap for sentence embeddings + FAISS/pgvector/Chroma in
    the advanced exercise; the interface stays the same."""

    def __init__(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("no chunks to index")
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self.matrix = self.vectorizer.fit_transform([f"{c.title} {c.text}" for c in chunks])

    def search(self, query: str, k: int = 3) -> list[tuple[float, Chunk]]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        top = np.argsort(scores)[::-1][:k]
        return [(float(scores[i]), self.chunks[i]) for i in top if scores[i] > 0]


def build_rag_prompt(question: str, hits: list[tuple[float, Chunk]]) -> str:
    """Grounded prompt: numbered sources, cite-or-decline instruction."""
    sources = "\n\n".join(
        f"[{n}] {chunk.title} ({chunk.source}, chunk {chunk.chunk_id})\n{chunk.text}"
        for n, (_, chunk) in enumerate(hits, 1)
    )
    return (
        "You are a financial research assistant. Answer the question using only the sources below. "
        "Cite sources like [1] after each claim. If the sources do not contain the answer, say so "
        "plainly rather than guessing. Do not give buy/sell recommendations.\n\n"
        f"Sources:\n{sources}\n\nQuestion: {question}"
    )


def extractive_answer(question: str, hits: list[tuple[float, Chunk]], max_sentences: int = 2) -> str:
    """Offline fallback: return the retrieved sentences that best overlap the question."""
    q_terms = set(tokenize(question)) - ENGLISH_STOP_WORDS - NEGATORS
    scored, seen = [], set()
    for n, (_, chunk) in enumerate(hits, 1):
        for sentence in split_sentences(chunk.text):
            if sentence in seen:
                continue  # overlapping chunks repeat sentences
            seen.add(sentence)
            overlap = len(q_terms & set(tokenize(sentence)))
            if overlap:
                scored.append((overlap, f"{sentence} [{n}]"))
    if not scored:
        return "The retrieved sources do not answer this question."
    scored.sort(key=lambda s: s[0], reverse=True)
    return " ".join(s for _, s in scored[:max_sentences])


def answer_with_claude(question: str, hits: list[tuple[float, Chunk]], model: str | None = None) -> str:
    """Generate a cited answer with Claude.

    Uses the model in ``CFMAT_CLAUDE_MODEL`` if set, else ``claude-opus-5``.
    Server-side fallbacks are enabled so a declined request is retried on
    Anthropic's recommended fallback model instead of failing outright.
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("Install the LLM extra: pip install anthropic") from exc

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    response = client.beta.messages.create(
        model=model or os.environ.get("CFMAT_CLAUDE_MODEL", "claude-opus-5"),
        max_tokens=16000,
        thinking={"type": "adaptive"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": build_rag_prompt(question, hits)}],
    )
    if response.stop_reason == "refusal":
        return "The model declined to answer this request."
    return "".join(block.text for block in response.content if block.type == "text").strip()
