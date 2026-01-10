"""
Embedding service using local HuggingFace MiniLM.

NOTE:
- OpenAI embeddings temporarily disabled due to quota issues.
- Easy to revert by replacing implementation here only.
"""

from typing import List, Tuple

from sentence_transformers import SentenceTransformer

from backend.app.utils.logger import logger

# -----------------------------
# Model setup (loaded once)
# -----------------------------

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

try:
    _model = SentenceTransformer(_MODEL_NAME)
    logger.info(f"✅ Loaded local embedding model: {_MODEL_NAME}")
except Exception as e:
    logger.critical(f"❌ Failed to load embedding model: {e}")
    raise


# -----------------------------
# Public API (single contract)
# -----------------------------

async def get_embeddings(
    texts: List[str],
    model: str | None = None,  # kept for compatibility
) -> Tuple[List[List[float]], int]:
    """
    Generate embeddings locally.

    Returns:
        embeddings: List of vectors
        dim: Embedding dimension
    """

    if not texts:
        return [], 0

    try:
        embeddings = _model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception as e:
        logger.error(f"❌ Local embedding generation failed: {e}")
        return [], 0

    embeddings_list = embeddings.tolist()
    embedding_dim = len(embeddings_list[0])

    return embeddings_list, embedding_dim