from typing import Protocol, runtime_checkable


@runtime_checkable
class UserDirectory(Protocol):
    """Minimal surface the app needs from the auth provider.

    Keeps the auth vendor behind a thin boundary so it can be swapped later.
    """

    async def get_email(self, user_id: str) -> str: ...

    async def revoke_all_sessions(self, user_id: str) -> None:
        """End every session for a user, across devices (ADR-0031).

        Used when a password is set: a reset is the remedy for a suspected
        compromise, and old sessions would otherwise keep working.
        """
        ...
