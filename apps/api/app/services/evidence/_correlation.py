"""Correlation-ID dependency for /api/v1/evidence/* (T-S09)."""

from __future__ import annotations

import uuid

from fastapi import Header, Request, Response

HEADER_NAME = "x-ama-correlation-id"


def correlation_id_dep(
    request: Request,
    response: Response,
    incoming: str | None = Header(default=None, alias=HEADER_NAME),
) -> str:
    cid = incoming or request.headers.get(HEADER_NAME) or uuid.uuid4().hex
    response.headers[HEADER_NAME] = cid
    return cid
