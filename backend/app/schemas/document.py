"""Pydantic response schemas for document ingestion APIs."""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Response model representing a successfully ingested document."""

    id: str
    filename: str
    source_type: str
    chunk_count: int
    created_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
