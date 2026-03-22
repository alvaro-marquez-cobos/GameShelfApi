from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    is_guest: bool
    provider: str
    created_at: str | None = None
    updated_at: str | None = None


class MessageResponse(BaseModel):
    message: str
