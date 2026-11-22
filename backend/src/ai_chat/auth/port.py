from typing import Protocol, runtime_checkable


@runtime_checkable
class UserDirectory(Protocol):
    """Minimal surface the app needs from the auth provider.

    Keeps the auth vendor behind a thin boundary so it can be swapped later.
    """

    async def get_email(self, user_id: str) -> str: ...

    async def is_email_verified(self, user_id: str) -> bool:
        """Whether the account's email address has been verified (FR-4).

        The app reads this rather than storing it, because the provider owns the
        state: an address can be verified by a flow the app never sees (the
        reset flow marks it verified, for one).
        """
        ...

    async def revoke_all_sessions(self, user_id: str) -> None:
        """End every session for a user, across devices (ADR-0031).

        Used when a password is set: a reset is the remedy for a suspected
        compromise, and old sessions would otherwise keep working.
        """
        ...
