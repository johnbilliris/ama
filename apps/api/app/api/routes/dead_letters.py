"""Dead-letter inspection and manual redelivery endpoints (FR-003a)."""

from __future__ import annotations

import logging
from typing import Any

from app.middleware.auth import authorize_management
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dead-letters", tags=["dead-letters"])

# In-memory store for local dev — replaced by Cosmos DB in production
_dead_letter_store: dict[str, dict[str, Any]] = {}


def _get_store():
    """Get the dead-letter store (dependency injection point)."""
    return _dead_letter_store


@router.get("")
async def list_dead_letters(
    incident_id: str | None = None,
    target_agent: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """List dead-letter entries with optional filters (Section 3a + 5a)."""
    store = _get_store()
    entries = list(store.values())

    if incident_id:
        entries = [e for e in entries if e.get("incident_id") == incident_id]
    if target_agent:
        entries = [e for e in entries if e.get("target_agent") == target_agent]
    if status:
        entries = [e for e in entries if e.get("status") == status]

    total = len(entries)
    page = entries[offset : offset + limit]
    return {"items": page, "total": total, "limit": limit, "offset": offset}


@router.post(
    "/{handoff_id}/redeliver",
    status_code=202,
    dependencies=[Depends(authorize_management)],
)
async def redeliver_dead_letter(
    handoff_id: str,
    identity: dict = Depends(authorize_management),
) -> dict:
    """Manually trigger redelivery of a dead-lettered handoff (Section 3b + 5b)."""
    store = _get_store()
    entry = store.get(handoff_id)

    if not entry or entry.get("status") not in ("dead_lettered",):
        # Check if permanently_failed — return 409
        if entry and entry.get("status") == "permanently_failed":
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "permanently_failed",
                    "message": "This handoff has been permanently failed and cannot be redelivered",
                    "handoff_id": handoff_id,
                },
            )
        raise HTTPException(status_code=404, detail="Handoff not found or not in dead_lettered status")

    # Reset status and increment manual attempts
    entry["status"] = "pending"
    entry["manual_redeliver_attempts"] = entry.get("manual_redeliver_attempts", 0) + 1

    logger.info(
        "dead_letter_manual_redeliver",
        extra={
            "handoff_id": handoff_id,
            "initiated_by": identity.get("sub", "unknown"),
        },
    )

    return {
        "handoff_id": handoff_id,
        "status": "pending",
        "message": "Redelivery initiated",
    }
