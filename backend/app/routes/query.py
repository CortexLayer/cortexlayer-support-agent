"""Query endpoint for the support bot."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_client
from backend.app.core.database import get_db
from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client
from backend.app.models.usage import UsageLog
from backend.app.rag.pipeline import run_rag_pipeline
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.utils.logger import logger
from backend.app.utils.rate_limit import check_rate_limit, get_rate_limit_for_plan

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query_support_bot(
    request: QueryRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    """Main query endpoint – runs full RAG pipeline."""
    # 1. Hard stop if account disabled
    if client.is_disabled:
        raise HTTPException(
            status_code=403,
            detail="Account disabled due to billing or policy issues",
        )

    # 2. Rate limiting (per plan)
    rate_limit = get_rate_limit_for_plan(client.plan_type.value)
    await check_rate_limit(str(client.id), rate_limit)

    # 3. Run RAG pipeline
    try:
        result = await run_rag_pipeline(
            client_id=str(client.id),
            query=request.query,
            plan_type=client.plan_type.value,
        )
    except Exception as e:
        logger.error(f"RAG pipeline failed for client {client.id}: {e}")
        raise HTTPException(status_code=500, detail="Query processing failed") from None

    # 4. Persist chat log
    chat_log = ChatLog(
        client_id=client.id,
        query_text=request.query,
        response_text=result["answer"],
        retrieved_chunks=result.get("retrieved_chunks", []),
        confidence_score=result["confidence"],
        latency_ms=result["latency_ms"],
        channel="api",
    )
    db.add(chat_log)

    # 5. Persist usage log (for billing)
    usage_log = UsageLog(
        client_id=client.id,
        operation_type="query",
        input_tokens=result["usage_stats"]["input_tokens"],
        output_tokens=result["usage_stats"]["output_tokens"],
        cost_usd=result["usage_stats"]["cost_usd"],
        model_used=result["usage_stats"]["model_used"],
        latency_ms=result["latency_ms"],
    )
    db.add(usage_log)

    db.commit()

    # 6. Return clean response
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        confidence=result["confidence"],
        latency_ms=result["latency_ms"],
    )
