"""Screening at the SDK boundary: a refusal is a password field error (FR-2).

SuperTokens core runs in Compose for the end-to-end suite only, so these tests
exercise the overrides directly — the same way the session-revocation override
is pinned. What matters is the order: the password is judged *before* the
original function runs, so a refused password creates no account, changes no
password, and ends no session.
"""

import pytest
from supertokens_python.recipe.emailpassword.exceptions import FieldError
from supertokens_python.recipe.emailpassword.interfaces import (
    SignUpOkResult,
    UpdateEmailOrPasswordOkResult,
)

import ai_chat.auth.adapter_supertokens as adapter
from ai_chat.auth import passwords as passwords_module
from ai_chat.auth.adapter_supertokens import (
    _revoke_sessions_on_password_change,
    _screen_passwords,
)
from ai_chat.auth.passwords import split_sha1
from ai_chat.shared.config import Settings

WEAK = "password123"
# Scores 4 with zxcvbn and is not in the breach data. (`correcthorsebatterystaple`
# would be a cute choice and a real one — it is in HIBP, which one test below
# pins by stubbing the lookup rather than asking the service.)
STRONG = "j7Kq2-mZx9#Lp4Vt"


def _settings(**overrides: object) -> Settings:
    """Settings for the boundary tests: the breach service is never called.

    These tests are about where the check sits, not what it decides; the breach
    path is driven by a stub in the one test that needs it, and by fakes in
    `tests/auth/unit/test_password_rules.py`.
    """
    settings: dict[str, object] = {"password_breach_check_enabled": False}
    settings.update(overrides)
    return Settings(_env_file=None, **settings)


class _RecipeUserId:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_as_string(self) -> str:
        return self._value


class _User:
    def __init__(self, user_id: str) -> None:
        self.id = user_id


class _FakeRecipe:
    """The emailpassword recipe implementation, recording what reached it."""

    def __init__(self) -> None:
        self.sign_ups: list[dict] = []
        self.password_updates: list[dict] = []

    async def sign_up(
        self,
        *,
        email,
        password,
        tenant_id,
        session,
        should_try_linking_with_session_user,
        user_context,
    ):
        self.sign_ups.append({"email": email, "password": password})
        return SignUpOkResult(user=_User("user-1"), recipe_user_id=_RecipeUserId("user-1"))

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
        self.password_updates.append({"email": email, "password": password})
        return UpdateEmailOrPasswordOkResult()


def _screened(recipe: _FakeRecipe, **overrides: object) -> _FakeRecipe:
    """The overrides as `init_supertokens` composes them, around a fake recipe."""
    settings = _settings(**overrides)
    screened = _screen_passwords(settings)(recipe)  # type: ignore[arg-type]
    return _revoke_sessions_on_password_change(screened)  # type: ignore[arg-type]


async def _sign_up(recipe, password: str):
    return await recipe.sign_up(
        email="new@example.com",
        password=password,
        tenant_id="public",
        session=None,
        should_try_linking_with_session_user=None,
        user_context={},
    )


async def _set_password(recipe, password: str | None):
    """The call the reset flow makes: an email-only change passes `None`."""
    return await recipe.update_email_or_password(
        recipe_user_id=_RecipeUserId("user-1"),
        email=None,
        password=password,
        apply_password_policy=None,
        tenant_id_for_password_policy="public",
        user_context={},
    )


@pytest.fixture
def sent_mail(monkeypatch) -> list[dict]:
    """Record what a sign-up hands to the verification-mail send."""
    sent: list[dict] = []

    async def fake_send(sign_up, email, tenant_id, user_context) -> None:
        sent.append({"sign_up": sign_up, "email": email, "tenant_id": tenant_id})

    monkeypatch.setattr(adapter, "_send_verification_email", fake_send)
    return sent


@pytest.fixture
def revoked(monkeypatch) -> list[str]:
    """Record revocations instead of asking the core to perform them.

    Ending sessions is a core call, and the core is Compose-only; the
    revocation's own behaviour is pinned in
    `tests/auth/unit/test_revoke_sessions_on_password_change.py`.
    """
    revoked: list[str] = []

    async def fake_revoke(user_id: str) -> None:
        revoked.append(user_id)

    monkeypatch.setattr(adapter, "revoke_all_sessions", fake_revoke)
    return revoked


async def test_a_weak_password_never_creates_an_account(sent_mail) -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    with pytest.raises(FieldError) as refused:
        await _sign_up(screened, WEAK)

    # The field error the sign-up form already renders, carrying the reason.
    assert [field.id for field in refused.value.form_fields] == ["password"]
    assert "too easy to guess" in refused.value.form_fields[0].error
    # Nothing reached the core, so no account exists and no mail went out.
    assert recipe.sign_ups == []
    assert sent_mail == []


async def test_a_breached_password_never_creates_an_account(monkeypatch) -> None:
    """The lookup is stubbed, because this pins the boundary, not HIBP."""
    _, suffix = split_sha1(STRONG)

    class _StubHibp:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def known_suffixes(self, _sha1_prefix: str) -> set[str]:
            return {suffix}

    monkeypatch.setattr(passwords_module, "HibpRangeClient", _StubHibp)
    recipe = _FakeRecipe()
    screened = _screened(recipe, password_breach_check_enabled=True)

    with pytest.raises(FieldError) as refused:
        await _sign_up(screened, STRONG)

    assert "data breach" in refused.value.form_fields[0].error
    assert recipe.sign_ups == []


async def test_a_short_password_is_refused_on_the_reset_path() -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    with pytest.raises(FieldError) as refused:
        await _set_password(screened, "Aa1!xy")

    assert "8 characters" in refused.value.form_fields[0].error
    assert recipe.password_updates == []


async def test_an_email_only_change_is_untouched() -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    result = await _set_password(screened, None)

    assert isinstance(result, UpdateEmailOrPasswordOkResult)
    assert recipe.password_updates == [{"email": None, "password": None}]


async def test_an_accepted_password_reaches_the_core(revoked) -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    result = await _set_password(screened, STRONG)

    assert isinstance(result, UpdateEmailOrPasswordOkResult)
    assert recipe.password_updates == [{"email": None, "password": STRONG}]
    # The composed override is still in place: an accepted change revokes.
    assert revoked == ["user-1"]


async def test_a_successful_sign_up_sends_the_verification_mail(sent_mail) -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    result = await _sign_up(screened, STRONG)

    assert isinstance(result, SignUpOkResult)
    assert recipe.sign_ups == [{"email": "new@example.com", "password": STRONG}]
    assert len(sent_mail) == 1
    assert sent_mail[0]["email"] == "new@example.com"
    assert sent_mail[0]["sign_up"].user.id == "user-1"
    assert sent_mail[0]["tenant_id"] == "public"


async def test_a_screened_out_password_does_not_revoke_sessions(revoked) -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    with pytest.raises(FieldError):
        await _set_password(screened, WEAK)

    assert revoked == []


async def test_the_composition_still_revokes_on_an_accepted_password(revoked) -> None:
    recipe = _FakeRecipe()
    screened = _screened(recipe)

    await _set_password(screened, STRONG)

    assert revoked == ["user-1"]
