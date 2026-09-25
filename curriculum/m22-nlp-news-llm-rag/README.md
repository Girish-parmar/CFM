# M22 · NLP, News Sentiment, LLMs and RAG

<!-- BEGIN GENERATED: module-header -->
<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->
|  |  |
|---|---|
| Term | T5 · AI for Trading |
| Weeks | 43–44 |
| Hours | 24 guided |
| Labs | [22a](lab_22a_sentiment_rag.py) — Lexicon and TF-IDF sentiment, RAG with relevance guard, optional Claude<br>[22b](lab_22b_news_signal_event_study.py) — Timestamped news to signals: dedupe, session alignment, decay, pooled event study, delay sweep |
| Library | `cfmat.nlp` |
| Prerequisites | [M06](../m06-technical-analysis-patterns/README.md), [M19](../m19-machine-learning/README.md) |
| Committed topics | Sentiment and news analysis, Macroeconomics |
| Status | ready |
<!-- END GENERATED: module-header -->

## Why this module

News, exchange announcements, annual reports and earnings calls move prices, and language models
can now read them at scale. Two questions matter for a trader: does a text signal predict returns
after costs and delays, and can an LLM answer questions about filings without making things up?
This module answers both with event studies and retrieval-augmented generation that cites its
sources and refuses when the sources are silent.

## Learning outcomes

By the end of the module you can:

1. Turn financial text into features: tokenisation, finance lexicons (Loughran–McDonald style) with negation, TF-IDF.
2. Train and compare sentiment classifiers (lexicon, TF-IDF + logistic regression, transformer models such as FinBERT) fairly.
3. Test whether a text signal predicts returns with an event study that respects timestamps, publication delays and decay.
4. Build a RAG system: sentence-aware chunking with contextual headers, retrieval, grounded prompts with citations, and a relevance guard.
5. Evaluate RAG (retrieval recall, faithfulness, citation accuracy) and defend against hallucination and prompt injection.
6. Call an LLM (Claude) safely and control cost, latency and data-privacy risk.

## Before you start

- M06 (event studies) and M19 (classification, validation) complete.
- Optional: `pip install anthropic` and an `ANTHROPIC_API_KEY` for the LLM step.

## Weekly plan

### Week 43 — News, sentiment and event studies

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz on M21 · 15–60 text as data: tokens, n-grams, TF-IDF; finance lexicons and why general sentiment lexicons fail on finance · 60–70 break · 70–120 negation, uncertainty and litigation words; transformer models and FinBERT · 120–170 live: Lab 22a §1–§2 — lexicon vs TF-IDF classifier · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 from headline to signal: timestamps, market hours, publication delay, deduplication, aggregation by stock and day, decay · 60–70 break · 70–130 workshop: a news-sentiment event study with `analytics.stats.event_study` · 130–170 case: results-day announcements and index moves (data ≥ 3 months old) · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–10 setup · 10–100 Lab 22b: timestamped headlines → stories → signal → pooled event study → delay sweep · 100–120 blockers |
| OH · Wed · 60 min | NLP Q&A |
| C2 · Thu · 120 min | 0–60 classifier comparison with a held-out, time-ordered split · 60–100 peer review · 100–120 review |
| QP · Fri · 60 min | 0–20 quiz 22a · 20–50 label 30 headlines and measure inter-annotator agreement · 50–60 preview |
| Self-study · ~6 h | Loughran and McDonald (2011); Tetlock (2007) |

### Week 44 — LLMs and retrieval-augmented generation for research

