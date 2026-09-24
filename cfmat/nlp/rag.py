"""Retrieval-Augmented Generation building blocks: sentence-aware chunking with
contextual headers, a TF-IDF retriever, grounded prompts and an offline
extractive answer (Module 22).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..infra.paths import SAMPLE_DATA_DIR
from .sentiment import NEGATORS, tokenize


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
    directory = Path(directory or SAMPLE_DATA_DIR / "filings")
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
