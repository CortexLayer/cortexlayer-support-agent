"""Billing utilities: token cost calculation + usage logging."""

from backend.app.models.usage import UsageLog
from backend.app.utils.logger import logger

# Pricing per 1M tokens
PRICING = {
    "text-embedding-3-small": {"input": 0.02},
    "mixtral-8x7b": {"input": 0.27, "output": 0.27},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "whatsapp_message": 0.005,
}


def calculate_embedding_cost(
    tokens: int,
    model: str = "text-embedding-3-small",
) -> float:
    """Calculate cost for embeddings."""
    price_per_1m = PRICING.get(model, {}).get("input", 0.02)
    return (tokens / 1_000_000) * price_per_1m


def calculate_generation_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    """Calculate cost for LLM generation."""
    if model not in PRICING:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * PRICING[model].get("input", 0)
    output_cost = (output_tokens / 1_000_000) * PRICING[model].get("output", 0)

    return input_cost + output_cost


def log_usage(
    db,
    client_id: str,
    operation_type: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    embedding_tokens: int = 0,
    model_used: str | None = None,
    latency_ms: int | None = None,
) -> UsageLog:
    """Create a usage log entry with correct cost calculation."""
    if operation_type == "embedding":
        cost_usd = calculate_embedding_cost(
            embedding_tokens,
            model_used or "text-embedding-3-small",
        )
    elif operation_type == "query":
        cost_usd = calculate_generation_cost(
            input_tokens,
            output_tokens,
            model_used or "mixtral-8x7b",
        )
    elif operation_type == "whatsapp":
        cost_usd = PRICING["whatsapp_message"]
    else:
        cost_usd = 0.0

    usage_log = UsageLog(
        client_id=client_id,
        operation_type=operation_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        embedding_tokens=embedding_tokens,
        cost_usd=cost_usd,
        model_used=model_used,
        latency_ms=latency_ms,
        metadata_json=None,
    )

    db.add(usage_log)

    logger.info(
        "Logged usage: %s | cost=$%.4f | client=%s",
        operation_type,
        cost_usd,
        client_id,
    )

    return usage_log
