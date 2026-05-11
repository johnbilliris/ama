"""ProblemDetails response model w/ advisory-only banner (T-S15, FR-030)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    ama_advisory_only: bool = True

    @classmethod
    def of(
        cls,
        *,
        title: str,
        status: int,
        detail: str | None = None,
        type: str = "about:blank",
    ) -> ProblemDetails:
        return cls(type=type, title=title, status=status, detail=detail)


def advisory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure `ama_advisory_only=True` is set on any outbound payload."""
    payload.setdefault("ama_advisory_only", True)
    return payload
