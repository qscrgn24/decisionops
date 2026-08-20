from __future__ import annotations

from collections.abc import Iterable

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "object-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": (
        "camera=(), microphone=(), geolocation=()"
    ),
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


class BrowserSecurityMiddleware:
    def __init__(self, app: ASGIApp, *, allowed_origins: Iterable[str], enable_hsts: bool) -> None:
        self.app = app
        self.allowed_origins = frozenset(origin.strip() for origin in allowed_origins if origin.strip())
        self.enable_hsts = enable_hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self._is_forbidden_browser_request(scope):
            response = JSONResponse(status_code=403, content={"detail": "Cross-site request blocked"})

            await response(scope, receive, self._security_header_send(send))
            return

        await self.app(scope, receive, self._security_header_send(send))

    def _is_forbidden_browser_request(self, scope: Scope) -> bool:
        method = scope.get("method", "GET").upper()

        if method not in _UNSAFE_METHODS:
            return False

        fetch_site = self._get_header(scope, "sec-fetch-site")

        if fetch_site == "cross-site":
            return True

        origin = self._get_header(scope, "origin")

        if origin is not None and origin not in self.allowed_origins:
            return True

        return False

    def _security_header_send(self, send: Send) -> Send:
        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)

                for name, value in _SECURITY_HEADERS.items():
                    headers[name] = value

                if self.enable_hsts:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

            await send(message)

        return wrapped_send

    @staticmethod
    def _get_header(scope: Scope, name: str) -> str | None:
        headers = Headers(scope=scope)
        return headers.get(name)
