"""Billing utilities: token cost calculation and centralized usage logging."""

from backend.app.core.config import settings
from backend.app.models.usage import UsageLog
from backend.app.utils.logger import logger

# Pricing per 1M tokens (USD)
PRICING = {
    settings.OPENAI_EBD_MODEL: {"input": 0.02},
    settings.GROQ_MODEL: {"input": 0.27, "output": 0.27},
    settings.OPENAI_MODEL: {"input": 0.15, "output": 0.60},
}
WHATSAPP_MESSAGE_COST_USD = 0.005


def calculate_embedding_cost(tokens: int, model: str) -> float:
    """Calculate internal embedding cost for a given token count."""
    pricing = PRICING.get(model)
    if not pricing:
        logger.warning("Unknown embedding model for billing: %s", model)
        return 0.0
    return (tokens / 1_000_000) * pricing["input"]


def calculate_generation_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    """Calculate internal LLM generation cost."""
    pricing = PRICING.get(model)
    if not pricing:
        logger.warning("Unknown generation model for billing: %s", model)
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


def log_usage(
    db,
    client_id: str,
    operation_type: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    embedding_tokens: int = 0,
    model_used: str | None = None,
    latency_ms: int | None = None,
) -> UsageLog:
    """Single source of truth for usage logging + billing."""
    if operation_type == "embedding":
        cost_usd = calculate_embedding_cost(
            embedding_tokens,
            model_used or "text-embedding-3-small",
        )

    elif operation_type == "query":
        cost_usd = (
            calculate_generation_cost(
                input_tokens,
                output_tokens,
                model_used,
            )
            if model_used
            else 0.0
        )

    elif operation_type == "whatsapp":
        cost_usd = WHATSAPP_MESSAGE_COST_USD

    else:
        logger.warning("Unknown operation type for billing: %s", operation_type)
        cost_usd = 0.0

    usage = UsageLog(
        client_id=client_id,
        operation_type=operation_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        embedding_tokens=embedding_tokens,
        cost_usd=cost_usd,
        model_used=model_used,
        latency_ms=latency_ms,
    )

    db.add(usage)

    logger.info(
        "Usage logged | client=%s | op=%s | cost=$%.4f",
        client_id,
        operation_type,
        cost_usd,
    )

    return usage
