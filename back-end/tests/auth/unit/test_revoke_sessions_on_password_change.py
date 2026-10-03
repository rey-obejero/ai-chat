"""Sessions must end when a password is set (ADR-0031).

The SDK updates the password but leaves existing sessions alive, so this
override is what makes a reset actually evict someone who is already signed in.
The failure it guards against is silent, so it is pinned here.
"""

from supertokens_python.recipe.emailpassword.interfaces import (
    UnknownUserIdError,
    UpdateEmailOrPasswordOkResult,
)

import ai_chat.auth.adapter_supertokens as adapter
from ai_chat.auth.adapter_supertokens import _revoke_sessions_on_password_change


class _UserId:
    def get_as_string(self) -> str:
        return "user-1"


class _FakeRecipeInterface:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[dict] = []

    async def update_email_or_password(
        self,
        *,
        recipe_user_id,
        email,
        password,
        apply_password_policy,
        tenant_id_for_password_policy,
        user_context,
    ):
        self.calls.append({"email": email, "password": password})
        return self._result


async def _run(result, password):
    original = _FakeRecipeInterface(result)
    wrapped = _revoke_sessions_on_password_change(original)  # type: ignore[arg-type]
    return await wrapped.update_email_or_password(
        recipe_user_id=_UserId(),
        email=None,
        password=password,
        apply_password_policy=None,
        tenant_id_for_password_policy="public",
        user_context={},
    )


def _record_revocations(monkeypatch) -> list[str]:
    revoked: list[str] = []

    async def fake_revoke(user_id: str) -> None:
        revoked.append(user_id)

    monkeypatch.setattr(adapter, "revoke_all_sessions", fake_revoke)
    return revoked


async def test_a_successful_password_change_revokes_every_session(monkeypatch) -> None:
    revoked = _record_revocations(monkeypatch)

    result = await _run(UpdateEmailOrPasswordOkResult(), password="new-password")

    assert revoked == ["user-1"]
    assert isinstance(result, UpdateEmailOrPasswordOkResult)


async def test_an_email_only_change_does_not_revoke(monkeypatch) -> None:
    # `update_email_or_password` is also the email-change path; only a password
    # change should end sessions.
    revoked = _record_revocations(monkeypatch)

    await _run(UpdateEmailOrPasswordOkResult(), password=None)

    assert revoked == []


async def test_a_failed_change_does_not_revoke(monkeypatch) -> None:
    revoked = _record_revocations(monkeypatch)

    await _run(UnknownUserIdError(), password="new-password")

    assert revoked == []
