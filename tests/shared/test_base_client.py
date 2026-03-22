"""Tests for the BaseHttpClient retry and backoff behavior."""

import httpx
import pytest
import respx

from shared.infrastructure.http.base_client import BaseHttpClient


@pytest.fixture
def client() -> BaseHttpClient:
    return BaseHttpClient(
        base_url="https://example.com",
        max_retries=2,
        base_delay=0.01,
        max_delay=0.1,
        timeout=5.0,
    )


@pytest.mark.asyncio
async def test_successful_request_returns_response(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        mock.get("/api/data").mock(return_value=httpx.Response(200, json={"ok": True}))
        response = await client.get("/api/data")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_retries_on_500_and_succeeds(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/api/data").mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        response = await client.get("/api/data")

    assert response.status_code == 200
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_retries_on_429_and_succeeds(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/api/rate").mock(
            side_effect=[
                httpx.Response(429),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        response = await client.get("/api/rate")

    assert response.status_code == 200
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_returns_last_response_after_max_retries_exhausted(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/api/fail").mock(return_value=httpx.Response(503))
        response = await client.get("/api/fail")

    # max_retries=2 means 3 total attempts
    assert response.status_code == 503
    assert route.call_count == 3


@pytest.mark.asyncio
async def test_does_not_retry_on_4xx_client_errors(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/api/notfound").mock(return_value=httpx.Response(404))
        response = await client.get("/api/notfound")

    assert response.status_code == 404
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_raises_on_timeout_after_max_retries(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        mock.get("/api/slow").mock(side_effect=httpx.TimeoutException("timed out"))

        with pytest.raises(httpx.TimeoutException):
            await client.get("/api/slow")


@pytest.mark.asyncio
async def test_post_request_succeeds(client: BaseHttpClient) -> None:
    with respx.mock(base_url="https://example.com") as mock:
        mock.post("/api/create").mock(return_value=httpx.Response(201, json={"id": "123"}))
        response = await client.post("/api/create", json={"name": "test"})

    assert response.status_code == 201
    assert response.json()["id"] == "123"


@pytest.mark.asyncio
async def test_default_headers_are_sent(client: BaseHttpClient) -> None:
    client_with_headers = BaseHttpClient(
        base_url="https://example.com",
        headers={"X-Custom": "value"},
        max_retries=0,
    )
    with respx.mock(base_url="https://example.com") as mock:
        route = mock.get("/api/check").mock(return_value=httpx.Response(200))
        await client_with_headers.get("/api/check")

    assert route.call_count == 1
    sent_headers = route.calls[0].request.headers
    assert sent_headers["x-custom"] == "value"
