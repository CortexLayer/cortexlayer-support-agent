"""FAISS vector store utilities.

Provides creation, persistence, caching, and querying of FAISS indexes
with local disk storage, S3 backup, and an in-memory LRU cache.

Design goals:
- Thread-safe
- Disk-safe (no temp file leaks)
- Durable (S3-backed)
- Observable (no silent failures)
"""

from __future__ import annotations

import os
import pickle
import tempfile
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Dict, List, Tuple

import faiss
import numpy as np

from backend.app.utils.logger import logger
from backend.app.utils.s3 import download_file, upload_file

# Path helpers


def _get_base_tmp_dir() -> Path:
    """Return an OS-safe temporary directory for FAISS indexes."""
    base = Path(tempfile.gettempdir()) / "faiss_indexes"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _get_index_path(client_id: str) -> str:
    """Return the local file path for a FAISS index."""
    return str(_get_base_tmp_dir() / f"faiss_{client_id}.index")


def _get_metadata_path(client_id: str) -> str:
    """Return the local file path for FAISS metadata."""
    return str(_get_base_tmp_dir() / f"faiss_{client_id}_meta.pkl")


def _delete_local_files(client_id: str) -> None:
    """Delete local FAISS index and metadata files for a client.

    Used during cache eviction to prevent disk leaks.
    """
    for path in (_get_index_path(client_id), _get_metadata_path(client_id)):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.warning("Failed to delete %s: %s", path, exc)


# S3 helpers


def _upload_with_retry(data: bytes, key: str, retries: int = 3) -> None:
    """Upload data to S3 with retries and exponential backoff.

    Raises:
        Exception: If all retry attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            upload_file(data, key)
            return
        except Exception as exc:
            if attempt == retries:
                raise
            logger.warning(
                "S3 upload retry %d/%d failed for %s: %s",
                attempt,
                retries,
                key,
                exc,
            )
            time.sleep(2**attempt)


# LRU cache


class LRUIndexCache:
    """Thread-safe LRU cache for FAISS indexes.

    Evicts least-recently-used entries and cleans up disk files.
    """

    def __init__(self, capacity: int = 50) -> None:
        """Initialize the FAISS LRU cache.

        Args:
            capacity: Maximum number of indexes to keep in memory.
        """
        self.capacity = capacity
        self.cache: OrderedDict[str, Tuple[faiss.Index, List[Dict]]] = OrderedDict()
        self.lock = Lock()

    def get(self, client_id: str) -> Tuple[faiss.Index, List[Dict]] | None:
        """Retrieve a cached index and mark it as recently used."""
        with self.lock:
            if client_id not in self.cache:
                return None
            self.cache.move_to_end(client_id)
            return self.cache[client_id]

    def put(
        self,
        client_id: str,
        value: Tuple[faiss.Index, List[Dict]],
    ) -> None:
        """Insert or update a cached index and evict if over capacity."""
        with self.lock:
            if client_id in self.cache:
                self.cache.move_to_end(client_id)

            self.cache[client_id] = value

            if len(self.cache) > self.capacity:
                evicted_client, evicted_value = self.cache.popitem(last=False)
                self._cleanup(evicted_client, evicted_value)
                logger.info(
                    "Evicted FAISS index for client %s from cache",
                    evicted_client,
                )

    def _cleanup(
        self,
        client_id: str,
        value: Tuple[faiss.Index, List[Dict]],
    ) -> None:
        """Cleanup resources for an evicted cache entry."""
        index, _ = value
        try:
            del index
        except Exception:
            pass

        _delete_local_files(client_id)


_index_cache = LRUIndexCache(capacity=50)


# FAISS operations


def create_index(dimension: int = 1536) -> faiss.Index:
    """Create a new FAISS HNSW index."""
    return faiss.IndexHNSWFlat(dimension, 32)


def add_to_index(
    client_id: str,
    embeddings: List[List[float]],
    metadata_list: List[Dict],
) -> None:
    """Add embeddings and metadata to a client's FAISS index."""
    if not embeddings:
        logger.warning("No embeddings provided for client %s", client_id)
        return

    try:
        index, existing_meta = load_index(client_id)
    except Exception:
        index = create_index(len(embeddings[0]))
        existing_meta = []

    vectors = np.asarray(embeddings, dtype="float32")

    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a 2D array")

    if index.d != vectors.shape[1]:
        raise ValueError(
            f"Index dim mismatch: index={index.d}, \
vector_dim={vectors.shape[1]}"
        )

    index.add(vectors)
    save_index(client_id, index, existing_meta + metadata_list)

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
    """Persist a FAISS index locally and attempt S3 upload."""
    index_path = _get_index_path(client_id)
    meta_path = _get_metadata_path(client_id)

    Path(index_path).parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, index_path)

    with open(meta_path, "wb") as f:
        pickle.dump(metadata, f)

    try:
        with open(index_path, "rb") as f:
            _upload_with_retry(f.read(), f"indexes/{client_id}.index")

        with open(meta_path, "rb") as f:
            _upload_with_retry(f.read(), f"indexes/{client_id}_meta.pkl")

    except Exception as exc:
        logger.error(
            "S3 upload FAILED for client %s. Index remains local only. Error: %s",
            client_id,
            exc,
        )

    _index_cache.put(client_id, (index, metadata))


def load_index(client_id: str) -> Tuple[faiss.Index, List[Dict]]:
    """Load a FAISS index from cache, disk, or S3."""
    cached = _index_cache.get(client_id)
    if cached:
        return cached

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

    _index_cache.put(client_id, (index, metadata))
    return index, metadata


def search_index(
    client_id: str,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict]:
    """Search a client's FAISS index for nearest neighbors."""
    index, metadata = load_index(client_id)

    query = np.asarray([query_embedding], dtype="float32")

    if query.shape[1] != index.d:
        raise ValueError(f"Query dim mismatch: query={query.shape[1]}, index={index.d}")

    distances, indices = index.search(query, top_k)

    results: List[Dict] = []
    for i, idx in enumerate(indices[0]):
        if 0 <= idx < len(metadata):
            item = metadata[idx].copy()
            item["score"] = float(1 / (1 + distances[0][i]))
            results.append(item)

    return results
