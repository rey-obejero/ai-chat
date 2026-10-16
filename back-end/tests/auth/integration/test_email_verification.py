"""Verification mail and the state the app reads back (FR-4, ADR-0039).

SuperTokens core runs in Compose for the end-to-end suite only, so the recipe
functions are exercised directly here: the mail a sign-up sends, the lookup the
allowance depends on, and the cache entry a completed verification clears.
"""

import logging
from types import SimpleNamespace

import pytest
from supertokens_python.recipe.emailverification.interfaces import (
    VerifyEmailUsingTokenInvalidTokenError,
    VerifyEmailUsingTokenOkResult,
)
from supertokens_python.recipe.emailverification.types import EmailVerificationUser
from supertokens_python.types import RecipeUserId

import ai_chat.auth.adapter_supertokens as adapter
from ai_chat.auth import EmailNotVerifiedError, require_verified_email
from ai_chat.auth.adapter_supertokens import MailNotConfiguredError
from ai_chat.auth.verification import VerificationStateCache


class _RecipeUserId:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_as_string(self) -> str:
        return self._value


class _SignedUpAccount:
    """Just the parts of the SDK's sign-up result the mail send reads."""

    def __init__(self, user_id: str) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.recipe_user_id = _RecipeUserId(user_id)


class _FakeVerificationRecipe:
    """The emailverification recipe implementation, returning what it is told to."""

    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[tuple] = []

    async def verify_email_using_token(
        self, token, tenant_id, attempt_account_linking, user_context
    ):
        self.calls.append((token, tenant_id, attempt_account_linking, user_context))
        return self._result


def _verified_user(user_id: str = "user-1") -> VerifyEmailUsingTokenOkResult:
    return VerifyEmailUsingTokenOkResult(
        EmailVerificationUser(RecipeUserId(user_id), "new@example.com")
    )


async def test_a_sign_up_mail_is_addressed_to_the_new_account(monkeypatch) -> None:
    sent: list[dict] = []

    async def fake_send(**kwargs) -> None:
        sent.append(kwargs)

    monkeypatch.setattr(adapter, "send_email_verification_email", fake_send)
    account = _SignedUpAccount("user-1")

    await adapter._send_verification_email(account, "new@example.com", "public", {})

    assert sent == [
        {
            "tenant_id": "public",
            "user_id": "user-1",
            "recipe_user_id": account.recipe_user_id,
            "email": "new@example.com",
            "user_context": {},
        }
    ]


async def test_an_unconfigured_mailer_does_not_fail_sign_up(monkeypatch, caplog) -> None:
    # The account exists by the time the mail is attempted, so the failure is a
    # log line here: the resend endpoint is where it becomes visible to a user.
    async def failing_send(**_kwargs) -> None:
        raise MailNotConfiguredError("SMTP is not configured")

    monkeypatch.setattr(adapter, "send_email_verification_email", failing_send)

    with caplog.at_level(logging.WARNING):
        await adapter._send_verification_email(
            _SignedUpAccount("user-1"), "new@example.com", "public", {}
        )

    assert "could not be sent" in caplog.records[0].getMessage()


async def test_a_completed_verification_forgets_the_cached_state(monkeypatch) -> None:
    forgotten: list[str] = []
    monkeypatch.setattr(adapter, "forget_email_verified", forgotten.append)
    original = _FakeVerificationRecipe(_verified_user())

    wrapped = adapter._forget_cached_verification_state(original)  # type: ignore[arg-type]
    await wrapped.verify_email_using_token("tok", "public", True, {})

    # The account that just verified does not wait out the TTL for its full
    # allowance, and the result is passed through untouched.
    assert forgotten == ["user-1"]
    assert original.calls == [("tok", "public", True, {})]


async def test_an_invalid_token_changes_nothing(monkeypatch) -> None:
    forgotten: list[str] = []
    monkeypatch.setattr(adapter, "forget_email_verified", forgotten.append)
    result = VerifyEmailUsingTokenInvalidTokenError()
    original = _FakeVerificationRecipe(result)

    wrapped = adapter._forget_cached_verification_state(original)  # type: ignore[arg-type]
    returned = await wrapped.verify_email_using_token("stale", "public", True, {})

    assert returned is result
    assert forgotten == []


async def test_a_verified_answer_survives_the_cache_but_not_a_forget(monkeypatch) -> None:
    lookups: list[str] = []

    async def fake_lookup(user_id: str) -> bool:
        lookups.append(user_id)
        return True

    # The adapter's own state, so this covers the wiring between the cache and
    # the two functions the rest of the app calls.
    monkeypatch.setattr(adapter, "_verification_state", VerificationStateCache(fake_lookup))

    assert await adapter.is_email_verified("user-1") is True
    assert await adapter.is_email_verified("user-1") is True
    assert lookups == ["user-1"]

    adapter.forget_email_verified("user-1")

    assert await adapter.is_email_verified("user-1") is True
    assert lookups == ["user-1", "user-1"]


async def test_a_failed_lookup_counts_as_unverified(monkeypatch) -> None:
    """A lookup that cannot answer must not read as "verified" (ADR-0039).

    The allowance split is where the wrong guess would be invisible: "verified"
    hands the full allowance to an account nobody has proved anything about.
    """

    async def unreachable(_user_id: str) -> bool:
        raise RuntimeError("auth service unreachable")

    monkeypatch.setattr(adapter, "_verification_state", VerificationStateCache(unreachable))

    assert await adapter.is_email_verified("account-with-no-verified-address") is False


async def test_the_upload_gate_refuses_an_unverified_account() -> None:
    # Nothing is wired to this yet — the routes that upload and retrieve are
    # WI-9's and WI-13's — so this pins the refusal they will pick up.
    await require_verified_email(email_verified=True)

    with pytest.raises(EmailNotVerifiedError) as refused:
        await require_verified_email(email_verified=False)

    assert refused.value.code == "EMAIL_NOT_VERIFIED"
    assert "Verify your email" in refused.value.detail
