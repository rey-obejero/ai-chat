"""display name

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The account's name (FR-7, ADR-0045). `NOT NULL` with an empty server
    # default, so the `ALTER` itself fills the rows that already exist and the
    # column can be added in one statement; the backfill below then replaces
    # the empty strings with each account's derivation.
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(50), server_default=sa.text("''"), nullable=False),
    )
    # The first-run prompt (FR-7). A flag of its own, because the derived name
    # already satisfies "never nameless" while the prompt is still unasked.
    op.add_column(
        "users",
        sa.Column("name_prompt_seen", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Backfill in SQL: existing accounts have names the moment the migration
    # lands, not on their next request. The derivation's first step, spelled in
    # the database's own words — the local part, truncated to the cap. The
    # filter runs in Python only, so a backfilled name the filter would refuse
    # is a name the account can change when the prompt asks.
    op.execute("UPDATE users SET display_name = left(split_part(email, '@', 1), 50)")


def downgrade() -> None:
    op.drop_column("users", "name_prompt_seen")
    op.drop_column("users", "display_name")
