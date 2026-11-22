"""assistant personalisation

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The account's standing instructions (FR-24). Nullable, because having
    # none is a state, not an empty string; the cap is enforced at the
    # endpoint, not by the width.
    op.add_column("users", sa.Column("instructions", sa.Text(), nullable=True))
    # The response style (FR-25). A server default so existing rows are
    # backfilled by the `ALTER` itself and the column can be `NOT NULL`.
    op.add_column(
        "users",
        sa.Column("response_style", sa.String(16), server_default="default", nullable=False),
    )
    # The conversation's chosen model (FR-23). Nullable: without a choice the
    # request-time default applies, which is what the picker shows as "Auto".
    op.add_column("conversations", sa.Column("model", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("conversations", "model")
    op.drop_column("users", "response_style")
    op.drop_column("users", "instructions")
