import time

from modules.auth.domain.interfaces.use_cases.logout import ILogoutUseCase
from shared.domain.interfaces.firebase_auth import IFirebaseAuthProvider
from shared.domain.interfaces.token_blacklist import ITokenBlacklist


class LogoutUseCase(ILogoutUseCase):
    def __init__(
        self,
        firebase_auth: IFirebaseAuthProvider,
        token_blacklist: ITokenBlacklist,
    ) -> None:
        self._firebase_auth = firebase_auth
        self._token_blacklist = token_blacklist

    async def execute(self, token: str) -> None:
        decoded = await self._firebase_auth.verify_token(token)

        uid: str = decoded["uid"]
        iat: int = decoded.get("iat", 0)
        exp: int = decoded.get("exp", 0)
        token_id: str = decoded.get("jti") or f"{uid}:{iat}"

        now = int(time.time())
        ttl = max(exp - now, 1) if exp > now else 1

        await self._token_blacklist.add(token_id, ttl)
