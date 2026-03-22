from abc import ABC, abstractmethod
from typing import Any


class IFirebaseAuthProvider(ABC):
    @abstractmethod
    async def verify_token(self, id_token: str) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_user(self, uid: str) -> None: ...
