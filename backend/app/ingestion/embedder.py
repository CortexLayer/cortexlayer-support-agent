"""Embedding service for generating vector embeddings for text chunks."""

from typing import Dict, List, Tuple

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.utils.logger import logger

# Initialize OpenAI client once
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_embeddings(
    texts: List[str], model: str = "text-embedding-3-small"
) -> Tuple[List[List[float]], Dict]:
    """Generate embeddings for a list of texts.

    Returns:
        embeddings: List[List[float]]
        usage_stats: {"tokens": int, "cost_usd": float}
    """
    try:
        response = openai_client.embeddings.create(model=model, input=texts)

        embeddings = [item.embedding for item in response.data]

        total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens

        logger.info(
            f"Generated {len(embeddings)} embeddings | "
            f"Tokens: {total_tokens} | Cost: ${cost:.6f}"
        )

        return embeddings, {"tokens": total_tokens, "cost_usd": cost}

    except Exception as exc:
        logger.error(f"Embedding generation failed: {exc}")
        raise


async def embed_chunks(chunks: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Take a list of chunks and attach embeddings to each one.

    Returns:
        Updated chunks + usage statistics.
    """
    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings
    embeddings, usage_stats = await get_embeddings(texts)

    # Attach embedding to each chunk
    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[idx]
        chunk["embedding_model"] = "text-embedding-3-small"

    return chunks, usage_stats
