"""``POST /api/offline/replay`` route + service (spec-035 T030).

Service-Worker replays queued field actions on reconnect. Life-safety tier
drains first; idempotent dedupe by ``(persona_id, client_correlation_id)``;
``captured_ts`` preserved verbatim on the appended audit row (SC-007).

Per the [contract](../../../../specs/035-webapp-capstone-closure/contracts/offline-replay.openapi.yaml):

- Batch ≤ 50 entries; > 50 ⇒ 413.
- All entries in a batch share ``tier``.
- Idempotent dedupe across the same persona + ``client_correlation_id``.
- Admin impersonation triggers paired-row emission via ``audit_appender``.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.repositories.audit_repository import AuditRepository
from app.schemas.envelope_errors import ExtensionEnvelopeError
from app.schemas.extension_envelope import ExtensionErrorCode
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

router = APIRouter(prefix="/offline", tags=["offline"])

logger = logging.getLogger(__name__)

_MAX_BATCH = 50


class QueueEntryEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_correlation_id: str
    captured_ts: str
    route: str
    payload_hash: str
    payload: dict[str, Any]
    was_displaced: bool = False


class BatchedReplayEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tier: str = Field(..., pattern=r"^(life_safety|routine)$")
    entries: list[QueueEntryEnvelope]

    @field_validator("entries")
    @classmethod
    def _max_size(cls, v: list[QueueEntryEnvelope]) -> list[QueueEntryEnvelope]:
        if len(v) == 0:
            raise ValueError("at least 1 entry required")
        if len(v) > _MAX_BATCH:
            raise ValueError(f"batch exceeds {_MAX_BATCH} entries")
        return v


class ReplayResultItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_correlation_id: str
    status: str
    audit_id: str


class BatchedReplayResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[ReplayResultItem]


class _DedupeIndex:
    """Per-process dedupe index keyed by (persona_id, client_correlation_id)."""

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], str] = {}

    def take(self, persona_id: str, ccid: str) -> str | None:
        return self._seen.get((persona_id, ccid))

    def remember(self, persona_id: str, ccid: str, audit_id: str) -> None:
        self._seen[(persona_id, ccid)] = audit_id


_DEDUPE = _DedupeIndex()


def _resolve_repository(request: Request) -> AuditRepository:
    repo = getattr(request.app.state, "audit_repository", None)
    if isinstance(repo, AuditRepository):
        return repo
    new_repo = AuditRepository()
    request.app.state.audit_repository = new_repo
    return new_repo


@router.post("/replay")
async def replay_offline_queue(
    request: Request,
    envelope: BatchedReplayEnvelope,
) -> BatchedReplayResult:
    if len(envelope.entries) > _MAX_BATCH:
        raise HTTPException(status_code=413, detail="batch_too_large")

    claims: dict[str, Any] = getattr(request.state, "claims", None) or {}
    persona_id = request.headers.get("X-Persona-Id") or claims.get("persona_id") or claims.get("personaId") or "unknown"

    repo = _resolve_repository(request)

    results: list[ReplayResultItem] = []
    for entry in envelope.entries:
        existing = _DEDUPE.take(persona_id, entry.client_correlation_id)
        if existing is not None:
            results.append(
                ReplayResultItem(
                    client_correlation_id=entry.client_correlation_id,
                    status="deduped",
                    audit_id=existing,
                )
            )
            continue

        if entry.was_displaced:
            audit_row = await _emit_audit_row(
                repo,
                persona_id=persona_id,
                tier=envelope.tier,
                entry=entry,
                outcome="rejected_displaced_then_lost",
            )
            _DEDUPE.remember(persona_id, entry.client_correlation_id, audit_row["auditId"])
            results.append(
                ReplayResultItem(
                    client_correlation_id=entry.client_correlation_id,
                    status="rejected_displaced_then_lost",
                    audit_id=audit_row["auditId"],
                )
            )
            continue

        audit_row = await _emit_audit_row(
            repo,
            persona_id=persona_id,
            tier=envelope.tier,
            entry=entry,
            outcome="approved",
        )
        _DEDUPE.remember(persona_id, entry.client_correlation_id, audit_row["auditId"])
        results.append(
            ReplayResultItem(
                client_correlation_id=entry.client_correlation_id,
                status="replayed",
                audit_id=audit_row["auditId"],
            )
        )

    return BatchedReplayResult(results=results)


async def _emit_audit_row(
    repo: AuditRepository,
    *,
    persona_id: str,
    tier: str,
    entry: QueueEntryEnvelope,
    outcome: str,
) -> dict[str, Any]:
    correlation_id = entry.client_correlation_id
    body_hash = hashlib.sha256(f"{entry.payload_hash}:{entry.captured_ts}".encode()).hexdigest()

    row = {
        "outcome": outcome,
        "personaId": persona_id,
        "appRole": "field-coordinator",
        "operatorIdentity": persona_id,
        "route": entry.route,
        "requestHash": body_hash,
        "timestamp": entry.captured_ts,
        "tier": tier,
        "replayedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "extensionEnvelope": None,
    }
    try:
        return await repo.append(row, correlation_id=correlation_id)
    except Exception:
        logger.exception("audit append failed for replayed entry %s", correlation_id)
        raise ExtensionEnvelopeError(
            ExtensionErrorCode.SCHEMA_INVALID,
            audit_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
        ) from None
