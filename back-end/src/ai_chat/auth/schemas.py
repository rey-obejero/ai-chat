from datetime import datetime

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from ai_chat.auth.display_name import validate_display_name
from ai_chat.llm import ResponseStyle

# The cap on standing instructions (FR-24). They ride every reply, so they are
# bounded here rather than left to the provider's own context limit.
INSTRUCTIONS_MAX_LENGTH = 2000


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    # What the account is called, and whether the first-run prompt has been
    # answered (FR-7). They travel with the account because the prompt's
    # first-run check and the settings field both read them from here.
    display_name: str
    name_prompt_seen: bool
    # The account owner's own settings, the way the email is theirs: the
    # settings form loads in one call and always sees what the service holds.
    instructions: str | None
    response_style: ResponseStyle
    # Whether the address has been verified (FR-4). Read from the auth service
    # rather than stored here: the recipe owns this state, and a copy in the row
    # could disagree with it. It defaults to False, so a payload assembled
    # without the flag claims nothing.
    email_verified: bool = False
    created_at: datetime


class PreferencesUpdate(BaseModel):
    """A partial update of the account's personalisation (FR-24, FR-25).

    Changing either affects future replies only: nothing already said is
    rewritten, which is why this is a settings write and not a conversation one.
    """

    model_config = ConfigDict(extra="forbid")

    instructions: str | None = None
    response_style: ResponseStyle | None = None

    @field_validator("instructions", "response_style", mode="before")
    @classmethod
    def _reject_null(cls, value: object, info: ValidationInfo) -> object:
        # A field is absent or it carries a value. Clearing instructions is
        # sending them empty, not sending `null`.
        if value is None:
            raise ValueError(f"{info.field_name} may not be null; omit it instead.")
        return value

    @field_validator("instructions")
    @classmethod
    def _clean_instructions(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) > INSTRUCTIONS_MAX_LENGTH:
            raise ValueError(f"instructions must be at most {INSTRUCTIONS_MAX_LENGTH} characters")
        return cleaned


class ProfileUpdate(BaseModel):
    """A partial update of the caller's name and first-run prompt state (FR-7).

    Both fields are optional and absent means "leave it alone", so the schema's
    validation is where a name is judged: `auth.display_name` owns the rules,
    and a refusal becomes the ordinary 422 whose message says what is wrong.
    """

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    name_prompt_seen: bool | None = None

    @field_validator("display_name", "name_prompt_seen", mode="before")
    @classmethod
    def _reject_null(cls, value: object, info: ValidationInfo) -> object:
        # A field is absent or it carries a value; "clear my name" is not a
        # state an account can be in (FR-7).
        if value is None:
            raise ValueError(f"{info.field_name} may not be null; omit it instead.")
        return value

    @field_validator("display_name")
    @classmethod
    def _valid_name(cls, value: str) -> str:
        return validate_display_name(value)


class SocialProviderRead(BaseModel):
    """One configured social provider, as the sign-in screen needs it."""

    id: str
    name: str


class SocialProvidersRead(BaseModel):
    """Which social buttons to render.

    Identifiers and display names only — never credential state. The front end
    needs this before sign-in, so the endpoint is public, and it must not
    disclose more than which buttons appear.
    """

    providers: list[SocialProviderRead]
