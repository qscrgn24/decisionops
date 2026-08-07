from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestBodyTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
            self,
            scope: Scope,
            receive: Receive,
            send: Send,      
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = self._get_content_length(scope)

        if content_length is not None and content_length > self.max_bytes:
            await self._send_too_large(scope, receive, send)
            return

        bytes_received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal bytes_received

            message = await receive()

            if message["type"] == "http.request":
                body = message.get("body", b"")
                bytes_received += len(body)

                if bytes_received > self.max_bytes:
                    raise RequestBodyTooLarge

            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True

            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except RequestBodyTooLarge:
            if response_started:
                return

            await self._send_too_large(scope, receive, send)

    @staticmethod
    def _get_content_length(scope: Scope) -> int | None:
        for key, value in scope.get("headers", []):
            if key.lower() != b"content-length":
                continue

            try:
                content_length = int(value)
            except ValueError:
                return None

            if content_length < 0:
                return None

            return content_length

        return None

    @staticmethod
    async def _send_too_large(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Request body too large"},
        )
        await response(scope, receive, send)