"""
Embedding service for generating vector embeddings for text chunks.
"""

from typing import Dict, List, Tuple
from openai import OpenAI

from backend.app.core.config import settings
from backend.app.utils.logger import logger
from backend.app.services.usage_logger import log_embedding_usage
from backend.app.core.database import get_db
from backend.app.ingestion.embedder_hf import get_embeddings as hf_embed



openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_embeddings(
    texts: List[str],
) -> Tuple[List[List[float]], Dict]:
    """
    Generate embeddings using OpenAI.
    Falls back to HF embeddings if OpenAI fails.
    """

    try:
        response = openai_client.embeddings.create(
            model=settings.OPENAI_EBD_MODEL,
            input=texts,
        )

        embeddings = [item.embedding for item in response.data]

        total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1_000_000) * 0.02

        return embeddings, {
            "tokens": total_tokens,
            "cost_usd": cost,
            "model": settings.OPENAI_EBD_MODEL,
        }

    except Exception as e:
        logger.error("OpenAI embedding failed, falling back to HF")
        logger.error(str(e))


        embeddings, token_count = hf_embed(texts)

        return embeddings, {
            "tokens": token_count,
            "cost_usd": 0.0,
            "model": settings.HF_EBD_MODEL,
        }


async def embed_and_index(
    client_id: str,
    chunks: List[Dict],
    document_id: str,
) -> Dict:
    """
    Full ingestion pipeline:
    chunks → embeddings → FAISS → billing
    """

    from backend.app.core.vectorstore import add_to_index

    if not chunks:
        return {"tokens": 0, "cost_usd": 0.0}

    texts = [chunk["text"] for chunk in chunks]

    embeddings, usage_stats = await get_embeddings(texts)

    metadata_list = [
        {
            "text": chunk["text"],
            "metadata": chunk.get("metadata", {}),
            "document_id": document_id,
            "chunk_index": idx,
        }
        for idx, chunk in enumerate(chunks)
    ]

    add_to_index(
        client_id=client_id,
        embeddings=embeddings,
        metadata_list=metadata_list,
    )

    if usage_stats["cost_usd"] > 0:
        db = next(get_db())
        log_embedding_usage(
            db=db,
            client_id=client_id,
            tokens=usage_stats["tokens"],
            cost_usd=usage_stats["cost_usd"],
        )

    return usage_stats
