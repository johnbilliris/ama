from datetime import datetime

from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.services.ingestion.community_ingestion import CommunityIngestionService
from app.services.ingestion.iot_ingestion import IoTIngestionService
from app.services.state_store import SIGNALS
from app.validators.signal_envelope import SignalEnvelope
from fastapi import APIRouter

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("")
async def ingest_signal(envelope: SignalEnvelope) -> dict[str, str]:
    service_map = {
        "authoritative": AuthoritativeIngestionService(),
        "iot": IoTIngestionService(),
        "sensor": IoTIngestionService(),
        "community": CommunityIngestionService(),
        "social": CommunityIngestionService(),
        "field_report": AuthoritativeIngestionService(),
    }
    service = service_map.get(envelope.source.kind, CommunityIngestionService())
    signal = service.ingest(envelope)
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
) -> dict:
    results = list(SIGNALS.values())

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
    return {
        "items": [s.model_dump(mode="json") for s in paged],
        "total": total,
    }
