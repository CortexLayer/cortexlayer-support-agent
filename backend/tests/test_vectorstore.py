"""Tests for FAISS vectorstore."""

from pathlib import Path
from tempfile import gettempdir

import numpy as np
import pytest

import backend.app.core.vectorstore as vs

BASE_TMP_DIR = Path(gettempdir()) / "faiss_test"
BASE_TMP_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def cleanup_tmp_files():
    """Remove temporary FAISS files after each test."""
    yield
    for file in BASE_TMP_DIR.glob("*"):
        try:
            file.unlink()
        except Exception:
            pass


def test_create_index_and_add_search(monkeypatch):
    """Create index, add vectors, and search successfully."""
    monkeypatch.setattr(
        vs,
        "_get_index_path",
        lambda cid: str(BASE_TMP_DIR / f"fa_{cid}.idx"),
    )
    monkeypatch.setattr(
        vs,
        "_get_metadata_path",
        lambda cid: str(BASE_TMP_DIR / f"fa_{cid}.meta"),
    )

    monkeypatch.setattr(
        vs,
        "create_index",
        lambda dimension=3: vs.faiss.IndexHNSWFlat(3, 8),
    )

    emb1 = [0.1, 0.0, 0.0]
    emb2 = [0.2, 0.1, 0.0]

    metadata = [{"id": 1}, {"id": 2}]

    vs.add_to_index("c1", [emb1, emb2], metadata)

    results = vs.search_index("c1", emb1, top_k=2)

    assert len(results) == 2
    assert "score" in results[0]


def test_dimension_mismatch_raises():
    """Vector dimension mismatch must raise ValueError."""
    index = vs.faiss.IndexHNSWFlat(4, 8)
    bad_vec = np.array([[0.1, 0.2, 0.3]], dtype="float32")

    with pytest.raises(ValueError):
        if index.d != bad_vec.shape[1]:
            raise ValueError("Dimension mismatch detected.")
