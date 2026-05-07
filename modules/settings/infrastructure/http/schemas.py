"""Pydantic schemas for settings HTTP endpoints."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NotificationPrefsResponse(BaseModel):
    """Current notification preferences."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    deals_enabled: bool = Field(alias="dealsEnabled")


class UpdateNotificationPrefsRequest(BaseModel):
    """Notification preference update payload."""

    model_config = ConfigDict(populate_by_name=True)

    deals_enabled: bool = Field(alias="dealsEnabled")


class CountryResponse(BaseModel):
    """Current ITAD country preference."""

    country_code: str | None = None


class UpdateCountryRequest(BaseModel):
    """ITAD country update payload."""

    model_config = ConfigDict(populate_by_name=True)

    country_code: str = Field(min_length=2, max_length=2)


# ---------------------------------------------------------------------------
# Push notification tokens
# ---------------------------------------------------------------------------


class RegisterPushTokenRequest(BaseModel):
    """Register a push notification token from the mobile client."""

    model_config = ConfigDict(populate_by_name=True)

    expo_token: str = Field(min_length=1, description="Expo push token")
    platform: Literal["ios", "android", "web"]


class RegisterPushTokenResponse(BaseModel):
    """Response after registering a push notification token."""

    model_config = ConfigDict(populate_by_name=True)

    token_id: str = Field(alias="tokenId", description="Server-assigned token ID")
