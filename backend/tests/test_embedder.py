"""Tests for embedder (mocking OpenAI API)."""

from unittest.mock import patch

import pytest

from backend.app.ingestion.embedder import embed_chunks


@pytest.mark.asyncio
@patch("backend.app.ingestion.embedder.get_embeddings")
async def test_embed_chunks(mock_get_embeddings):
    """Test that embeddings are attached correctly to chunks."""
    # Fake embedding output
    fake_emb = [[0.1, 0.2, 0.3]]

    mock_get_embeddings.return_value = (fake_emb, {"tokens": 10, "cost_usd": 0.0002})

    chunks = [{"text": "hello world", "metadata": {}}]

    embedded_chunks, stats = await embed_chunks(chunks)

    assert "embedding" in embedded_chunks[0]
    assert embedded_chunks[0]["embedding"] == fake_emb[0]
    assert stats["tokens"] == 10
