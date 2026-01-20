"""FAISS vector store: create, add, save, load, search."""

import os
import pickle
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np

from backend.app.utils.logger import logger
from backend.app.utils.s3 import download_file, upload_file

_index_cache: Dict[str, Tuple[faiss.Index, List[Dict]]] = {}


def _get_base_tmp_dir() -> Path:
    """Return an OS-safe temporary directory and ensure it exists.

    Works on Windows, Linux, Docker, CI.
    """
    base = Path(tempfile.gettempdir()) / "faiss_indexes"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _get_index_path(client_id: str) -> str:
    """Local file path for FAISS index."""
    return str(_get_base_tmp_dir() / f"faiss_{client_id}.index")


def _get_metadata_path(client_id: str) -> str:
    """Local file path for FAISS metadata."""
    return str(_get_base_tmp_dir() / f"faiss_{client_id}_meta.pkl")


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
        index = create_index(len(embeddings[0]))
        existing_meta = []

    vectors = np.array(embeddings, dtype="float32")

    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a 2D array")

    if index.d != vectors.shape[1]:
        shape = vectors.shape[1]
        raise ValueError(f"Index dim mismatch: index={index.d}, vector_dim={shape}")

    index.add(vectors)
    all_metadata = existing_meta + metadata_list

    save_index(client_id, index, all_metadata)

    logger.info(
        "Added %d vectors to FAISS index for client %s",
        len(embeddings),
        client_id,
    )


def save_index(
    client_id: str,
    index: faiss.Index,
    metadata: List[Dict],
) -> None:
    """Save index locally and upload to S3."""
    index_path = _get_index_path(client_id)
    meta_path = _get_metadata_path(client_id)

    faiss.write_index(index, index_path)

    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    try:
        with open(index_path, "rb") as f:
            upload_file(f.read(), f"indexes/{client_id}.index")

        with open(meta_path, "rb") as f:
            upload_file(f.read(), f"indexes/{client_id}_meta.pkl")
    except Exception as exc:
        logger.warning(
            "S3 upload failed, continuing with local cache: %s",
            exc,
        )

    _index_cache[client_id] = (index, metadata)


def load_index(client_id: str) -> Tuple[faiss.Index, List[Dict]]:
    """Load index from cache, local disk, or S3."""
    if client_id in _index_cache:
        return _index_cache[client_id]

    index_path = _get_index_path(client_id)
    meta_path = _get_metadata_path(client_id)

    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        try:
            index_bytes = download_file(f"indexes/{client_id}.index")
            meta_bytes = download_file(f"indexes/{client_id}_meta.pkl")

            with open(index_path, "wb") as f:
                f.write(index_bytes)

            with open(meta_path, "wb") as f:
                f.write(meta_bytes)
        except Exception as exc:
            logger.error("Failed to load index from S3: %s", exc)
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
        raise ValueError(f"Query dim mismatch: query={q.shape[1]}, index={index.d}")

    distances, indices = index.search(q, top_k)

    results: List[Dict] = []
    for i, idx in enumerate(indices[0]):
        if 0 <= idx < len(metadata):
            m = metadata[idx].copy()
            m["score"] = float(1 / (1 + distances[0][i]))
            results.append(m)

    return results
