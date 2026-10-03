from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: datetime


class SocialProvidersRead(BaseModel):
    """Which social buttons to render.

    Identifiers only — never credential state. The front end needs this before
    sign-in, so the endpoint is public, and it must not disclose more than which
    buttons appear.
    """

    providers: list[str]
