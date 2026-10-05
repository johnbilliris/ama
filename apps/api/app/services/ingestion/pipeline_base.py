import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

from app.services.privacy_classification import classify_payload
from app.services.signal_accepted_workflow import publish_signal_accepted
from opentelemetry import trace

from apps.ingestion import telemetry as tel
from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.models.signal_accepted_event import SignalAcceptedEvent

logger = logging.getLogger(__name__)

IngestionProcessingResult = Signal


@dataclass(frozen=True, slots=True)
class PipelineProcessingResult:
    accepted: bool
    status: str
    reason: str | None = None
    signal_ids: tuple[str, ...] = ()


DerivedSourceKind = Literal["authoritative", "sensor", "iot", "field_report", "social", "community", "derived"]
DerivedTrustTier = Literal[
    "tier_1_authoritative_government",
    "tier_2_verified_institutional",
    "tier_3_operational_sensor",
    "tier_4_field_reports",
    "tier_5_community_volunteer",
    "tier_6_social_unverified",
    "tier_7_derived_computed",
]

_DERIVED_SOURCE_KINDS: dict[str, DerivedSourceKind] = {
    "authoritative": "authoritative",
    "sensor": "sensor",
    "iot": "iot",
    "field_report": "field_report",
    "social": "social",
    "community": "community",
    "derived": "derived",
}
_DERIVED_TRUST_TIERS: dict[str, DerivedTrustTier] = {
    "tier_1_authoritative_government": "tier_1_authoritative_government",
    "tier_2_verified_institutional": "tier_2_verified_institutional",
    "tier_3_operational_sensor": "tier_3_operational_sensor",
    "tier_4_field_reports": "tier_4_field_reports",
    "tier_5_community_volunteer": "tier_5_community_volunteer",
    "tier_6_social_unverified": "tier_6_social_unverified",
    "tier_7_derived_computed": "tier_7_derived_computed",
}


TRUST_TIER_CONFIDENCE: dict[str, float] = {
    "tier_1_authoritative_government": 0.95,
    "tier_2_verified_institutional": 0.85,
    "tier_3_operational_sensor": 0.75,
    "tier_4_field_reports": 0.65,
    "tier_5_community_volunteer": 0.45,
    "tier_6_social_unverified": 0.30,
    "tier_7_derived_computed": 0.50,
}


