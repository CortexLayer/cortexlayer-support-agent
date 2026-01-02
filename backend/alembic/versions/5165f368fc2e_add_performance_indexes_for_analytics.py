"""add performance indexes for analytics

Revision ID: 5165f368fc2e
Revises: 461c4ed19bc7
Create Date: 2026-01-02 13:43:15.051808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5165f368fc2e'
down_revision: Union[str, None] = '461c4ed19bc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_usage_client_op_time",
        "usage_logs",
        ["client_id", "operation_type", "timestamp"],
    )

    # Chat analytics hot path
    op.create_index(
        "ix_chat_client_time",
        "chat_logs",
        ["client_id", "timestamp"],
    )


def downgrade() -> None:
    op.drop_index("ix_usage_client_op_time", table_name="usage_logs")
    op.drop_index("ix_chat_client_time", table_name="chat_logs")
