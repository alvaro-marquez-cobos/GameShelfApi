"""Pydantic request/response schemas for the platforms HTTP layer."""

from pydantic import BaseModel, ConfigDict, Field

from shared.domain.enums.platform import Platform


class LinkedPlatformResponse(BaseModel):
    """Response schema for a single linked platform."""

    model_config = ConfigDict(populate_by_name=True)

    platform: Platform
    external_user_id: str = Field(alias="externalUserId")
    username: str | None = None
    avatar_url: str | None = None
    linked_at: str = Field(default="", alias="linkedAt")


class LinkSteamRequest(BaseModel):
    """OpenID 2.0 callback parameters forwarded from the client."""

    model_config = ConfigDict(populate_by_name=True)

    openid_params: dict[str, str]


class LinkCodeRequest(BaseModel):
    """OAuth2 authorization code for Epic or GOG linking."""

    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(alias="authCode")


class LinkPsnRequest(BaseModel):
    """NPSSO cookie value for PSN linking."""

    model_config = ConfigDict(populate_by_name=True)

    npsso: str = Field(alias="npssoCode")


class LinkSteamByIdRequest(BaseModel):
    """Steam profile URL, vanity, or SteamID64 input."""

    model_config = ConfigDict(populate_by_name=True)

    profile_url_or_id: str = Field(alias="profileUrlOrId")


class LinkSteamOpenIdRequest(BaseModel):
    """Steam OpenID callback payload."""

    model_config = ConfigDict(populate_by_name=True)

    callback_url: str | None = Field(default=None, alias="callbackUrl")
    callback_params: dict[str, str] = Field(alias="callbackParams")


class EpicAuthCodeRequest(BaseModel):
    """Epic OAuth authorization code payload."""

    model_config = ConfigDict(populate_by_name=True)

    auth_code: str = Field(alias="authCode")


class EpicGdprRequest(BaseModel):
    """Raw Epic GDPR export JSON payload."""

    model_config = ConfigDict(populate_by_name=True)

    json_content: str = Field(alias="jsonContent")


class SteamAuthUrlResponse(BaseModel):
    """Response containing the Steam OpenID redirect URL."""

    url: str


class OAuthAuthUrlResponse(BaseModel):
    """Response containing the OAuth2 redirect URL for Epic or GOG."""

    url: str
