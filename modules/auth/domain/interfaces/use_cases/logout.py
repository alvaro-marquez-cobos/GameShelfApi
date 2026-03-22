from abc import ABC, abstractmethod


class ILogoutUseCase(ABC):
    @abstractmethod
    async def execute(self, token: str) -> None: ...
