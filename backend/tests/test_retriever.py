import pytest
from unittest.mock import patch
pytestmark = pytest.mark.integration

from backend.app.rag.retriever import retrieve_relevant_chunks


@pytest.mark.asyncio
async def test_retriever_empty_query():
    results = await retrieve_relevant_chunks(
        client_id="test-client",
        query="",
        top_k=3
    )
    assert results == []


@pytest.mark.asyncio
@patch("backend.app.rag.retriever.get_embeddings")
async def test_retriever_embedding_failure(mock_get_embeddings):
    mock_get_embeddings.side_effect = Exception("Embedding failed")

    results = await retrieve_relevant_chunks(
        client_id="test-client",
        query="test question",
        top_k=3
    )

    assert results == []


@pytest.mark.asyncio
@patch("backend.app.rag.retriever.get_embeddings")
@patch("backend.app.rag.retriever.search_index")
async def test_retriever_success(mock_search_index, mock_get_embeddings):
    mock_get_embeddings.return_value = ([[0.1] * 1536], {})
    mock_search_index.return_value = [
        {
            "text": "Test chunk",
            "metadata": {"filename": "test.txt"},
            "score": 0.9
        }
    ]

    results = await retrieve_relevant_chunks(
        client_id="test-client",
        query="reset password",
        top_k=1
    )

    assert len(results) == 1
    assert results[0]["text"] == "Test chunk"
    assert "score" in results[0]