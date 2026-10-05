"""Dead-letter inspection and manual redelivery endpoints (FR-003a)."""

from __future__ import annotations

import logging

from app.middleware.auth import AuthenticatedIdentity, authorize_management
from app.services.dead_letter_service import DeadLetterService
from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dead-letters", tags=["dead-letters"])
service = DeadLetterService()


@router.post(
    "/{entry_id}/redeliver",
    status_code=202,
    dependencies=[Depends(authorize_management)],
)
async def redeliver_dead_letter(
    entry_id: str,
    identity: AuthenticatedIdentity = Depends(authorize_management),
) -> dict[str, str]:
    """Manually trigger redelivery of a dead-lettered handoff (Section 3b + 5b)."""
    resolved = service.resolve_entry(
        entry_id=entry_id,
        resolution="replayed",
        resolved_by_persona_id=str(identity.get("sub", "management-api")),
        notes="manual redelivery requested",
    )

    logger.info(
        "dead_letter_manual_redeliver",
        extra={
            "entry_id": entry_id,
            "initiated_by": identity.get("sub", "unknown"),
        },
    )

    return {
        "entry_id": resolved.entry_id,
        "status": "replayed",
        "message": "Redelivery initiated",
    }
