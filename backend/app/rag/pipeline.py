"""RAG pipeline orchestrator: retrieval, prompt construction, generation."""

from __future__ import annotations

import time
from typing import Dict, List

from backend.app.rag.generator import generate_answer
from backend.app.rag.prompt import build_fallback_prompt, build_rag_prompt
from backend.app.rag.retriever import retrieve_relevant_chunks
from backend.app.utils.logger import logger

ESCALATION_CONFIDENCE_THRESHOLD = 0.3


def _select_model_preference(plan_type: str) -> str:
    """Select model strategy based on plan type."""
    if plan_type == "starter":
        return "groq"
    if plan_type == "growth":
        return "groq_with_fallback"
    if plan_type == "scale":
        return "openai_gpt4"
    return "groq"


async def run_rag_pipeline(
    client_id: str,
    query: str,
    plan_type: str = "starter",
    top_k: int = 5,
) -> Dict:
    """Run the complete RAG pipeline.

    This function is side-effect free. It does not write to DB,
    send emails, or create handoff tickets.
    """
    if not query or not query.strip():
        logger.warning("Empty query received for RAG pipeline")
        return {
            "answer": "Please provide a valid question.",
            "citations": [],
            "confidence": 0.0,
            "latency_ms": 0,
            "usage_stats": {
                "model_used": "none",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
            },
            "should_escalate": False,
            "escalation_reason": None,
        }

    start_time = time.time()

    try:
        retrieved_chunks: List[Dict] = await retrieve_relevant_chunks(
            client_id=client_id,
            query=query,
            top_k=top_k,
        )
    except Exception as exc:
        logger.error("Retrieval failed: %s", exc)
        retrieved_chunks = []

    if retrieved_chunks:
        prompt = build_rag_prompt(query, retrieved_chunks)
        confidence = min(
            float(retrieved_chunks[0].get("score", 0.0)),
            1.0,
        )
    else:
        prompt = build_fallback_prompt(query)
        confidence = 0.0

    model_preference = _select_model_preference(plan_type)

    try:
        answer, usage_stats = await generate_answer(
            prompt,
            model_preference=model_preference,
        )
    except Exception as exc:
        logger.error("Generation failed: %s", exc)
        answer = "I'm sorry, I'm experiencing technical issues."
        usage_stats = {
            "model_used": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
        }

    citations = [
        {
            "document": chunk.get("metadata", {}).get("filename", "unknown"),
            "chunk_index": chunk.get("metadata", {}).get("chunk_index", 0),
            "relevance_score": round(chunk.get("score", 0.0), 3),
        }
        for chunk in retrieved_chunks[:3]
    ]

    latency_ms = int((time.time() - start_time) * 1000)

    should_escalate = confidence < ESCALATION_CONFIDENCE_THRESHOLD
    escalation_reason = (
        f"Low confidence \
({confidence:.2f})"
        if should_escalate
        else None
    )

    return {
        "answer": answer,
        "citations": citations,
        "confidence": round(confidence, 3),
        "latency_ms": latency_ms,
        "usage_stats": usage_stats,
        "should_escalate": should_escalate,
        "escalation_reason": escalation_reason,
    }
