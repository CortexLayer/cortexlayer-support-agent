"""Document ingestion API endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_client
from backend.app.core.database import get_db
from backend.app.ingestion.chunker import chunk_text
from backend.app.ingestion.embedder import embed_and_index
from backend.app.ingestion.pdf_reader import extract_pdf_text
from backend.app.ingestion.text_reader import extract_text
from backend.app.ingestion.url_scraper import scrape_url
from backend.app.models.client import Client
from backend.app.models.documents import Document, DocumentStatus
from backend.app.schemas.document import DocumentResponse
from backend.app.services.billing import log_usage
from backend.app.services.usage_limits import (
    check_chunk_limit,
    check_document_limit,
    check_file_size,
)
from backend.app.utils.logger import logger

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/file", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    """Upload and ingest a document file into the knowledge base."""
    if client.is_disabled:
        raise HTTPException(status_code=403, detail="Account disabled")

    if not file.filename.endswith((".pdf", ".txt", ".md")):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, TXT, and MD files are allowed",
        )

    check_document_limit(client, db)

    content = await file.read()
    file_size = len(content)

    check_file_size(file_size, client.plan_type)

    try:
        if file.filename.endswith(".pdf"):
            text = extract_pdf_text(content)
            source_type = "pdf"
        else:
            text = extract_text(content)
            source_type = "text"
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Text extraction failed",
        ) from e

    chunks = chunk_text(text, filename=file.filename)

    check_chunk_limit(len(chunks), client.plan_type)

    document_id = str(uuid.uuid4())

    document = Document(
        id=document_id,
        client_id=client.id,
        filename=file.filename,
        source_type=source_type,
        file_size_bytes=file_size,
        chunk_count=len(chunks),
        status=DocumentStatus.PROCESSING.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        usage_stats = await embed_and_index(
            client_id=str(client.id),
            chunks=chunks,
            document_id=document_id,
        )

        log_usage(
            db=db,
            client_id=str(client.id),
            operation_type="embedding",
            embedding_tokens=usage_stats.get("tokens", 0),
            model_used=usage_stats.get("model"),
        )

        document.status = DocumentStatus.READY.value
        db.commit()

        logger.info(
            f"Document {document_id} uploaded successfully: "
            f"chunks={len(chunks)}, tokens={usage_stats.get('tokens', 0)}, "
            f"cost=${usage_stats.get('cost_usd', 0):.6f}, status=ready"
        )

    except Exception as e:
        document.status = DocumentStatus.FAILED.value
        db.commit()

        logger.error(
            "Upload failed for document %s. Document marked as failed.",
            document_id,
            exc_info=e,
        )
        raise HTTPException(
            status_code=500,
            detail="Document upload failed",
        ) from e

    return DocumentResponse.from_orm(document)


@router.post("/url", response_model=DocumentResponse)
async def upload_url(
    url: str = Form(...),
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    """Ingest and index content from a URL."""
    if client.is_disabled:
        raise HTTPException(status_code=403, detail="Account disabled")

    check_document_limit(client, db)

    try:
        text, metadata = scrape_url(url)
    except Exception as e:
        logger.error(f"URL scraping failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="URL scraping failed",
        ) from e

    chunks = chunk_text(text, filename=url)

    check_chunk_limit(len(chunks), client.plan_type)

    document_id = str(uuid.uuid4())

    document = Document(
        id=document_id,
        client_id=client.id,
        filename=metadata.get("title", url[:50]),
        source_type="url",
        source_url=url,
        file_size_bytes=len(text),
        chunk_count=len(chunks),
        status=DocumentStatus.PROCESSING.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        usage_stats = await embed_and_index(
            client_id=str(client.id),
            chunks=chunks,
            document_id=document_id,
        )

        log_usage(
            db=db,
            client_id=str(client.id),
            operation_type="embedding",
            embedding_tokens=usage_stats.get("tokens", 0),
            model_used=usage_stats.get("model"),
        )

        document.status = DocumentStatus.READY.value
        db.commit()

        logger.info(
            f"URL document {document_id} uploaded successfully: "
            f"chunks={len(chunks)}, tokens={usage_stats.get('tokens', 0)}, "
            f"cost=${usage_stats.get('cost_usd', 0):.6f}, status=ready"
        )

    except Exception as e:
        document.status = DocumentStatus.FAILED.value
        db.commit()

        logger.error(
            "URL upload failed for document %s. Document marked as failed.",
            document_id,
            exc_info=e,
        )
        raise HTTPException(
            status_code=500,
            detail="URL upload failed",
        ) from e

    return DocumentResponse.from_orm(document)
