"""Text analytics for markets (Module 22).

sentiment  lexicon sentiment with negation, TF-IDF + logistic-regression classifier
rag        chunking, TF-IDF retrieval, grounded prompts, extractive answers
llm        optional Claude API answer step
"""

from .llm import (
    answer_with_claude,
)
from .rag import (
    Chunk,
    TfidfRetriever,
    build_rag_prompt,
    chunk_text,
    extractive_answer,
    load_filings,
    split_sentences,
)
from .sentiment import (
    NEGATIVE,
    NEGATORS,
    POSITIVE,
    UNCERTAIN,
    lexicon_sentiment,
    load_headlines,
    sentiment_classifier,
    tokenize,
)

__all__ = [
    "NEGATIVE",
    "NEGATORS",
    "POSITIVE",
    "UNCERTAIN",
    "Chunk",
    "TfidfRetriever",
    "answer_with_claude",
    "build_rag_prompt",
    "chunk_text",
    "extractive_answer",
    "lexicon_sentiment",
    "load_filings",
    "load_headlines",
    "sentiment_classifier",
    "split_sentences",
    "tokenize",
]
