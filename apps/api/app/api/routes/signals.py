from datetime import UTC, datetime
from uuid import uuid4

from app.services.governance_registry import GovernanceRegistryService
from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.services.ingestion.community_ingestion import CommunityIngestionService
from app.services.ingestion.iot_ingestion import IoTIngestionService
from app.services.operational_store import OperationalStore
from app.services.signal_accepted_workflow import publish_signal_accepted
from app.validators.signal_envelope import SignalEnvelope
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent

router = APIRouter(prefix="/signals", tags=["signals"])
_governance_registry = GovernanceRegistryService()


class SignalPage(BaseModel):
    items: list[dict]
    total: int


@router.post("", status_code=202)
async def ingest_signal(envelope: SignalEnvelope) -> dict[str, str]:
    source = _governance_registry.get_source(envelope.source.dataSourceId)
    source_kind = source.kind
    if source_kind != envelope.source.kind:
        raise HTTPException(status_code=403, detail="source.kind must match registered data source kind")
    if source_kind in {"community", "social"} and envelope.validationStatus == "validated":
        raise HTTPException(status_code=403, detail="community/social sources cannot self-assert validated status")

    service_map = {
        "authoritative": AuthoritativeIngestionService(),
        "iot": IoTIngestionService(),
        "sensor": IoTIngestionService(),
        "community": CommunityIngestionService(),
        "social": CommunityIngestionService(),
        "field_report": AuthoritativeIngestionService(),
    }
    service = service_map.get(source_kind, CommunityIngestionService())
    try:
        signal = service.ingest(envelope, source=source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    derived_source_kind = str(signal.provenance.get("derivedSourceKind", source.kind))
    derived_trust_tier = str(signal.provenance.get("derivedTrustTier", source.trust_tier))
    evaluated_confidence = float(signal.provenance.get("evaluatedConfidenceScore", signal.confidence_score))
    correlation_id = str(signal.provenance.get("correlationId", f"ingest-{uuid4().hex}"))

    await publish_signal_accepted(
        SignalAcceptedEvent(
            tenant_id=OperationalStore.current().tenant_id,
            scope=OperationalStore.current().tenant_id,
            signal_id=signal.signal_id,
            data_source_id=signal.data_source_id,
            correlation_id=correlation_id,
            incident_id=signal.incident_id,
            derived_source_kind=derived_source_kind,
            derived_trust_tier=derived_trust_tier,
            validation_status=signal.validation_status,
            evaluated_confidence_score=evaluated_confidence,
        )
    )
    return {"signalId": signal.signal_id, "status": "accepted"}


@router.get("")
async def list_signals(
    incidentId: str | None = None,
    jurisdictionId: str | None = None,
    category: str | None = None,
    dataSourceId: str | None = None,
    since: str | None = None,
    validationStatus: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> SignalPage:
    now = datetime.now(tz=UTC)
    results = [
        s
        for s in OperationalStore.current().signals.values()
        if getattr(s, "retention_until", None) is None or s.retention_until >= now
    ]

    if incidentId:
        results = [s for s in results if s.incident_id == incidentId]
    if jurisdictionId:
        results = [s for s in results if s.jurisdiction_id == jurisdictionId]
    if category:
        results = [s for s in results if s.category == category]
    if dataSourceId:
        results = [s for s in results if s.data_source_id == dataSourceId]
    if validationStatus:
        results = [s for s in results if s.validation_status == validationStatus]
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            results = [s for s in results if s.occurred_at >= since_dt]
        except ValueError:
            pass

    results.sort(key=lambda s: s.occurred_at, reverse=True)
    total = len(results)
    paged = results[offset : offset + limit]
    return SignalPage(items=[s.model_dump(mode="json") for s in paged], total=total)
