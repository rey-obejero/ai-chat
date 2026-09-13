from typing import Protocol, runtime_checkable


@runtime_checkable
class UserDirectory(Protocol):
    """Minimal surface the app needs from the auth provider.

    Keeps the auth vendor behind a thin boundary so it can be swapped later.
    """

    async def get_email(self, user_id: str) -> str: ...
