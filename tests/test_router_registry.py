"""Smoke tests for registered API routes."""

from fastapi.routing import APIRoute

from main import app


def test_phase5_routes_are_registered() -> None:
    routes = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
    }

    expected = {
        ("GET", "/api/v1/library"),
        ("GET", "/api/v1/library/stats"),
        ("POST", "/api/v1/library/sync"),
        ("GET", "/api/v1/games/{game_id}"),
        ("GET", "/api/v1/games/{game_id}/dlcs"),
        ("GET", "/api/v1/search"),
        ("GET", "/api/v1/wishlist"),
        ("POST", "/api/v1/wishlist"),
        ("DELETE", "/api/v1/wishlist/{item_id}"),
        ("GET", "/api/v1/wishlist/check/{game_id}"),
        ("GET", "/api/v1/home"),
        ("GET", "/api/v1/home/popular"),
        ("GET", "/api/v1/settings/notifications"),
        ("PUT", "/api/v1/settings/notifications"),
        ("GET", "/api/v1/platforms/steam/login-url"),
        ("POST", "/api/v1/platforms/steam/link/openid"),
        ("POST", "/api/v1/platforms/epic/link/authcode"),
        ("POST", "/api/v1/platforms/epic/link/gdpr"),
        ("GET", "/api/v1/platforms/epic/login-url"),
        ("GET", "/api/v1/platforms/psn/login-url"),
    }

    assert expected.issubset(routes)
