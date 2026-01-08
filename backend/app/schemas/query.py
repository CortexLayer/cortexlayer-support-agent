"""For Handling Reponse Validation."""

from typing import List, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """For Validating Query Request."""

    query: str
    conversation_id: Optional[str] = None


class Citation(BaseModel):
    """Citation Format Validation."""

    document: str
    chunk_index: int
    relevance_score: float


class QueryResponse(BaseModel):
    """Reponse Model validation."""

    answer: str
    citations: List[Citation]
    confidence: float
    latency_ms: int
