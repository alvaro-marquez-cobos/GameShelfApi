"""Pydantic request/response schemas for the platforms HTTP layer."""

from pydantic import BaseModel

from shared.domain.enums.platform import Platform


class LinkedPlatformResponse(BaseModel):
    """Response schema for a single linked platform."""

    platform: Platform
    username: str
    avatar_url: str | None = None
    linked_at: str = ""


class LinkSteamRequest(BaseModel):
    """OpenID 2.0 callback parameters forwarded from the client."""

    openid_params: dict[str, str]


class LinkCodeRequest(BaseModel):
    """OAuth2 authorization code for Epic or GOG linking."""

    code: str


class LinkPsnRequest(BaseModel):
    """NPSSO cookie value for PSN linking."""

    npsso: str


class SteamAuthUrlResponse(BaseModel):
    """Response containing the Steam OpenID redirect URL."""

    url: str


class OAuthAuthUrlResponse(BaseModel):
    """Response containing the OAuth2 redirect URL for Epic or GOG."""

    url: str
