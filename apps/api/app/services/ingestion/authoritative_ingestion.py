from uuid import uuid4

from app.api.dependencies.simulation_composition import get_resource_governor
from app.repositories.signal_repository import SignalRepository
from app.services.audit_service import AuditService
from app.services.governance_registry import GovernanceRegistryService
from app.services.operational_store import OperationalStore
from app.services.privacy_classification import classify_payload
from app.services.provenance_scoring_service import ProvenanceScoringService
from app.validators.signal_envelope import SignalEnvelope

from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.signal import Signal


class AuthoritativeIngestionService:
    def __init__(
        self,
        registry: GovernanceRegistryService | None = None,
        signal_repository: SignalRepository | None = None,
    ) -> None:
        self._registry = registry or GovernanceRegistryService()
        self._scoring = ProvenanceScoringService()
        self._signal_repository = signal_repository or SignalRepository(write_guard=get_resource_governor())

    def ingest(self, envelope: SignalEnvelope, source: DataSource | None = None) -> Signal:
        store = OperationalStore.current()
        resolved_source = source or self._registry.get_source(envelope.source.dataSourceId)
        if resolved_source.kind != envelope.source.kind:
            raise ValueError("source.kind must match registered data source kind")
        if resolved_source.kind in {"community", "social"} and envelope.validationStatus == "validated":
            raise ValueError("community/social sources cannot self-assert validated status")

        allow_unassigned = bool(envelope.payload.get("allowUnassignedIncident"))
        if envelope.incidentId:
            incident_id = envelope.incidentId
        elif allow_unassigned:
            incident_id = f"unassigned-{envelope.jurisdictionId or 'national'}"
        else:
            raise ValueError("incidentId is required unless payload.allowUnassignedIncident is true")

        evaluated_confidence = self._scoring.score(
            resolved_source.kind,
            envelope.freshnessScore,
            envelope.confidenceScore,
        )
        classification, pii_fields, retention_until = classify_payload(
            envelope.payload,
            envelope.receivedAt,
        )

        incident_to_create: Incident | None = None
        if not store.incidents.contains(incident_id):
            incident_to_create = Incident(
                incident_id=incident_id,
                title="Imported Incident",
                incident_type="other",
                status="active",
                severity="warning",
                affected_jurisdiction_ids=[envelope.jurisdictionId or "unknown"],
            )

        signal = Signal(
            signal_id=f"sig-{uuid4().hex[:8]}",
            incident_id=incident_id,
            data_source_id=envelope.source.dataSourceId,
            category=envelope.category,
            occurred_at=envelope.occurredAt,
            received_at=envelope.receivedAt,
            jurisdiction_id=envelope.jurisdictionId,
            location=envelope.location.model_dump(mode="json"),
            payload=envelope.payload,
            classification=classification,
            pii_fields=pii_fields,
            retention_until=retention_until,
            confidence_score=evaluated_confidence,
            freshness_score=envelope.freshnessScore,
            validation_status=envelope.validationStatus,
            provenance={
                **envelope.provenance.model_dump(mode="json"),
                "derivedSourceKind": resolved_source.kind,
                "derivedTrustTier": resolved_source.trust_tier,
                "assertedConfidenceScore": envelope.confidenceScore,
                "evaluatedConfidenceScore": evaluated_confidence,
                "assertedValidationStatus": envelope.validationStatus,
                "correlationId": f"ingest-{uuid4().hex}",
            },
        )

        AuditService().record_event(
            incident_id=incident_id,
            event_type="ingestion",
            summary=f"Accepted signal {signal.signal_id} from {signal.data_source_id}",
            actor="authoritative-ingestion",
            tenant_id=store.tenant_id,
            mode="live" if store.tenant_id == "live" else "rehearsal",
            correlation_id=signal.signal_id,
            outcome="accepted",
            route="/api/signals",
            supporting_signal_ids=[signal.signal_id],
            rationale="Signal normalized and accepted",
            payload={
                "signalId": signal.signal_id,
                "dataSourceId": signal.data_source_id,
                "validationStatus": signal.validation_status,
                "derivedTrustTier": resolved_source.trust_tier,
                "classification": signal.classification,
                "piiFields": signal.pii_fields,
                "retentionUntil": signal.retention_until.isoformat(),
            },
        )

        if incident_to_create is not None:
            store.incidents.put(incident_id, incident_to_create)
        store.signals.put(signal.signal_id, signal)
        return signal
