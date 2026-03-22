"""Shared asyncio semaphore for Steam API concurrency control.

Both the Steam auth client (platforms module) and the Steam metadata client
(games module) must share the same semaphore to respect the max-3-concurrent
calls limit. Importing this module-level instance from ``shared/`` avoids any
cross-module dependency between ``platforms`` and ``games``.
"""

import asyncio

from shared.config import get_settings

_settings = get_settings()
steam_semaphore = asyncio.Semaphore(_settings.steam_max_concurrent)
