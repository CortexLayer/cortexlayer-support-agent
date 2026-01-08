# backend/app/rag/retriever.py

from typing import List, Dict
from backend.app.ingestion.embedder import get_embeddings
from backend.app.core.vectorstore import search_index
from backend.app.utils.logger import logger


async def retrieve_relevant_chunks(
    client_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """
    Retrieve most relevant chunks for a query.

    Steps:
    1. Embed query
    2. Search FAISS index
    3. Return ranked metadata
    """

    if not query.strip():
        logger.warning("Empty query received for retrieval")
        return []

    # Step 1: Embed query
    try:
        embeddings, usage = await get_embeddings([query])
        query_embedding = embeddings[0]
    except Exception as e:
        logger.error(f"❌ Failed to embed query: {e}")
        return []

    # Step 2: Search FAISS
    try:
        results = search_index(
            client_id=client_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
    except Exception as e:
        logger.error(f"❌ FAISS search failed: {e}")
        return []

    logger.info(
        f"🔍 Retrieved {len(results)} chunks for client={client_id}"
    )

    return results

