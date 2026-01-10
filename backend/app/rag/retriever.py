"""Auto-generated placeholder module for CortexLayer        Backend."""
from typing import List, Dict
# from backend.app.ingestion.embedder import get_embeddings
from backend.app.core.vectorstore import search_index
from backend.app.utils.logger import logger

from backend.app.ingestion.embedder_hf import get_embeddings


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
    try:
        # embeddings, _ = await get_embeddings(
        #     texts=[query],
        #     model="text-embedding-3-small"
        # )
        # query_embedding = embeddings[0]
        
        embeddings, _ = await get_embeddings(texts=[query])
        query_embedding = embeddings[0]

    except Exception as e:
        error_msg = str(e).lower()

        if "insufficient_quota" in error_msg or "quota" in error_msg:
            logger.error(
                "❌ Embedding quota exhausted. "
                "Retriever returning empty context."
            )
        else:
            logger.error(f"❌ Query embedding failed: {e}")

        return []


    # Step 2: Search FAISS index
    try:
        results = search_index(
            client_id=client_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
    except Exception as e:
        logger.error(f"❌ FAISS search failed: {e}")
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
        f"🔍 Retrieved {len(cleaned_results)} chunks for client={client_id}"
    )

    return cleaned_results