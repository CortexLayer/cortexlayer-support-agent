"""Text chunking utilities for token-based and sentence-based chunking."""

import re
from typing import Dict, List

import tiktoken


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def chunk_text(
    text: str,
    filename: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    encoding_name: str = "cl100k_base",
) -> List[Dict]:
    """Chunk text using token boundaries with overlap.

    Returns a list of dictionaries, each containing:
        {
            "text": "...",
            "metadata": {
                "filename": ...,
                "chunk_index": ...,
                "token_count": ...,
                "start_char": ...,
                "end_char": ...
            }
        }
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]

        chunk_text_value = encoding.decode(chunk_tokens)

        chunks.append(
            {
                "text": chunk_text_value,
                "metadata": {
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "token_count": len(chunk_tokens),
                    "start_char": start,
                    "end_char": end,
                },
            }
        )

        chunk_index += 1
        start = end - chunk_overlap  # overlapping window

    return chunks


def chunk_by_sentences(text: str, filename: str, max_tokens: int = 512) -> List[Dict]:
    """Chunk text by sentence boundaries for semantic coherence."""
    # Split text into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current_chunk = ""
    chunk_index = 0

    for sentence in sentences:
        test_chunk = (current_chunk + " " + sentence).strip()

        # Check if adding this sentence exceeds max token limit
        if current_chunk and count_tokens(test_chunk) > max_tokens:
            chunks.append(
                {
                    "text": current_chunk,
                    "metadata": {
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "token_count": count_tokens(current_chunk),
                    },
                }
            )
            chunk_index += 1
            current_chunk = sentence  # start new chunk
        else:
            current_chunk = test_chunk

    # Add last chunk
    if current_chunk:
        chunks.append(
            {
                "text": current_chunk,
                "metadata": {
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "token_count": count_tokens(current_chunk),
                },
            }
        )

    return chunks
