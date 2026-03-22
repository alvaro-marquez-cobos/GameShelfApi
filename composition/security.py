from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from composition.dependencies import get_firebase_auth_provider, get_token_blacklist
from shared.domain.entities.user import AuthenticatedUser
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.token_blacklist import ITokenBlacklist
from shared.exceptions import UnauthorizedException

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
    token_blacklist: Annotated[ITokenBlacklist, Depends(get_token_blacklist)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException("Missing authorization header")

    token = credentials.credentials
    decoded = await firebase_auth.verify_token(token)

    uid: str = decoded["uid"]
    iat: int = decoded.get("iat", 0)
    token_id: str = decoded.get("jti") or f"{uid}:{iat}"

    if await token_blacklist.is_blacklisted(token_id):
        raise UnauthorizedException("Token has been revoked")

    provider: str = decoded.get("firebase", {}).get("sign_in_provider", "anonymous")
    is_guest = provider == "anonymous"

    return AuthenticatedUser(
        uid=uid,
        email=decoded.get("email"),
        display_name=decoded.get("name"),
        photo_url=decoded.get("picture"),
        is_guest=is_guest,
        provider=provider,
    )


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    firebase_auth: Annotated[IFirebaseAuthProvider, Depends(get_firebase_auth_provider)],
    token_blacklist: Annotated[ITokenBlacklist, Depends(get_token_blacklist)],
) -> AuthenticatedUser | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, firebase_auth, token_blacklist)
    except UnauthorizedException:
        return None
