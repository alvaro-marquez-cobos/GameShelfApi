from abc import ABC, abstractmethod
from typing import Any

from shared.domain.entities.user import AuthenticatedUser


class ISyncUserUseCase(ABC):
    @abstractmethod
    async def execute(self, user: AuthenticatedUser) -> dict[str, Any]: ...
