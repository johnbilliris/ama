"""Recovery handover signing route (spec-035 FR-007 / SC-008).

Wires :class:`RecoveryHandoverService` to ``POST /api/recovery/handover/sign``
and returns the
[Q10 extension envelope](../../../../specs/035-webapp-capstone-closure/contracts/production-auth-extension.contract.md)
on validation / signing-key-expired errors.
"""

from __future__ import annotations

from typing import Any

from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from app.services.recovery_handover_service import (
    HandoverRequest,
    HandoverResponse,
    HandoverValidationError,
    RecoveryHandoverService,
    SigningKeyExpiredError,
)
from fastapi import APIRouter, Request

router = APIRouter(prefix="/recovery", tags=["recovery-handover"])


@router.post("/handover/sign", response_model=HandoverResponse)
async def sign_handover(payload: HandoverRequest, request: Request) -> HandoverResponse:
    service: RecoveryHandoverService | None = getattr(
        request.app.state, "recovery_handover_service", None
    )
    if service is None:
        audit_repo: Any | None = getattr(
            request.app.state, "audit_repository", None
        )
        service = RecoveryHandoverService(audit_repository=audit_repo)

    correlation_id = request.headers.get("X-Correlation-Id")

    try:
        return await service.sign(payload, correlation_id=correlation_id)
    except SigningKeyExpiredError as exc:
        # Closed-set: surface as schema_invalid with operator-facing detail per
        # production-auth-extension contract; the UI banner uses the detail to
        # render the rotation runbook link (T044).
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.SCHEMA_INVALID,
            detail=f"signing_key_expired: {exc}",
            correlation_id=correlation_id,
        ) from exc
    except HandoverValidationError as exc:
        code = (
            ExtensionErrorCode.SEED_NOT_READY
            if exc.code == "seed_not_ready"
            else ExtensionErrorCode.SCHEMA_INVALID
        )
        raise ExtensionEnvelopeError(
            code,
            detail=str(exc),
            correlation_id=correlation_id,
        ) from exc
