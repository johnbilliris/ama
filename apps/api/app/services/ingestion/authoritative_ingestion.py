from datetime import datetime
from uuid import uuid4

from app.services.state_store import INCIDENTS, SIGNALS
from app.validators.signal_envelope import SignalEnvelope
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.signal import Signal


class AuthoritativeIngestionService:
    def ingest(self, envelope: SignalEnvelope) -> Signal:
        incident_id = envelope.incidentId or "incident-default"
        if incident_id not in INCIDENTS:
            INCIDENTS[incident_id] = Incident(
                incident_id=incident_id,
                title="Imported Incident",
                incident_type="flood",
                status="active",
                severity="warning",
                affected_jurisdiction_ids=[envelope.jurisdictionId or "nsw"],
            )

        signal = Signal(
            signal_id=f"sig-{uuid4().hex[:8]}",
            incident_id=incident_id,
            data_source_id=envelope.source.dataSourceId,
            category=envelope.category,
            occurred_at=datetime.fromisoformat(envelope.occurredAt.replace("Z", "+00:00")),
            received_at=datetime.fromisoformat(envelope.receivedAt.replace("Z", "+00:00")),
            jurisdiction_id=envelope.jurisdictionId,
            location=envelope.location,
            payload=envelope.payload,
            confidence_score=envelope.confidenceScore,
            freshness_score=envelope.freshnessScore,
            validation_status=envelope.validationStatus,
            provenance=envelope.provenance,
        )
        SIGNALS[signal.signal_id] = signal
        return signal
