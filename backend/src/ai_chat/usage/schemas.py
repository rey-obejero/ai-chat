from datetime import datetime

from pydantic import BaseModel


class UsageRead(BaseModel):
    """A user's token spend for the current period.

    ``limit`` and ``remaining`` are ``null`` when the quota is disabled.
    ``full_limit`` is the allowance a verified account gets: it is what makes a
    reduced ``limit`` explainable rather than merely lower (FR-4, ADR-0039).
    """

    used: int
    limit: int | None
    full_limit: int | None
    remaining: int | None
    period_start: datetime
    resets_at: datetime
