# %% [markdown]
# # Lab 14 — NLP, LLMs and RAG for Financial Research (Module 14)
#
# **Goals**
# 1. Score news headlines with a finance-specific sentiment lexicon.
# 2. Train and cross-validate a TF-IDF + logistic regression classifier.
# 3. Build a Retrieval-Augmented Generation (RAG) pipeline over annual reports:
#    chunk → index → retrieve → grounded prompt → cited answer.
# 4. (Optional) generate the answer with Claude when `ANTHROPIC_API_KEY` is set.
#
# All companies and documents in `data/` are fictional.

# %%
import os

import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from cfmat import nlp

headlines = nlp.load_headlines()
print(headlines.label.value_counts().to_string())

# %% [markdown]
# ## 1. Lexicon sentiment

# %%
scores = headlines.headline.apply(nlp.lexicon_sentiment).apply(pd.Series)
headlines = headlines.join(scores)
headlines["lexicon_label"] = pd.cut(headlines.score, [-1.01, -0.01, 0.01, 1.01], labels=["negative", "neutral", "positive"])
accuracy = (headlines.lexicon_label.astype(str) == headlines.label).mean()
print(f"Lexicon accuracy: {accuracy:.1%}")
misses = headlines[headlines.lexicon_label.astype(str) != headlines.label]
print("Misclassified examples:\n", misses[["headline", "label", "lexicon_label"]].head(6).to_string(index=False))

# %% [markdown]
# ## 2. Supervised classifier (TF-IDF + logistic regression)

# %%
cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=0)
predicted = cross_val_predict(nlp.sentiment_classifier(), headlines.headline, headlines.label, cv=cv)
print(classification_report(headlines.label, predicted, zero_division=0))
print("With 48 examples the lexicon's built-in knowledge beats a model that must learn every word from "
      "scratch. In class we fine-tune FinBERT on thousands of labelled Indian market headlines.")

# %% [markdown]
# ## 3. RAG over annual reports

# %%
chunks = nlp.load_filings(chunk_words=80, overlap=20)
retriever = nlp.TfidfRetriever(chunks)
print(f"Indexed {len(chunks)} chunks from {len({c.source for c in chunks})} filings")

questions = [
    "What was Aravalli Steel's EBITDA margin and net debt?",
    "Which Deccan Pharma plant received a USFDA warning letter and why?",
    "How sensitive is Konkan Power's profit to interest rates?",
    "What is Konkan Power's plan for new coal capacity?",
    "What was Vindhya Motors' revenue?",       # no filing for this company — should be declined
]
GENERIC_TITLE_WORDS = {"ltd", "annual", "report", "fictional", "for", "training", "only"}


def entity_guard(question: str, hits: list) -> list:
    """Keep only chunks whose document title shares a name with the question.

    Retrieval always returns *something*; without a guard, a question about a
    company we hold no filing for gets answered from another company's report.
    """
    q_terms = set(nlp.tokenize(question))
    return [(score, chunk) for score, chunk in hits
            if (set(nlp.tokenize(chunk.title)) - GENERIC_TITLE_WORDS) & q_terms]


for question in questions:
    hits = retriever.search(question, k=3)
    print(f"\nQ: {question}")
    for score, chunk in hits:
        print(f"   retrieved {chunk.source} #{chunk.chunk_id} (score {score:.2f})")
    guarded = entity_guard(question, hits)
    print("A (extractive):", nlp.extractive_answer(question, guarded) if guarded else "Not found in the indexed filings.")

naive = nlp.extractive_answer(questions[-1], retriever.search(questions[-1], k=3))
print(f"\nWithout the guard, the last question would get: {naive!r} — confidently wrong.")

# %% [markdown]
# ### The grounded prompt that goes to the LLM

# %%
hits = retriever.search(questions[1], k=3)
prompt = nlp.build_rag_prompt(questions[1], hits)
print(prompt[:900], "...")

# %% [markdown]
# ## 4. Optional: generate the answer with Claude
# `pip install anthropic` and set `ANTHROPIC_API_KEY`. The answer must cite [n]
# sources and decline when the context lacks the answer.

# %%
if os.environ.get("ANTHROPIC_API_KEY"):
    for question in (questions[1], questions[4]):
        hits = retriever.search(question, k=3)
        print(f"\nQ: {question}\nClaude: {nlp.answer_with_claude(question, hits)}")
else:
    print("ANTHROPIC_API_KEY not set — skipping the LLM step (the retrieval pipeline above ran offline).")

# %% [markdown]
# ## Exercises
# 1. Replace TF-IDF with sentence embeddings (e.g. `sentence-transformers`) stored
#    in pgvector or Chroma. Compare retrieval hit rate on 20 hand-written questions.
# 2. Build an evaluation set: for each question, the correct source chunk. Measure
#    recall@3 for chunk sizes 40, 80 and 160 words.
# 3. Aggregate daily headline sentiment per company and test whether it predicts
#    next-day returns (event study from Lab 5).
