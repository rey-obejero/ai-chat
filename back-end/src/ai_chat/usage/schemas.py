from datetime import datetime

from pydantic import BaseModel


class UsageRead(BaseModel):
    """A user's token spend for the current period.

    ``limit`` and ``remaining`` are ``null`` when the quota is disabled.
    """

    used: int
    limit: int | None
    remaining: int | None
    period_start: datetime
    resets_at: datetime
