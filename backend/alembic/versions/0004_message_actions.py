"""message actions: generation gate and idempotency key

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # One in-flight stream per conversation (ADR-0050, H2). Nullable: only a
    # running stream sets it, and a stale value expires via `stream_grace_seconds`.
    op.add_column(
        "conversations",
        sa.Column("generating_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Client-generated write key (ADR-0050, H3), unique per conversation and
    # role so a retried write is a structural no-op. Nullable: rows without a
    # key are unaffected, and Postgres treats each null as distinct. The role is
    # part of the key because the key names one logical turn: an edit keys the
    # reply it produces with the key of the user turn it rewrites.
    op.add_column("messages", sa.Column("client_id", sa.Uuid(as_uuid=True), nullable=True))
    op.create_unique_constraint(
        "uq_messages_conversation_role_client_id",
        "messages",
        ["conversation_id", "role", "client_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_messages_conversation_role_client_id", "messages", type_="unique")
    op.drop_column("messages", "client_id")
    op.drop_column("conversations", "generating_at")
