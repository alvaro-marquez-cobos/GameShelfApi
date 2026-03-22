from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any


class ICleanupRegistry(ABC):
    @abstractmethod
    def register(self, name: str, handler: Callable[[str], Coroutine[Any, Any, None]]) -> None: ...

    @abstractmethod
    async def execute_all(self, uid: str) -> None: ...