class CircuitBreakerState:
    def __init__(self, threshold: int = 3, backoff_initial: int = 30, backoff_max: int = 300):
        self.threshold = threshold
        self.backoff_initial = backoff_initial
        self.backoff_max = backoff_max
        self.state: str = "closed"
        self.consecutive_failures: int = 0
        self.last_failure_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.backoff_until: datetime | None = None
        self.total_trips: int = 0

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.last_success_at = datetime.now(UTC)
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker closed after successful half-open poll")

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_at = datetime.now(UTC)
        if self.state == "half_open":
            self._trip()
        elif self.consecutive_failures >= self.threshold:
            self._trip()

    def _trip(self) -> None:
        self.state = "open"
        self.total_trips += 1
        backoff = min(
            self.backoff_initial * (2 ** (self.total_trips - 1)),
            self.backoff_max,
        )
        self.backoff_until = datetime.now(UTC).replace(second=datetime.now(UTC).second)
        from datetime import timedelta

        self.backoff_until = datetime.now(UTC) + timedelta(seconds=backoff)
        tel.circuit_breaker_trips.add(1)
        logger.warning(
            "Circuit breaker tripped (trip #%d), backoff %ds",
            self.total_trips,
            backoff,
        )

    def should_allow_request(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open" and self.backoff_until and datetime.now(UTC) >= self.backoff_until:
            self.state = "half_open"
            logger.info("Circuit breaker half-open, testing connectivity")
            return True
        if self.state == "half_open":
            return True
        return False


class IngestionPipelineBase(ABC):
    def __init__(
        self,
        pipeline_id: str,
        data_source_ids: list[str],
        poll_interval_seconds: int,
        trust_tier: str = "tier_1_authoritative_government",
        expected_update_seconds: int = 60,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_backoff_initial: int = 30,
        circuit_breaker_backoff_max: int = 300,
        dedup_service: Any = None,
        dedup_ttl_seconds: int = 86_400,
        blob_storage: Any = None,
        signal_repository: Any = None,
        audit_writer: Any = None,
        incident_association: Any = None,
        misinformation_detector: Any = None,
        governance_registry: Any = None,
        dead_letter_service: Any = None,
        schema: dict[str, Any] | None = None,
        schema_validator: Any = None,
        scope: str = "live",
        allow_simulation_scope: bool = False,
    ):
        if scope.startswith("sim-") and not allow_simulation_scope:
            raise ValueError("Simulation scope requires allow_simulation_scope=True")
        self.pipeline_id = pipeline_id
        self.data_source_ids = data_source_ids
        self.poll_interval_seconds = poll_interval_seconds
        self.trust_tier = trust_tier
        self.expected_update_seconds = expected_update_seconds
        self.circuit_breaker = CircuitBreakerState(
            circuit_breaker_threshold,
            circuit_breaker_backoff_initial,
            circuit_breaker_backoff_max,
        )
        self.dedup_service = dedup_service
        self.dedup_ttl_seconds = dedup_ttl_seconds
        self.blob_storage = blob_storage
        self.signal_repository = signal_repository
        self.audit_writer = audit_writer
        self.incident_association = incident_association
        self.misinformation_detector = misinformation_detector
        self.governance_registry = governance_registry
        self.dead_letter_service = dead_letter_service
        self.schema = schema
        self.schema_validator = schema_validator
        self.scope = scope
        self._running = False
        self._metrics = PipelineMetrics(pipeline_id)

    @abstractmethod
    async def poll_source(self) -> list[dict[str, Any]]:
        """Fetch raw payloads from the external source. Returns list of raw payload dicts."""

    @abstractmethod
    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Convert a source-specific raw payload into a SignalEnvelope dict."""

    @abstractmethod
    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        """Compute a dedup canonical key from the raw payload."""

    async def run(self) -> None:
        self._running = True
        logger.info("Pipeline %s starting", self.pipeline_id)
        while self._running:
            try:
                await self._poll_cycle()
            except Exception:
                logger.exception("Pipeline %s poll cycle error", self.pipeline_id)
            await asyncio.sleep(self.poll_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        logger.info("Pipeline %s stopping", self.pipeline_id)

    async def _poll_cycle(self) -> None:
        if not self.circuit_breaker.should_allow_request():
            self._metrics.record_poll("circuit_open")
            return

        with tel.tracer.start_as_current_span(
            "ingestion.poll_cycle",
            attributes={"pipeline.id": self.pipeline_id, "pipeline.trust_tier": self.trust_tier},
        ) as span:
            poll_start = time.monotonic()
            try:
                raw_payloads = await self.poll_source()
                self.circuit_breaker.record_success()
                self._metrics.record_poll("success")
                tel.poll_cycles.add(1, {"pipeline.id": self.pipeline_id, "outcome": "success"})
                span.set_attribute("poll.payload_count", len(raw_payloads))
                if raw_payloads:
                    logger.info("Pipeline %s polled %d payloads", self.pipeline_id, len(raw_payloads))
            except Exception as exc:
                self.circuit_breaker.record_failure()
                self._metrics.record_poll("failure")
                tel.poll_errors.add(1, {"pipeline.id": self.pipeline_id})
                span.set_status(trace.StatusCode.ERROR, str(exc))
                span.record_exception(exc)
                logger.warning("Pipeline %s poll failed: %s", self.pipeline_id, exc)
                return
            finally:
                tel.poll_duration.record(
                    (time.monotonic() - poll_start) * 1000,
                    {"pipeline.id": self.pipeline_id},
                )

            for raw in raw_payloads:
                try:
                    await self._process_payload(raw)
                except Exception:
                    logger.exception("Pipeline %s payload processing error", self.pipeline_id)

            if raw_payloads:
                logger.info(
                    "Pipeline %s cycle complete: %d payloads processed",
                    self.pipeline_id,
                    len(raw_payloads),
                )

    async def _process_payload(self, raw_payload: dict[str, Any]) -> PipelineProcessingResult:
        start_time = time.monotonic()
        correlation_id = str(uuid4())
        data_source_id = self.data_source_ids[0] if self.data_source_ids else "unknown"
        span = trace.get_current_span()
        span.set_attribute("signal.data_source_id", data_source_id)
        span.set_attribute("signal.correlation_id", correlation_id)

        if self.governance_registry is not None:
            decision, _source = self.governance_registry.evaluate_source_eligibility(data_source_id)
            if not decision.allowed:
                if self.audit_writer:
                    await self.audit_writer.write_entry(
                        signal_id=None,
                        data_source_id=data_source_id,
                        correlation_id=correlation_id,
                        outcome="blocked",
                        validation_errors=[decision.reason],
                        pipeline_id=self.pipeline_id,
                    )
                return PipelineProcessingResult(False, "blocked", decision.reason)

        canonical_key = self.compute_canonical_key(raw_payload)
        dedup_hash = hashlib.sha256(canonical_key.encode()).hexdigest()
        dedup_claimed = False

        if self.dedup_service:
            if hasattr(self.dedup_service, "try_claim"):
                claimed = await self.dedup_service.try_claim(dedup_hash, self.dedup_ttl_seconds)
                dedup_claimed = claimed
            else:
                claimed = not await self.dedup_service.check(dedup_hash)
            if not claimed:
                self._metrics.record_dedup_hit()
                tel.dedup_hits.add(1, {"pipeline.id": self.pipeline_id})
                logger.debug("Pipeline %s dedup hit: %s", self.pipeline_id, canonical_key[:60])
                if self.audit_writer:
                    await self.audit_writer.write_entry(
                        signal_id=None,
                        data_source_id=data_source_id,
                        correlation_id=correlation_id,
                        outcome="deduplicated",
                        dedup_hash=dedup_hash,
                        pipeline_id=self.pipeline_id,
                    )
                return PipelineProcessingResult(False, "deduplicated", "canonical payload was already processed")

        signal_id = f"sig-{uuid4().hex[:12]}"
        raw_blob_uri = None
        if self.blob_storage:
            raw_blob_uri = await self.blob_storage.store_raw_payload(
                data_source_id=data_source_id,
                signal_id=signal_id,
                payload=raw_payload,
            )

        try:
            envelope = self.normalise(raw_payload)
        except Exception as exc:
            if dedup_claimed and hasattr(self.dedup_service, "release"):
                await self.dedup_service.release(dedup_hash)
            tel.normalisation_errors.add(1, {"pipeline.id": self.pipeline_id})
            logger.warning("Normalisation failed for %s: %s", self.pipeline_id, exc)
            if self.audit_writer:
                await self.audit_writer.write_entry(
                    signal_id=None,
                    data_source_id=data_source_id,
                    correlation_id=correlation_id,
                    outcome="failed",
                    validation_errors=[str(exc)],
                    dedup_hash=dedup_hash,
                    pipeline_id=self.pipeline_id,
                )
            return PipelineProcessingResult(False, "rejected", str(exc))

        envelope = self._enrich_envelope(envelope, correlation_id)

        validator = self.schema_validator
        if validator is not None:
            try:
                validator.validate(envelope)
            except Exception as exc:
                await self._reject_payload(
                    raw_payload=raw_payload,
                    envelope=envelope,
                    data_source_id=data_source_id,
                    signal_id=signal_id,
                    correlation_id=correlation_id,
                    dedup_hash=dedup_hash,
                    dedup_claimed=dedup_claimed,
                    raw_blob_uri=raw_blob_uri,
                    failure_code="schema_validation_failed",
                    error=str(getattr(exc, "message", exc)),
                )
                return PipelineProcessingResult(False, "rejected", str(getattr(exc, "message", exc)))

        if (
            self.misinformation_detector is not None
            and self.signal_repository is not None
            and envelope.get("source", {}).get("kind") in {"social", "community"}
            and hasattr(self.signal_repository, "query_by_jurisdiction")
        ):
            occurred_at = datetime.fromisoformat(envelope["occurredAt"].replace("Z", "+00:00"))
            context_rows = await self.signal_repository.query_by_jurisdiction(
                envelope.get("jurisdictionId") or "national",
                scope=self.scope,
                category=envelope.get("category"),
                since=occurred_at - timedelta(hours=1),
                limit=200,
            )
            context = [self._context_envelope(row) for row in context_rows]
            authoritative = [row for row in context if row.get("source", {}).get("kind") in {"authoritative", "sensor"}]
            recent_social = [row for row in context if row.get("source", {}).get("kind") in {"social", "community"}]
            recent_social.append(envelope)
            result = self.misinformation_detector.detect(envelope, recent_social, authoritative)
            envelope["validationStatus"] = result["validationStatus"]
            envelope["confidenceScore"] = result["confidenceScore"]
            envelope.setdefault("payload", {})["misinformationFlags"] = result["flags"]
            envelope["payload"]["misinformationTier1Result"] = {
                "status": result["validationStatus"],
                "confidenceScore": result["confidenceScore"],
                "flags": result["flags"],
            }
            notes = envelope.setdefault("provenance", {}).get("validationNotes")
            tier1_note = f"tier1_misinformation flags={','.join(result['flags']) or 'none'}"
            envelope["provenance"]["validationNotes"] = f"{notes}; {tier1_note}" if notes else tier1_note

        envelopes = [envelope]
        if self.incident_association:
            if hasattr(self.incident_association, "associate_multi"):
                envelopes = await self.incident_association.associate_multi(envelope, scope=self.scope)
            else:
                envelopes = [await self.incident_association.associate(envelope, scope=self.scope)]

        if not self.signal_repository:
            self._metrics.record_persistence_failure()
            if dedup_claimed and hasattr(self.dedup_service, "release"):
                await self.dedup_service.release(dedup_hash)
            tel.persistence_failures.add(1, {"pipeline.id": self.pipeline_id})
            if self.audit_writer:
                await self.audit_writer.write_entry(
                    signal_id=None,
                    data_source_id=data_source_id,
                    correlation_id=correlation_id,
                    outcome="degraded",
                    validation_errors=["signal repository unavailable"],
                    dedup_hash=dedup_hash,
                    pipeline_id=self.pipeline_id,
                )
            return PipelineProcessingResult(False, "degraded", "signal repository unavailable")

        if not envelopes:
            if dedup_claimed and hasattr(self.dedup_service, "release"):
                await self.dedup_service.release(dedup_hash)
            return PipelineProcessingResult(False, "rejected", "incident association produced no signal envelopes")

        persisted_signals: list[tuple[Signal, dict[str, Any]]] = []
        for index, associated_envelope in enumerate(envelopes):
            associated_signal_id = signal_id if index == 0 else f"sig-{uuid4().hex[:12]}"
            try:
                received_at = datetime.fromisoformat(associated_envelope["receivedAt"].replace("Z", "+00:00"))
                classification, pii_fields, retention_until = classify_payload(
                    associated_envelope.get("payload", {}),
                    received_at,
                )
                signal = Signal(
                    signal_id=associated_signal_id,
                    incident_id=associated_envelope.get("incidentId"),
                    data_source_id=associated_envelope["source"]["dataSourceId"],
                    category=associated_envelope["category"],
                    occurred_at=datetime.fromisoformat(associated_envelope["occurredAt"].replace("Z", "+00:00")),
                    received_at=received_at,
                    jurisdiction_id=associated_envelope.get("jurisdictionId"),
                    location=associated_envelope["location"],
                    payload=associated_envelope.get("payload", {}),
                    classification=classification,
                    pii_fields=pii_fields,
                    retention_until=retention_until,
                    confidence_score=associated_envelope["confidenceScore"],
                    freshness_score=associated_envelope["freshnessScore"],
                    validation_status=associated_envelope["validationStatus"],
                    provenance=associated_envelope.get("provenance", {}),
                )
                await self.signal_repository.save(signal, scope=self.scope)
                persisted_signals.append((signal, associated_envelope))
            except (ValueError, TypeError, KeyError) as exc:
                await self._reject_payload(
                    raw_payload=raw_payload,
                    envelope=associated_envelope,
                    data_source_id=data_source_id,
                    signal_id=associated_signal_id,
                    correlation_id=correlation_id,
                    dedup_hash=dedup_hash,
                    dedup_claimed=dedup_claimed,
                    raw_blob_uri=raw_blob_uri,
                    failure_code="payload_model_validation_failed",
                    error=str(exc),
                )
                return PipelineProcessingResult(False, "rejected", str(exc))
            except Exception as exc:
                self._metrics.record_persistence_failure()
                if dedup_claimed and hasattr(self.dedup_service, "release"):
                    await self.dedup_service.release(dedup_hash)
                tel.persistence_failures.add(1, {"pipeline.id": self.pipeline_id})
                if self.audit_writer:
                    await self.audit_writer.write_entry(
                        signal_id=None,
                        data_source_id=data_source_id,
                        correlation_id=correlation_id,
                        outcome="degraded",
                        validation_errors=[str(exc)],
                        dedup_hash=dedup_hash,
                        pipeline_id=self.pipeline_id,
                    )
                return PipelineProcessingResult(False, "degraded", str(exc))

        if not persisted_signals:
            return PipelineProcessingResult(False, "rejected", "no signal was persisted")

        if self.dedup_service:
            if hasattr(self.dedup_service, "commit"):
                await self.dedup_service.commit(dedup_hash, persisted_signals[0][0].signal_id, self.dedup_ttl_seconds)
            else:
                await self.dedup_service.store(
                    dedup_hash,
                    persisted_signals[0][0].signal_id,
                    self.dedup_ttl_seconds,
                )

        latency_ms = (time.monotonic() - start_time) * 1000
        for signal, associated_envelope in persisted_signals:
            self._metrics.record_ingestion(latency_ms)
            tel.signals_ingested.add(1, {"pipeline.id": self.pipeline_id, "data_source_id": data_source_id})
            tel.ingestion_latency.record(latency_ms, {"pipeline.id": self.pipeline_id})

            derived_kind = _DERIVED_SOURCE_KINDS.get(
                str(signal.provenance.get("derivedSourceKind", associated_envelope["source"]["kind"])),
                "derived",
            )
            derived_trust = _DERIVED_TRUST_TIERS.get(
                str(signal.provenance.get("derivedTrustTier", self.trust_tier)),
                "tier_7_derived_computed",
            )
            evaluated_confidence = float(signal.provenance.get("evaluatedConfidenceScore", signal.confidence_score))
            await publish_signal_accepted(
                SignalAcceptedEvent(
                    tenant_id=self.scope,
                    scope=self.scope,
                    signal_id=signal.signal_id,
                    data_source_id=signal.data_source_id,
                    correlation_id=correlation_id,
                    incident_id=signal.incident_id,
                    derived_source_kind=derived_kind,
                    derived_trust_tier=derived_trust,
                    validation_status=signal.validation_status,
                    evaluated_confidence_score=evaluated_confidence,
                )
            )
            if self.audit_writer:
                await self.audit_writer.write_entry(
                    signal_id=signal.signal_id,
                    data_source_id=data_source_id,
                    correlation_id=correlation_id,
                    outcome="success",
                    validation_status=signal.validation_status,
                    raw_payload_blob_uri=raw_blob_uri,
                    raw_archival_enabled=bool(raw_blob_uri),
                    normalisation_latency_ms=latency_ms,
                    dedup_hash=dedup_hash,
                    pipeline_id=self.pipeline_id,
                )

        return PipelineProcessingResult(
            accepted=True,
            status="accepted",
            signal_ids=tuple(signal.signal_id for signal, _ in persisted_signals),
        )

    async def _reject_payload(
        self,
        *,
        raw_payload: dict[str, Any],
        envelope: dict[str, Any],
        data_source_id: str,
        signal_id: str,
        correlation_id: str,
        dedup_hash: str,
        dedup_claimed: bool,
        raw_blob_uri: str | None,
        failure_code: str,
        error: str,
    ) -> None:
        self._metrics.record_validation_failure()
        tel.validation_failures_counter.add(1, {"pipeline.id": self.pipeline_id})
        if self.audit_writer:
            await self.audit_writer.write_entry(
                signal_id=None,
                data_source_id=data_source_id,
                correlation_id=correlation_id,
                outcome="rejected",
                validation_errors=[error],
                raw_payload_blob_uri=raw_blob_uri,
                dedup_hash=dedup_hash,
                pipeline_id=self.pipeline_id,
            )
        if self.dead_letter_service:
            self.dead_letter_service.create_entry(
                entry_type="ingestion_failure",
                correlation_id=correlation_id,
                original_payload={
                    "raw_payload": raw_payload,
                    "raw_payload_blob_uri": raw_blob_uri,
                },
                failure_reason=error,
                failure_code=failure_code,
                source_service=self.pipeline_id,
                target_service="ingestion_pipeline",
                tenant_scope_key=self.scope,
                incident_id=envelope.get("incidentId"),
            )
        if dedup_claimed and hasattr(self.dedup_service, "release"):
            await self.dedup_service.release(dedup_hash)

    @staticmethod
    def _context_envelope(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            return dict(row)
        return {
            "signalId": getattr(row, "signal_id", None),
            "category": getattr(row, "category", None),
            "occurredAt": getattr(row, "occurred_at", None),
            "receivedAt": getattr(row, "received_at", None),
            "jurisdictionId": getattr(row, "jurisdiction_id", None),
            "location": getattr(row, "location", {}),
            "payload": getattr(row, "payload", {}),
            "source": {
                "dataSourceId": getattr(row, "data_source_id", "unknown"),
                "kind": getattr(row, "provenance", {}).get("derivedSourceKind", "unknown"),
            },
            "confidenceScore": getattr(row, "confidence_score", 0.0),
            "freshnessScore": getattr(row, "freshness_score", 0.0),
            "validationStatus": getattr(row, "validation_status", "pending"),
            "provenance": getattr(row, "provenance", {}),
        }

    def _enrich_envelope(self, envelope: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        if "receivedAt" not in envelope:
            envelope["receivedAt"] = now

        base_confidence = TRUST_TIER_CONFIDENCE.get(self.trust_tier, 0.5)
        if "confidenceScore" not in envelope:
            envelope["confidenceScore"] = base_confidence

        if "freshnessScore" not in envelope:
            envelope["freshnessScore"] = self._compute_freshness(envelope)

        provenance = envelope.get("provenance", {})
        provenance.setdefault("collector", self.pipeline_id)
        envelope["provenance"] = provenance

        return envelope

    def _compute_freshness(self, envelope: dict[str, Any]) -> float:
        try:
            occurred = datetime.fromisoformat(envelope["occurredAt"].replace("Z", "+00:00"))
            received = datetime.fromisoformat(envelope["receivedAt"].replace("Z", "+00:00"))
            delta_seconds = (received - occurred).total_seconds()
            if delta_seconds <= self.expected_update_seconds:
                return 0.95
            ratio = delta_seconds / self.expected_update_seconds
            if ratio >= 3.0:
                return max(0.1, 0.3 - (ratio - 3.0) * 0.05)
            return max(0.3, 1.0 - (ratio - 1.0) * 0.35)
        except (KeyError, ValueError):
            return 0.5


class PipelineMetrics:
    MAX_LATENCY_SAMPLES = 1000
    ROLLING_DEDUP_SECONDS = 3600
    ROLLING_SIGNALS_SECONDS = 3600

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.signals_ingested: int = 0
        self.dedup_hits: int = 0
        self.dedup_total: int = 0
        self.poll_successes: int = 0
        self.poll_failures: int = 0
        self.validation_failures: int = 0
        self.persistence_failures: int = 0
        self.latencies: deque[float] = deque(maxlen=self.MAX_LATENCY_SAMPLES)
        self._dedup_events: deque[tuple[datetime, bool]] = deque()
        self._signal_events: deque[datetime] = deque()

    def record_poll(self, outcome: str) -> None:
        if outcome == "success":
            self.poll_successes += 1
        elif outcome == "failure":
            self.poll_failures += 1

    def record_dedup_hit(self) -> None:
        self.dedup_hits += 1
        self.dedup_total += 1
        now = datetime.now(UTC)
        self._dedup_events.appendleft((now, True))
        self._prune_events(now)

    def record_ingestion(self, latency_ms: float) -> None:
        self.signals_ingested += 1
        self.dedup_total += 1
        self.latencies.append(latency_ms)
        now = datetime.now(UTC)
        self._dedup_events.appendleft((now, False))
        self._signal_events.appendleft(now)
        self._prune_events(now)

    def _prune_events(self, now: datetime) -> None:
        dedup_cutoff = now - timedelta(seconds=self.ROLLING_DEDUP_SECONDS)
        signal_cutoff = now - timedelta(seconds=self.ROLLING_SIGNALS_SECONDS)
        self._dedup_events = deque(
            (event_time, hit) for event_time, hit in self._dedup_events if event_time >= dedup_cutoff
        )
        self._signal_events = deque(event_time for event_time in self._signal_events if event_time >= signal_cutoff)

    def dedup_window_counts(self, *, now: datetime | None = None) -> dict[str, int | float]:
        now = now or datetime.now(UTC)
        self._prune_events(now)
        total = len(self._dedup_events)
        hits = sum(1 for _, hit in self._dedup_events if hit)
        return {"total": total, "hits": hits, "rate": hits / total if total else 0.0}

    def record_validation_failure(self) -> None:
        self.validation_failures += 1

    def record_persistence_failure(self) -> None:
        self.persistence_failures += 1

    @property
    def dedup_hit_rate(self) -> float:
        return self.dedup_hits / self.dedup_total if self.dedup_total > 0 else 0.0

    @property
    def latency_p95(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipelineId": self.pipeline_id,
            "signalsIngested": self.signals_ingested,
            "dedupHitRatePercent": round(self.dedup_hit_rate * 100, 1),
            "pollSuccesses": self.poll_successes,
            "pollFailures": self.poll_failures,
            "normalisationLatencyP95Ms": round(self.latency_p95, 1),
            "validationFailures": self.validation_failures,
            "persistenceFailures": self.persistence_failures,
        }
