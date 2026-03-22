import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from shared.domain.interfaces.cleanup_registry import ICleanupRegistry


class CleanupRegistry(ICleanupRegistry):
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[str], Coroutine[Any, Any, None]]] = {}

    def register(self, name: str, handler: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        self._handlers[name] = handler

    async def execute_all(self, uid: str) -> None:
        await asyncio.gather(*(handler(uid) for handler in self._handlers.values()))
