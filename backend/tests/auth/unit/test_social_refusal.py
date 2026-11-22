"""A social sign-in must be refused when its email already has an account.

The SDK's default account linking does the opposite — it lets a verified email
create a second account — so the rule is enforced in `_refuse_sign_in_when_email_exists`
(ADR-0034). These tests pin the three cases that matter.
"""

from supertokens_python.recipe.thirdparty.interfaces import SignInUpNotAllowed

import ai_chat.auth.adapter_supertokens as adapter
from ai_chat.auth.adapter_supertokens import _refuse_sign_in_when_email_exists


class _ThirdParty:
    def __init__(self, provider_id: str, user_id: str) -> None:
        self.id = provider_id
        self.user_id = user_id


class _Login:
    def __init__(self, recipe_id: str, third_party: _ThirdParty | None = None) -> None:
        self.recipe_id = recipe_id
        self.third_party = third_party


class _User:
    def __init__(self, *logins: _Login) -> None:
        self.login_methods = list(logins)


class _FakeRecipe:
    def __init__(self) -> None:
        self.calls = 0

    async def sign_in_up(self, **_kwargs):
        self.calls += 1
        return "allowed"


def _existing_users(monkeypatch, users) -> None:
    async def fake_list_users_by_account_info(*_args, **_kwargs):
        return users

    monkeypatch.setattr(adapter, "list_users_by_account_info", fake_list_users_by_account_info)


async def _sign_in(recipe, *, third_party_user_id: str = "idp-1"):
    wrapped = _refuse_sign_in_when_email_exists(recipe)  # type: ignore[arg-type]
    return await wrapped.sign_in_up(
        third_party_id="test-idp",
        third_party_user_id=third_party_user_id,
        email="user@example.com",
        is_verified=True,
        oauth_tokens={},
        raw_user_info_from_provider=None,
        session=None,
        should_try_linking_with_session_user=None,
        tenant_id="public",
        user_context={},
    )


async def test_refuses_when_the_email_belongs_to_a_password_account(monkeypatch) -> None:
    _existing_users(monkeypatch, [_User(_Login("emailpassword"))])
    recipe = _FakeRecipe()

    result = await _sign_in(recipe)

    assert isinstance(result, SignInUpNotAllowed)
    assert recipe.calls == 0


async def test_allows_a_returning_social_identity(monkeypatch) -> None:
    # The account with that email is *this* provider identity, so it is the
    # user's own account, not a conflict.
    _existing_users(
        monkeypatch,
        [_User(_Login("thirdparty", _ThirdParty("test-idp", "idp-1")))],
    )
    recipe = _FakeRecipe()

    result = await _sign_in(recipe)

    assert result == "allowed"
    assert recipe.calls == 1


async def test_allows_a_new_email(monkeypatch) -> None:
    _existing_users(monkeypatch, [])
    recipe = _FakeRecipe()

    result = await _sign_in(recipe)

    assert result == "allowed"
    assert recipe.calls == 1
