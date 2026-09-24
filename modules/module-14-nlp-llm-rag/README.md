# Module 14 — NLP, LLMs and RAG for Financial Research

| Term | Weeks | Hours | Lab |
|---|---|---|---|
| 4 · AI and Automation | 31–32 | 20 | [`lab14_nlp_llm_rag.py`](../../labs/lab14_nlp_llm_rag.py) |

## Learning outcomes

1. Turn financial text (news, announcements, annual reports, earnings calls) into features.
2. Use finance-specific lexicons, TF-IDF classifiers and transformer models such as FinBERT, and compare them fairly.
3. Test whether text-based signals predict returns, using event studies.
4. Build a Retrieval-Augmented Generation (RAG) system: chunking, embeddings, vector stores, retrieval, reranking and grounded prompts with citations.
5. Evaluate RAG systems (retrieval recall, answer faithfulness, citation accuracy) and defend against hallucination and prompt injection.
6. Control LLM cost, latency and data-privacy risk.

## Session plan

| # | Session | Content |
|---|---|---|
| L1 | Text as data (Sat, W31) | Tokenisation, bag of words, TF-IDF; Loughran–McDonald lexicons and why general sentiment lexicons fail on finance text; supervised classifiers |
| L2 | Transformers and signals (Sun, W31) | Embeddings, BERT and FinBERT, fine-tuning; news and earnings-call signals; aligning timestamps with market hours; event studies |
| L3 | LLMs and RAG (Sat, W32) | How LLMs work; prompting for extraction and summarisation; RAG architecture; chunking strategies and contextual headers; embeddings and vector databases (pgvector, Chroma, FAISS); hybrid search and reranking |
| L4 | Evaluating and securing RAG (Sun, W32) | Evaluation sets; recall@k; faithfulness and citation checks; relevance guards; hallucination; prompt injection from documents; cost and caching; privacy of non-public information |
| C1–C4 | Clinics | Sentiment pipeline; FinBERT fine-tuning (GPU lab); Lab 14; RAG evaluation set |

## RAG architecture used in the lab

```
annual reports / filings
        │  chunk_text: sentence-aware chunks + document-title header
        ▼
   TF-IDF index  ──(exercise: swap for embeddings + pgvector/Chroma)
        │  search(question, k)
        ▼
  entity / relevance guard  ──► "not found" if nothing relevant
        │
        ▼
 build_rag_prompt: numbered sources, cite-or-decline instruction
        │
        ▼
 answer_with_claude (optional)  or  extractive_answer (offline)
```

## Assignment

Build an evaluation set of 25 questions over at least five real annual reports (with the correct source passage for each). Measure recall@3 for two chunk sizes and two retrievers, and report answer faithfulness for your best configuration.

## Readings

- Loughran and McDonald (2011), "When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks".
- Araci (2019), "FinBERT: Financial Sentiment Analysis with Pre-trained Language Models".
- Lewis et al. (2020), "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks".
- Tunstall, von Werra and Wolf, *Natural Language Processing with Transformers*: chapters 1–4, 7.

## Assessment

Quiz 14; Lab 14; RAG evaluation assignment.
