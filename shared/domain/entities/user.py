from dataclasses import dataclass


@dataclass
class AuthenticatedUser:
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    is_guest: bool
    provider: str
