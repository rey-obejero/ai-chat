"""conversation states and search

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Substring search is `ILIKE '%term%'` over the title and the transcript, so
    # it works for scripts a word-based index does not tokenize; `pg_trgm`
    # supplies the index for it. In Compose the extension is created by the
    # entrypoint's init SQL as the superuser, because the application's own user
    # may not have the privilege; here it is `IF NOT EXISTS` so that is a no-op.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # The three presentation states (FR-17). Server defaults, so the rows that
    # already exist are backfilled by the `ALTER` itself.
    op.add_column(
        "conversations",
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "conversations",
        sa.Column("is_favourite", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "conversations",
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Backfill from the transcript: a conversation's activity is its last
    # message, or its creation when it has none. `now()` would order every
    # existing conversation by the migration's own run time instead.
    op.execute(
        """
        UPDATE conversations
        SET last_activity_at = COALESCE(
            (
                SELECT max(messages.created_at)
                FROM messages
                WHERE messages.conversation_id = conversations.id
            ),
            conversations.created_at
        )
        """
    )

    # The list's sort key: owner, then most recent activity.
    op.create_index(
        "ix_conversations_user_last_activity",
        "conversations",
        ["user_id", sa.text("last_activity_at DESC")],
    )
    # The search's access paths. `gin_trgm_ops` is what makes `ILIKE '%term%'`
    # answerable from the index rather than a sequential scan.
    op.create_index(
        "ix_conversations_title_trgm",
        "conversations",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_messages_content_trgm",
        "messages",
        ["content"],
        postgresql_using="gin",
        postgresql_ops={"content": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_messages_content_trgm", table_name="messages")
    op.drop_index("ix_conversations_title_trgm", table_name="conversations")
    op.drop_index("ix_conversations_user_last_activity", table_name="conversations")
    op.drop_column("conversations", "last_activity_at")
    op.drop_column("conversations", "is_archived")
    op.drop_column("conversations", "is_favourite")
    op.drop_column("conversations", "is_pinned")
    # The extension is left in place: dropping it would break any other object
    # that came to depend on it, and it costs nothing to keep.
