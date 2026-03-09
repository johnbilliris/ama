from fastapi import APIRouter

from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.services.ingestion.community_ingestion import CommunityIngestionService
from app.services.ingestion.iot_ingestion import IoTIngestionService
from app.services.state_store import SIGNALS
from app.validators.signal_envelope import SignalEnvelope

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("")
async def ingest_signal(envelope: SignalEnvelope) -> dict[str, str]:
    service_map = {
        "authoritative": AuthoritativeIngestionService(),
        "iot": IoTIngestionService(),
        "sensor": IoTIngestionService(),
        "community": CommunityIngestionService(),
        "social": CommunityIngestionService(),
    }
    signal = service_map.get(envelope.source.kind, CommunityIngestionService()).ingest(envelope)
    return {"signalId": signal.signal_id, "status": "accepted"}


@router.get("")
async def list_signals(incidentId: str | None = None) -> list[dict[str, object]]:
    return [
        signal.model_dump(mode="json")
        for signal in SIGNALS.values()
        if incidentId is None or signal.incident_id == incidentId
    ]
