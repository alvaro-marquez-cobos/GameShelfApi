"""Pydantic schemas for settings HTTP endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class NotificationPrefsResponse(BaseModel):
    """Current notification preferences."""

    model_config = ConfigDict(populate_by_name=True)

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
