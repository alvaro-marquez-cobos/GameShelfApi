"""Security headers middleware for the GameShelf API.

Adds HTTP response headers that instruct the browser on how to handle content
securely, reducing the attack surface for common web vulnerabilities.

Applied headers:

- ``X-Content-Type-Options``: Prevents MIME-type sniffing. Forces the browser
  to trust the declared ``Content-Type`` instead of guessing it, avoiding cases
  where a file with embedded scripts could be executed as code.

- ``Strict-Transport-Security``: Enforces HTTPS for all future requests once
  the client has connected at least once over TLS. Eliminates the window where
  a man-in-the-middle attack could intercept an unencrypted initial request.

- ``X-Frame-Options``: Prevents the response from being embedded in an
  ``<iframe>``, blocking clickjacking attacks where a malicious page overlays
  an invisible frame over a legitimate UI to trick users into unintended clicks.

- ``Referrer-Policy``: Controls what URL information is included in the
  ``Referer`` header when making requests. Set to ``no-referrer`` so internal
  API paths are never leaked to third-party services.

Note on ``Content-Security-Policy``:
    CSP is intentionally omitted for API responses. However, FastAPI serves
    Swagger UI at ``/docs`` and ``/redoc``, which are HTML pages that would
    benefit from a CSP policy. This is deferred until a dedicated Swagger
    hardening task is addressed.
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that attaches security-related HTTP headers to every response.

    Inherits from ``BaseHTTPMiddleware`` and intercepts the response after the
    route handler runs, injecting the headers before sending it to the client.

    This middleware applies the four headers described in the module docstring.
    ``Content-Security-Policy`` is intentionally omitted — see the module-level
    note for the rationale.

    Usage::

        app.add_middleware(SecurityHeadersMiddleware)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and attach security headers to the response.

        Args:
            request: The incoming HTTP request.
            call_next: Callable that passes the request to the next middleware
                or route handler and returns the response.

        Returns:
            The original response with security headers added.
        """
        response = await call_next(request)

        # Prevent MIME-type sniffing: the browser must treat the response
        # exactly as the declared Content-Type, never guessing or overriding it.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enforce HTTPS for one year (31 536 000 seconds) on this domain and
        # all subdomains. Once a client sees this header, it will upgrade HTTP
        # requests to HTTPS on its own, removing the unencrypted first-hop.
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Deny embedding this response inside an <iframe> on any origin.
        # Eliminates clickjacking: attackers cannot overlay an invisible frame
        # over a legitimate UI to capture unintended user interactions.
        response.headers["X-Frame-Options"] = "DENY"

        # Strip the Referer header entirely on all cross-origin requests.
        # Prevents internal API paths and query parameters from leaking to
        # third-party services referenced in responses.
        response.headers["Referrer-Policy"] = "no-referrer"

        return response
