"""Optional LLM answer step for RAG, using the Claude API (M22).

Needs ``pip install anthropic`` and an ``ANTHROPIC_API_KEY``. Everything else in
``cfmat.nlp`` runs offline.
"""

from __future__ import annotations

import os

from .rag import Chunk, build_rag_prompt


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
