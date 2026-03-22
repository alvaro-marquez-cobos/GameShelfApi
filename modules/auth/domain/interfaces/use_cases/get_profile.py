from abc import ABC, abstractmethod
from typing import Any


class IGetProfileUseCase(ABC):
    @abstractmethod
    async def execute(self, uid: str) -> dict[str, Any]: ...
