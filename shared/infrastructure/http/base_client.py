"""Base async HTTP client with retry and exponential backoff.

Wraps ``httpx.AsyncClient`` to provide automatic retries with exponential
backoff on transient failures (429 and 5xx responses). All derived clients
should inherit from or instantiate ``BaseHttpClient``.
"""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BASE_DELAY = 1.0
_DEFAULT_MAX_DELAY = 30.0
_DEFAULT_TIMEOUT = 10.0

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class BaseHttpClient:
    """Async HTTP client with configurable retry and exponential backoff.

    Args:
        base_url: Base URL prepended to all request paths.
        headers: Default headers sent with every request.
        max_retries: Maximum number of retry attempts on transient errors.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        base_delay: float = _DEFAULT_BASE_DELAY,
        max_delay: float = _DEFAULT_MAX_DELAY,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url
        self._default_headers = headers or {}
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._timeout = timeout

    def _build_client(self) -> httpx.AsyncClient:
        """Create a new httpx.AsyncClient with the configured defaults."""
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._default_headers,
            timeout=self._timeout,
        )

    def _should_retry(self, response: httpx.Response) -> bool:
        """Return True if the response status warrants a retry."""
        return response.status_code in _RETRYABLE_STATUS_CODES

    def _calculate_delay(self, attempt: int) -> float:
        """Compute exponential backoff delay capped at max_delay."""
        delay: float = self._base_delay * float(2**attempt)
        return min(delay, self._max_delay)

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an HTTP request with automatic retry on transient failures.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: URL path or absolute URL.
            **kwargs: Additional arguments forwarded to ``httpx.AsyncClient.request``.

        Returns:
            The last ``httpx.Response`` received.

        Raises:
            httpx.HTTPError: If all retry attempts are exhausted or a
                non-retryable error occurs.
        """
        last_response: httpx.Response | None = None

        async with self._build_client() as client:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.request(method, url, **kwargs)
                    last_response = response

                    if not self._should_retry(response):
                        return response

                    if attempt < self._max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            "Request to %s returned %s, retrying in %.1fs (attempt %d/%d)",
                            url,
                            response.status_code,
                            delay,
                            attempt + 1,
                            self._max_retries,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Request to %s failed with %s after %d attempts",
                            url,
                            response.status_code,
                            self._max_retries + 1,
                        )

                except httpx.TimeoutException:
                    logger.error(
                        "Request to %s timed out (attempt %d/%d)",
                        url,
                        attempt + 1,
                        self._max_retries + 1,
                    )
                    if attempt >= self._max_retries:
                        raise
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)

                except httpx.HTTPError:
                    logger.error(
                        "Request to %s raised an HTTP error (attempt %d/%d)",
                        url,
                        attempt + 1,
                        self._max_retries + 1,
                    )
                    raise

        assert last_response is not None
        return last_response

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a GET request with retry."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Perform a POST request with retry."""
        return await self.request("POST", url, **kwargs)
