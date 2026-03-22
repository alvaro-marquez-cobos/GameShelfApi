from abc import ABC, abstractmethod


class IDeleteAccountUseCase(ABC):
    @abstractmethod
    async def execute(self, uid: str) -> None: ...
