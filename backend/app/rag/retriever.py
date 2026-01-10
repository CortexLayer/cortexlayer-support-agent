"""Core retirever module for RAG Pipeline."""

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
    1. Convert query → embedding
    2. Search FAISS index
    3. Return ranked chunks
    """

    if not query.strip():
        logger.warning("Empty query received for retrieval")
        return []

    # Step 1: Embed the query
    embeddings, _ = await get_embeddings(
        texts=[query]
    )
    query_embedding = embeddings[0]

    # Step 2: Search FAISS index
    try:
        results = search_index(
            client_id=client_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
    except Exception as e:
        logger.error(f"FAISS search failed: {e}")
        return []

    # Step 3: Post-process results
    cleaned_results = []
    for item in results:
        if "text" not in item or "metadata" not in item:
            continue

        cleaned_results.append({
            "text": item["text"],
            "metadata": item["metadata"],
            "score": float(item.get("score", 0.0))
        })

    logger.info(
        f"Retrieved {len(cleaned_results)} chunks for client={client_id}"
    )

    return cleaned_results
