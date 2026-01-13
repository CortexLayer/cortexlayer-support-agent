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
from backend.app.models.documents import Document
from backend.app.schemas.document import DocumentResponse
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

    plan_limits = {"starter": 10, "growth": 50, "scale": 1000}
    existing_docs = db.query(Document).filter(Document.client_id == client.id).count()

    if existing_docs >= plan_limits.get(client.plan_type.value, 10):
        raise HTTPException(
            status_code=403,
            detail="Document limit reached for your plan",
        )

    content = await file.read()
    file_size = len(content)

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

    document_id = str(uuid.uuid4())

    try:
        await embed_and_index(
            client_id=str(client.id),
            chunks=chunks,
            document_id=document_id,
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Embedding failed",
        ) from e

    document = Document(
        client_id=client.id,
        filename=file.filename,
        source_type=source_type,
        file_size_bytes=file_size,
        chunk_count=len(chunks),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

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

    plan_limits = {"starter": 10, "growth": 50, "scale": 1000}
    existing_docs = db.query(Document).filter(Document.client_id == client.id).count()

    if existing_docs >= plan_limits.get(client.plan_type.value, 10):
        raise HTTPException(
            status_code=403,
            detail="Document limit reached for your plan",
        )

    try:
        text, metadata = scrape_url(url)
    except Exception as e:
        logger.error(f"URL scraping failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="URL scraping failed",
        ) from e

    chunks = chunk_text(text, filename=url)
    document_id = str(uuid.uuid4())

    try:
        await embed_and_index(
            client_id=str(client.id),
            chunks=chunks,
            document_id=document_id,
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Embedding failed",
        ) from e

    document = Document(
        client_id=client.id,
        filename=metadata.get("title", url[:50]),
        source_type="url",
        source_url=url,
        file_size_bytes=len(text),
        chunk_count=len(chunks),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentResponse.from_orm(document)
