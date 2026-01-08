"""
Embedding service for generating vector embeddings for text chunks.
Supports:
- OpenAI embeddings (prod)
- Mock embeddings (testing / Groq-only env)
"""

from typing import Dict, List, Tuple
import hashlib
import numpy as np
import os

from backend.app.core.config import settings
from backend.app.utils.logger import logger

EMBED_DIM = 1536  # MUST match FAISS index


def _mock_embedding(text: str) -> List[float]:
    """
    Deterministic mock embedding.
    Same text => same vector.
    """
    digest = hashlib.sha256(text.encode()).digest()
    seed = int.from_bytes(digest[:4], "little")
    rng = np.random.default_rng(seed)
    return rng.random(EMBED_DIM, dtype=np.float32).tolist()


async def get_embeddings(
    texts: List[str],
    model: str = "text-embedding-3-small",
) -> Tuple[List[List[float]], Dict]:
    """
    Generate embeddings.
    Uses MOCK embeddings when USE_MOCK_EMBEDDINGS=true
    """

    # 🚨 TEST MODE (DAY 8)
    if os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true":
        logger.warning("⚠️ Using MOCK embeddings (Groq test mode)")

        embeddings = [_mock_embedding(t) for t in texts]

        return embeddings, {
            "tokens": 0,
            "cost_usd": 0.0,
            "model": "mock",
        }

    # ✅ PROD MODE (OpenAI)
    try:
        from openai import OpenAI

        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        response = openai_client.embeddings.create(
            model=model,
            input=texts,
        )

        embeddings = [item.embedding for item in response.data]

        total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1_000_000) * 0.02

        logger.info(
            f"Generated {len(embeddings)} embeddings | "
            f"Tokens: {total_tokens} | Cost: ${cost:.6f}"
        )

        return embeddings, {"tokens": total_tokens, "cost_usd": cost}

    except Exception as exc:
        logger.error(f"Embedding generation failed: {exc}")
        raise


async def embed_chunks(
    chunks: List[Dict],
) -> Tuple[List[Dict], Dict]:
    """
    Attach embeddings to chunks.
    """
    texts = [chunk["text"] for chunk in chunks]

    embeddings, usage_stats = await get_embeddings(texts)

    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[idx]
        chunk["embedding_model"] = usage_stats.get("model", "unknown")

    return chunks, usage_stats
