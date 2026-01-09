"""RAG pipeline orchestrator: retrieval, prompt construction, generation."""

import time
from typing import Dict

from backend.app.rag.generator import generate_answer
from backend.app.rag.prompt import (
    build_fallback_prompt,
    build_rag_prompt,
)
from backend.app.rag.retriever import retrieve_relevant_chunks
from backend.app.utils.logger import logger


async def run_rag_pipeline(
    client_id: str,
    query: str,
    plan_type: str = "starter",
    top_k: int = 5,
) -> Dict:
    """Run the complete RAG pipeline."""
    start_time = time.time()

    try:
        retrieved_chunks = await retrieve_relevant_chunks(
            client_id=client_id,
            query=query,
            top_k=top_k,
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        retrieved_chunks = []

    if retrieved_chunks:
        prompt = build_rag_prompt(query, retrieved_chunks)
        confidence = min(retrieved_chunks[0].get("score", 0.0), 1.0)
    else:
        prompt = build_fallback_prompt(query)
        confidence = 0.0

    model_pref = "groq" if plan_type == "starter" else "openai"

    try:
        answer, usage_stats = await generate_answer(
            prompt,
            model_preference=model_pref,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        answer = "I'm sorry, I'm experiencing technical issues."
        usage_stats = {
            "model_used": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
        }

    citations = []
    for chunk in retrieved_chunks[:3]:
        citations.append(
            {
                "document": chunk.get("metadata", {}).get("filename", "unknown"),
                "chunk_index": chunk.get("metadata", {}).get("chunk_index", 0),
                "relevance_score": round(chunk.get("score", 0.0), 3),
            }
        )

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": round(confidence, 3),
        "latency_ms": latency_ms,
        "usage_stats": usage_stats,
    }
