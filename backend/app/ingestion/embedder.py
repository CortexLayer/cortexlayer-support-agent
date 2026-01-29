"""Embedding service for generating vector embeddings for text chunks."""

from typing import Dict, List, Tuple

from openai import OpenAI

from backend.app.core.config import settings
from backend.app.utils.logger import logger

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_embeddings(
    texts: List[str],
) -> Tuple[List[List[float]], Dict]:
    """Generate embeddings using OpenAI API.

    Args:
        texts: List of text strings to generate embeddings for.

    Returns:
        Tuple containing:
            - List of embedding vectors (each is a list of floats)
            - Dict with usage statistics (tokens, cost, model)

    Raises:
        RuntimeError: If OpenAI API is unavailable. No fallback is used to
            prevent embedding dimension mismatch that would corrupt the
            FAISS index.
    """
    try:
        model = settings.OPENAI_EBD_MODEL
        response = openai_client.embeddings.create(model=model, input=texts)

        embeddings = [item.embedding for item in response.data]

        total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1_000_000) * 0.02

        logger.info(
            f"OpenAI embeddings generated: {len(embeddings)} | "
            f"Tokens: {total_tokens} | Cost: ${cost:.6f}"
        )

        return embeddings, {
            "tokens": total_tokens,
            "cost_usd": cost,
            "model": settings.OPENAI_EBD_MODEL,
        }

    except Exception as e:
        logger.error(f"OpenAI Embedding API failed: {str(e)}")
        raise RuntimeError(
            "OpenAI embeddings unavailable. Cannot proceed with HuggingFace "
            "fallback due to embedding dimension mismatch "
            "(OpenAI: 1536-dim, HuggingFace: 384-dim). "
            "This would corrupt the FAISS index. Please ensure OpenAI API "
            "is accessible and the API key is valid."
        ) from e


async def embed_chunks(chunks: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Attach embeddings directly to chunks.

    Kept as a thin public helper for tests and legacy compatibility.

    Args:
        chunks: List of chunk dictionaries containing text.

    Returns:
        Tuple containing:
            - List of chunks with embeddings attached
            - Dict with usage statistics
    """
    if not chunks:
        return [], {"tokens": 0, "cost_usd": 0.0}

    texts = [chunk["text"] for chunk in chunks]

    embeddings, usage_stats = await get_embeddings(texts)

    for idx, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[idx]
        chunk["embedding_model"] = usage_stats.get("model", "unknown")

    return chunks, usage_stats


async def embed_and_index(client_id: str, chunks: List[Dict], document_id: str) -> Dict:
    """Full ingestion pipeline: chunks → embeddings → FAISS.

    Args:
        client_id: Unique identifier for the client.
        chunks: List of chunk dictionaries to embed and index.
        document_id: Unique identifier for the source document.

    Returns:
        Dict with usage statistics (tokens, cost, model).
    """
    from backend.app.core.vectorstore import add_to_index

    if not chunks:
        logger.warning("No chunks provided for embedding")
        return {"tokens": 0, "cost_usd": 0.0}

    texts = [chunk["text"] for chunk in chunks]

    embeddings, usage_stats = await get_embeddings(texts)

    metadata_list = []
    for idx, chunk in enumerate(chunks):
        metadata_list.append(
            {
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
                "document_id": document_id,
                "chunk_index": idx,
            }
        )

    add_to_index(
        client_id=client_id,
        embeddings=embeddings,
        metadata_list=metadata_list,
    )

    logger.info(
        "Indexed chunks",
        extra={
            "chunk_count": len(embeddings),
            "client_id": client_id,
            "document_id": document_id,
        },
    )

    return usage_stats
