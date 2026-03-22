"""Pydantic request/response schemas for the auth HTTP endpoints."""

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    """Response schema containing the user's profile information."""
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    is_guest: bool
    provider: str
    created_at: str | None = None
    updated_at: str | None = None


class MessageResponse(BaseModel):
    """Generic response schema for endpoints that return a simple message."""
    message: str
