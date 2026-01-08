"""FAISS vector store: create, add, save, load, search."""

import os
import pickle
from typing import Dict, List, Tuple

import faiss
import numpy as np

from backend.app.utils.logger import logger
from backend.app.utils.s3 import download_file, upload_file

# in-memory cache
_index_cache: Dict[str, Tuple[faiss.Index, List[Dict]]] = {}

USE_MOCK = os.getenv("USE_MOCK_EMBEDDINGS", "").lower() == "true"

def _get_index_path(client_id: str) -> str:
    """Local file path for FAISS index."""
    return f"/tmp/faiss_{client_id}.index"


def _get_metadata_path(client_id: str) -> str:
    """Local file path for FAISS metadata."""
    return f"/tmp/faiss_{client_id}_meta.pkl"


def create_index(dimension: int = 1536) -> faiss.Index:
    """Create a new FAISS index."""
    return faiss.IndexHNSWFlat(dimension, 32)


def add_to_index(
    client_id: str,
    embeddings: List[List[float]],
    metadata_list: List[Dict],
) -> None:
    """Add vectors and metadata to index."""
    try:
        index, existing_meta = load_index(client_id)
    except Exception:
        index = create_index()
        existing_meta = []

    vectors = np.array(embeddings, dtype="float32")

    if index.d != vectors.shape[1]:
        msg = "Index dim mismatch: " f"index={index.d}, vector_dim={vectors.shape[1]}"
        raise ValueError(msg)

    index.add(vectors)
    all_metadata = existing_meta + metadata_list

    save_index(client_id, index, all_metadata)
    logger.info(
        "Added %d vectors to FAISS index for client %s.",
        len(embeddings),
        client_id,
    )


def save_index(client_id: str, index: faiss.Index, metadata: List[Dict]) -> None:
    """Save index locally and in S3."""
    index_path = _get_index_path(client_id)
    meta_path = _get_metadata_path(client_id)

    faiss.write_index(index, index_path)

    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    # Upload to S3
    with open(index_path, "rb") as f:
        upload_file(f.read(), f"indexes/{client_id}.index")

    with open(meta_path, "rb") as f:
        upload_file(f.read(), f"indexes/{client_id}_meta.pkl")

    _index_cache[client_id] = (index, metadata)


def load_index(client_id: str) -> Tuple[faiss.Index, List[Dict]]:
    """Load index from cache, local, or S3."""

    # 1️⃣ In-memory cache
    if client_id in _index_cache:
        return _index_cache[client_id]

    # 2️⃣ MOCK MODE → create empty local index
    if USE_MOCK:
        logger.warning("⚠️ MOCK MODE: creating empty FAISS index (no S3)")
        index = create_index()
        metadata: List[Dict] = []
        _index_cache[client_id] = (index, metadata)
        return index, metadata

    # 3️⃣ REAL MODE → existing behavior
    index_path = _get_index_path(client_id)
    meta_path = _get_metadata_path(client_id)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        try:
            data = download_file(f"indexes/{client_id}.index")
            with open(index_path, "wb") as f:
                f.write(data)

            meta = download_file(f"indexes/{client_id}_meta.pkl")
            with open(meta_path, "wb") as f:
                f.write(meta)
        except Exception as e:
            logger.error("Failed to load index: %s", e)
            raise

    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)

    _index_cache[client_id] = (index, metadata)
    return index, metadata



def search_index(
    client_id: str,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict]:
    """Search FAISS index for similar vectors."""
    index, metadata = load_index(client_id)

    q = np.array([query_embedding], dtype="float32")

    if q.shape[1] != index.d:
        msg = "Query vector dimension mismatch: " f"query={q.shape[1]}, index={index.d}"
        raise ValueError(msg)

    distances, indices = index.search(q, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        m = metadata[idx].copy()
        m["score"] = float(1 / (1 + distances[0][i]))
        results.append(m)


    return results
