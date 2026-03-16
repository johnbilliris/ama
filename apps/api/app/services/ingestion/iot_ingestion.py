from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.validators.signal_envelope import SignalEnvelope

from packages.domain.src.domain.models.signal import Signal


class IoTIngestionService:
    def ingest(self, envelope: SignalEnvelope) -> Signal:
        return AuthoritativeIngestionService().ingest(envelope)
