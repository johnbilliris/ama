"""Explicit startup containment for first-bootstrap validation."""

from __future__ import annotations

import os

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def bootstrap_hold_requested() -> bool:
    value = os.getenv("AMA_BOOTSTRAP_HOLD", "false").strip().lower()
    if value not in {"true", "false", "1", "0"}:
        raise ValueError("AMA_BOOTSTRAP_HOLD must be true, false, 1 or 0")
    return value in {"true", "1"}


class BootstrapHoldMiddleware:
    def __init__(self, app: ASGIApp, *, allowed_paths: frozenset[str]) -> None:
        self.app = app
        self.allowed_paths = allowed_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1013})
            return
        if scope["type"] == "http" and (
            scope["path"] not in self.allowed_paths or scope["method"] not in {"GET", "HEAD"}
        ):
            await JSONResponse({"status": "held", "detail": "Application bootstrap hold is active"}, status_code=503)(
                scope, receive, send
            )
            return
        await self.app(scope, receive, send)
