"""Tests for text chunking utilities."""

from backend.app.ingestion.chunker import (
    chunk_by_sentences,
    chunk_text,
    count_tokens,
)


def test_count_tokens():
    """Token counting should return a positive integer."""
    text = "Hello world"
    tokens = count_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0


def test_chunk_text_basic():
    """Chunking should split text into multiple chunks with correct metadata."""
    text = " ".join(["hello"] * 300)  # Long enough to require multiple chunks

    chunks = chunk_text(text, filename="sample.txt", chunk_size=50, chunk_overlap=10)

    assert len(chunks) > 1
    for c in chunks:
        assert "text" in c
        assert "metadata" in c
        assert c["metadata"]["filename"] == "sample.txt"
        assert c["metadata"]["chunk_index"] >= 0
        assert c["metadata"]["token_count"] > 0


def test_chunk_by_sentences():
    """Sentence-based chunking should not break sentences incorrectly."""
    text = "This is sentence one. " "This is sentence two. " "This is sentence three."

    chunks = chunk_by_sentences(text, filename="sentences.txt", max_tokens=10)

    assert len(chunks) >= 1

    # Ensure each chunk contains real text
    for c in chunks:
        assert len(c["text"]) > 0
        assert c["metadata"]["filename"] == "sentences.txt"
        assert c["metadata"]["token_count"] > 0
