"""Query endpoint for the support bot."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_client
from backend.app.core.database import get_db
from backend.app.models.chat_logs import ChatLog
from backend.app.models.client import Client
from backend.app.rag.pipeline import run_rag_pipeline
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.services.billing import (
    check_query_limit,
    log_usage,
)
from backend.app.services.email_service import send_email_fallback
from backend.app.services.handoff_service import create_handoff_ticket
from backend.app.utils.logger import logger
from backend.app.utils.rate_limit import (
    check_global_rate_limit,
    check_rate_limit,
    get_rate_limit_for_plan,
)

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query_support_bot(
    request: QueryRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> QueryResponse:
    """Main query endpoint – runs full RAG pipeline with enforcement."""
    # 1. Hard stop if account disabled
    if client.is_disabled:
        raise HTTPException(
            status_code=403,
            detail="Account disabled due to billing or policy issues.",
        )

    # 2. Global rate limit (protect infra + OpenAI quota)
    await check_global_rate_limit()

    # 3. Per-client rate limit (per plan)
    rate_limit = get_rate_limit_for_plan(client.plan_type.value)
    await check_rate_limit(str(client.id), rate_limit)

    # 4. Monthly query quota enforcement (HARD stop)
    check_query_limit(client, db)

    # 5. Run RAG pipeline (pure inference)
    try:
        result = await run_rag_pipeline(
            client_id=str(client.id),
            query=request.query,
            plan_type=client.plan_type.value,
        )
    except Exception as exc:
        logger.error(
            "RAG pipeline failed for client %s: %s",
            client.id,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Query processing failed.",
        ) from None

    # 6. Escalation handling (handoff + email)
    if result["should_escalate"]:
        logger.info(
            "Escalation triggered for client %s: %s",
            client.id,
            result["escalation_reason"],
        )

        create_handoff_ticket(
            client_id=client.id,
            query=request.query,
            context=result["answer"],
            db=db,
        )

        await send_email_fallback(
            to_email=client.email,
            query=request.query,
            ai_response=result["answer"],
            confidence=result["confidence"],
        )

    # 7. Persist chat log
    db.add(
        ChatLog(
            client_id=client.id,
            query_text=request.query,
            response_text=result["answer"],
            confidence_score=result["confidence"],
            latency_ms=result["latency_ms"],
            channel="api",
        )
    )

    # 8. Centralized billing + usage logging
    log_usage(
        db=db,
        client_id=client.id,
        operation_type="query",
        input_tokens=result["usage_stats"]["input_tokens"],
        output_tokens=result["usage_stats"]["output_tokens"],
        model_used=result["usage_stats"]["model_used"],
        latency_ms=result["latency_ms"],
        cost_usd=result["usage_stats"]["cost_usd"],
    )

    db.commit()

    # 9. Clean API response
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        confidence=result["confidence"],
        latency_ms=result["latency_ms"],
    )
