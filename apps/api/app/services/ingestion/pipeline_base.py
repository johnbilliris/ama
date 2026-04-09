import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import jsonschema
from opentelemetry import trace

from apps.ingestion import telemetry as tel
from packages.domain.src.domain.models.signal import Signal

logger = logging.getLogger(__name__)

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
        self.backoff_until = datetime.now(UTC).replace(
            second=datetime.now(UTC).second
        )
        from datetime import timedelta
        self.backoff_until = datetime.now(UTC) + timedelta(seconds=backoff)
        tel.circuit_breaker_trips.add(1)
        logger.warning(
            "Circuit breaker tripped (trip #%d), backoff %ds",
            self.total_trips, backoff,
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
        blob_storage: Any = None,
        signal_repository: Any = None,
        audit_writer: Any = None,
        incident_association: Any = None,
        schema: dict | None = None,
    ):
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
        self.blob_storage = blob_storage
        self.signal_repository = signal_repository
        self.audit_writer = audit_writer
        self.incident_association = incident_association
        self.schema = schema
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
                await self._process_payload(raw)

            if raw_payloads:
                logger.info(
                    "Pipeline %s cycle complete: %d payloads processed",
                    self.pipeline_id, len(raw_payloads),
                )

    async def _process_payload(self, raw_payload: dict[str, Any]) -> None:
        start_time = time.monotonic()
        correlation_id = str(uuid4())
        data_source_id = self.data_source_ids[0] if self.data_source_ids else "unknown"
        span = trace.get_current_span()
        span.set_attribute("signal.data_source_id", data_source_id)
        span.set_attribute("signal.correlation_id", correlation_id)

        canonical_key = self.compute_canonical_key(raw_payload)
        dedup_hash = hashlib.sha256(canonical_key.encode()).hexdigest()

        if self.dedup_service and await self.dedup_service.check(dedup_hash):
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
            return

        try:
            envelope = self.normalise(raw_payload)
        except Exception as exc:
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
            return

        envelope = self._enrich_envelope(envelope, correlation_id)

        if self.schema:
            try:
                jsonschema.validate(instance=envelope, schema=self.schema)
            except jsonschema.ValidationError as exc:
                self._metrics.record_validation_failure()
                tel.validation_failures_counter.add(1, {"pipeline.id": self.pipeline_id})
                if self.audit_writer:
                    await self.audit_writer.write_entry(
                        signal_id=None,
                        data_source_id=data_source_id,
                        correlation_id=correlation_id,
                        outcome="rejected",
                        validation_errors=[exc.message],
                        dedup_hash=dedup_hash,
                        pipeline_id=self.pipeline_id,
                    )
                return

        if self.incident_association:
            envelope = await self.incident_association.associate(envelope)

        signal_id = f"sig-{uuid4().hex[:12]}"
        raw_blob_uri = None
        if self.blob_storage:
            raw_blob_uri = await self.blob_storage.store_raw_payload(
                data_source_id=data_source_id,
                signal_id=signal_id,
                payload=raw_payload,
            )

        if self.signal_repository:
            signal = Signal(
                signal_id=signal_id,
                incident_id=envelope.get("incidentId"),
                data_source_id=envelope["source"]["dataSourceId"],
                category=envelope["category"],
                occurred_at=datetime.fromisoformat(envelope["occurredAt"].replace("Z", "+00:00")),
                received_at=datetime.fromisoformat(envelope["receivedAt"].replace("Z", "+00:00")),
                jurisdiction_id=envelope.get("jurisdictionId"),
                location=envelope["location"],
                payload=envelope.get("payload", {}),
                confidence_score=envelope["confidenceScore"],
                freshness_score=envelope["freshnessScore"],
                validation_status=envelope["validationStatus"],
                provenance=envelope.get("provenance", {}),
            )
            await self.signal_repository.save(signal)

        if self.dedup_service:
            await self.dedup_service.store(dedup_hash, signal_id)

        latency_ms = (time.monotonic() - start_time) * 1000
        self._metrics.record_ingestion(latency_ms)
        tel.signals_ingested.add(1, {"pipeline.id": self.pipeline_id, "data_source_id": data_source_id})
        tel.ingestion_latency.record(latency_ms, {"pipeline.id": self.pipeline_id})

        if self.audit_writer:
            await self.audit_writer.write_entry(
                signal_id=signal_id,
                data_source_id=data_source_id,
                correlation_id=correlation_id,
                outcome="success",
                raw_payload_blob_uri=raw_blob_uri,
                normalisation_latency_ms=latency_ms,
                dedup_hash=dedup_hash,
                pipeline_id=self.pipeline_id,
            )

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
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.signals_ingested: int = 0
        self.dedup_hits: int = 0
        self.dedup_total: int = 0
        self.poll_successes: int = 0
        self.poll_failures: int = 0
        self.validation_failures: int = 0
        self.latencies: list[float] = []

    def record_poll(self, outcome: str) -> None:
        if outcome == "success":
            self.poll_successes += 1
        elif outcome == "failure":
            self.poll_failures += 1

    def record_dedup_hit(self) -> None:
        self.dedup_hits += 1
        self.dedup_total += 1

    def record_ingestion(self, latency_ms: float) -> None:
        self.signals_ingested += 1
        self.dedup_total += 1
        self.latencies.append(latency_ms)

    def record_validation_failure(self) -> None:
        self.validation_failures += 1

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
        }