| Session | Time-boxed plan |
|---|---|
| L1 · Sat · 180 min | 0–15 retrieval quiz · 15–60 LLMs for extraction and summarisation; what they are bad at (numbers, dates, citations) · 60–70 break · 70–120 RAG architecture: chunking, embeddings vs TF-IDF, retrieval, reranking, grounded prompts with numbered sources · 120–170 live: Lab 22a §3–§4 — RAG over annual reports; the relevance guard; the Claude call · 170–180 exit ticket |
| L2 · Sun · 180 min | 0–10 recap · 10–60 evaluation: retrieval recall@k, faithfulness, citation accuracy; building a small evaluation set · 60–70 break · 70–130 workshop: evaluate the lab's RAG on 20 questions, including 5 that must be refused · 130–170 risks: hallucination, prompt injection in retrieved documents, data privacy, cost control · 170–180 exit ticket |
| C1 · Tue · 120 min | 0–100 RAG evaluation set and metrics · 100–120 review |
| OH · Wed · 60 min | Capstone midpoint preparation |
| C2 · Thu · 120 min | 0–60 add a prompt-injection test document and check the guard · 60–100 peer review · 100–120 quiz review |
| QP · Fri · 60 min | 0–20 quiz 22b · 20–50 capstone midpoint reviews · 50–60 preview of M23 |
| Self-study · ~6 h | Lewis et al. (2020) RAG paper; Anthropic docs on prompt engineering and citations |

## Labs

**Lab 22a — sentiment and RAG** (`lab_22a_sentiment_rag.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Lexicon sentiment | Score headlines with negation handling | "Not profitable" scored negative |
| 2. Classifier | TF-IDF + logistic regression vs lexicon | Accuracy compared on held-out headlines |
| 3. RAG | Chunk filings, retrieve, build a grounded prompt, extractive answer | The right filing is retrieved; off-topic questions are refused |
| 4. Claude (optional) | Send the grounded prompt to `claude-opus-5` | Answer cites sources; refusals handled |

**Lab 22b — news to signals** (`lab_22b_news_signal_event_study.py`)

| Section | You do | What good looks like |
|---|---|---|
| 1. Timestamped news | Read two years of headlines at all hours, with re-publications | You say what share arrives outside market hours and why that matters |
| 2. Signal | De-duplicate, score, assign each story to the first session that can act; fix the lexicon's misreadings ("downgrades", "record date") | Every story on the right session; the fixed scorer reads every direction correctly |
| 3. Event study | Pooled, market-adjusted forward returns after good and bad news; HAC t and a permutation test that shifts all stocks together | The planted drift recovered within noise; significant at 1–5 days |
| 4. Trading and delay | Long/short on the signal after costs; delay 0–8 sessions; the same-close look-ahead mistake | The edge is gone once the delay passes the half-life; the look-ahead Sharpe explained |

## Assessment

| Item | Weight in course component | Due | Criteria |
|---|---|---|---|
| Quizzes 22a, 22b | quizzes (10%) | Fri W43, W44 | NLP and RAG concepts |
| Labs 22a, 22b | labs (20%) | Sun W44 | Runs; evaluation, event study and delay sweep reported |
| Assignment: a RAG assistant with an evaluation set | assignments (15%) | Sun W46 | RAG over ≥ 5 filings with ≥ 20 evaluation questions (≥ 5 unanswerable), recall@k, faithfulness and citation accuracy, and a prompt-injection test. Rubric: retrieval 25, evaluation 35, safety 25, clarity 15 |

## Common mistakes

- Using headline timestamps in the wrong time zone, or trading on news published after the close as if at the close → market-hours alignment.
- Evaluating a classifier on randomly split headlines from the same stories → time-ordered split and deduplication.
- RAG that always answers → the relevance guard and unanswerable questions in the evaluation set.
- Pasting API keys into notebooks → environment variables only; `.env` is git-ignored.

## Readings

- Loughran and McDonald (2011), "When Is a Liability Not a Liability?".
- Tetlock (2007), "Giving Content to Investor Sentiment".
- Araci (2019), "FinBERT".
- Lewis et al. (2020), "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks".
- Tunstall, von Werra and Wolf, *Natural Language Processing with Transformers*, ch. 1–4.

## Instructor notes

- Owner: NLP/LLM and automation lead.
- The sample headlines and filings are fictional (`cfmat/data/samples`); real filings used in class must be public and at least three months old.
- The LLM step uses `claude-opus-5` by default (override with `CFMAT_CLAUDE_MODEL`); keep a budget per learner and log usage.
- Lab 22b's look-ahead result (trading the close of the session a story belongs to) is worth a live demonstration: it is the most common error in news-signal capstones.
