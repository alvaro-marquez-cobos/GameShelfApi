from abc import ABC, abstractmethod


class ITokenBlacklist(ABC):
    @abstractmethod
    async def add(self, token_id: str, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def is_blacklisted(self, token_id: str) -> bool: ...
