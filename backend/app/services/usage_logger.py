from sqlalchemy.orm import Session
from backend.app.models.usage_log import UsageLog


def log_embedding_usage(
    db: Session,
    client_id: str,
    tokens: int,
    cost_usd: float,
):
    usage = UsageLog(
        client_id=client_id,
        operation_type="embedding",
        embedding_tokens=tokens,
        cost_usd=cost_usd,
    )

    db.add(usage)
    db.commit()
