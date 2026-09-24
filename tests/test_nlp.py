"""Tests for cfmat.nlp: sentiment and retrieval-augmented generation."""

from cfmat import nlp


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
