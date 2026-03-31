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
