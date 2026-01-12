from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.app.core.database import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"
    __table_args__ = {"extend_existing": True}


    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)

    operation_type = Column(String, nullable=False)
    embedding_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
