from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.user import AuthenticatedUser


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_uid(self, uid: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def upsert(self, user: AuthenticatedUser) -> dict[str, Any]: ...

    @abstractmethod
    async def delete(self, uid: str) -> None: ...
