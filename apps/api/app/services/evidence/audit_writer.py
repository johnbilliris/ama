"""Audit write wrapper with Strong consistency + exponential backoff (T-AMD-05, FR-044)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from ._clients import get_registry
from ._problem_details import ProblemDetails

logger = logging.getLogger(__name__)

BACKOFF_SECONDS = [0.25, 1.0, 4.0]


async def write_audit_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Write to evidence_audit with Strong consistency and 3-attempt exponential backoff.

    Raises AuditWriteUnavailableError (maps to 503) on exhaustion per FR-044.
    """
    registry = get_registry()
    container = registry.get("evidence_audit")

    last_exc: Exception | None = None
    for attempt, backoff in enumerate(BACKOFF_SECONDS):
        try:
            result = container.create_item(entry)
            logger.debug("audit write succeeded on attempt %d", attempt + 1)
            return result
        except Exception as exc:
            last_exc = exc
            logger.warning("audit write attempt %d failed: %s", attempt + 1, exc)
            if attempt < len(BACKOFF_SECONDS) - 1:
                await asyncio.sleep(backoff)

    logger.error("audit write exhausted all retries: %s", last_exc)
    raise AuditWriteUnavailableError(str(last_exc))


class AuditWriteUnavailableError(Exception):
    """Raised when all retry attempts are exhausted for an audit write."""

    def to_problem_details(self) -> ProblemDetails:
        return ProblemDetails.of(
            status=503,
            title="audit-write-unavailable",
            detail=str(self),
            type="https://ama.example/errors/audit-write-unavailable",
        )
