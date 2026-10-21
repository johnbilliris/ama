import json

import pytest
from app.services.governance_eligibility import EligibilityDecision
from jsonschema import Draft202012Validator, FormatChecker

from apps.api.app.services.ingestion.audit_writer import AuditWriter
from apps.api.app.services.ingestion.misinformation_detector import MisinformationDetector
from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase


def _schema_validator() -> Draft202012Validator:
    return Draft202012Validator(
        schema={
            "type": "object",
            "required": [
                "source",
                "category",
                "occurredAt",
                "receivedAt",
                "location",
                "payload",
                "confidenceScore",
                "freshnessScore",
                "validationStatus",
                "provenance",
            ],
            "properties": {
                "source": {
                    "type": "object",
                    "required": ["dataSourceId", "name", "kind"],
                    "properties": {
                        "dataSourceId": {"type": "string"},
                        "name": {"type": "string"},
                        "kind": {"type": "string"},
                    },
                },
                "category": {"type": "string"},
                "occurredAt": {"type": "string", "format": "date-time"},
                "receivedAt": {"type": "string", "format": "date-time"},
                "jurisdictionId": {"type": "string"},
                "incidentId": {"type": "string"},
                "location": {"type": "object"},
                "payload": {"type": "object"},
                "confidenceScore": {"type": "number"},
                "freshnessScore": {"type": "number"},
                "validationStatus": {"type": "string"},
                "provenance": {
                    "type": "object",
                    "required": ["sourceUri"],
                    "properties": {
                        "sourceUri": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
        format_checker=FormatChecker(),
    )


class MockPipeline(IngestionPipelineBase):
    def __init__(self, payloads=None, fail_on_poll=False, **kwargs):
        kwargs.setdefault("schema_validator", _schema_validator())
        super().__init__(
            pipeline_id="mock-pipeline",
            data_source_ids=["mock-source"],
            poll_interval_seconds=1,
            **kwargs,
        )
        self._payloads = payloads or []
        self._fail_on_poll = fail_on_poll
        self.processed: list = []

    async def poll_source(self):
        if self._fail_on_poll:
            raise ConnectionError("Source unavailable")
        return self._payloads

    def normalise(self, raw_payload):
        return {
            "source": {"dataSourceId": "mock-source", "name": "Mock", "kind": "authoritative"},
            "category": "weather",
            "occurredAt": "2026-03-25T10:00:00Z",
            "receivedAt": "2026-03-25T10:00:01Z",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
            "payload": raw_payload,
            "confidenceScore": 0.95,
            "freshnessScore": 0.9,
            "validationStatus": "validated",
            "provenance": {"collectionMethod": "api_pull", "sourceUri": "https://example.com"},
        }

    def compute_canonical_key(self, raw_payload):
        return f"mock:{raw_payload.get('id', 'unknown')}"


class TestIngestionPipelineIntegration:
    def test_simulation_scope_requires_explicit_authorization(self):
        with pytest.raises(ValueError, match="allow_simulation_scope"):
            MockPipeline(scope="sim-forged")

        pipeline = MockPipeline(scope="sim-authorized", allow_simulation_scope=True)
        assert pipeline.scope == "sim-authorized"

    @pytest.mark.asyncio
    async def test_full_pipeline_lifecycle_with_mocked_source(self):
        payloads = [{"id": "1", "value": "test"}]
        pipeline = MockPipeline(payloads=payloads, signal_repository=_RecordingRepository(fail=False))
        await pipeline._poll_cycle()
        assert pipeline._metrics.poll_successes == 1
        assert pipeline._metrics.signals_ingested == 1
        assert pipeline._metrics.persistence_failures == 0

    @pytest.mark.asyncio
    async def test_success_audit_without_raw_archive_is_valid(self):
        audit = AuditWriter()
        pipeline = MockPipeline(
            payloads=[{"id": "audit-without-raw-archive"}],
            audit_writer=audit,
            signal_repository=_RecordingRepository(fail=False),
        )

        await pipeline._poll_cycle()

        assert len(audit.entries) == 1
        entry = json.loads(audit.entries[0])
        assert entry["outcome"] == "success"
        assert entry["validation_status"] == "validated"
        assert entry["raw_payload_blob_uri"] is None
        assert entry["raw_archival_enabled"] is False

    @pytest.mark.asyncio
    async def test_success_audit_with_blank_raw_archive_is_valid(self):
        class _BlankRawStore:
            async def store_raw_payload(self, **kwargs):  # type: ignore[no-untyped-def]
                return ""

        audit = AuditWriter()
        pipeline = MockPipeline(
            payloads=[{"id": "audit-with-blank-raw-archive"}],
            audit_writer=audit,
            blob_storage=_BlankRawStore(),
            signal_repository=_RecordingRepository(fail=False),
        )

        await pipeline._poll_cycle()

        assert len(audit.entries) == 1
        entry = json.loads(audit.entries[0])
        assert entry["outcome"] == "success"
        assert entry["raw_payload_blob_uri"] == ""
        assert entry["raw_archival_enabled"] is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_after_failures(self):
        pipeline = MockPipeline(fail_on_poll=True)
        for _ in range(3):
            await pipeline._poll_cycle()
        assert pipeline.circuit_breaker.state == "open"
        assert pipeline._metrics.poll_failures == 3

    @pytest.mark.asyncio
    async def test_dedup_skips_duplicate_payloads(self):
        from apps.api.app.services.ingestion.dedup_service import DedupService

        dedup = DedupService()
        payloads = [{"id": "dup-1"}, {"id": "dup-1"}]
        pipeline = MockPipeline(
            payloads=payloads,
            dedup_service=dedup,
            signal_repository=_RecordingRepository(fail=False),
        )
        await pipeline._poll_cycle()
        assert pipeline._metrics.signals_ingested == 1
        assert pipeline._metrics.dedup_hits == 1

    @pytest.mark.asyncio
    async def test_successful_poll_records_metrics(self):
        pipeline = MockPipeline(payloads=[{"id": "a"}])
        await pipeline._poll_cycle()
        assert pipeline._metrics.poll_successes == 1


class _RecordingRepository:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.saved: list[tuple[str, str]] = []

    async def save(self, signal, scope: str = "live"):  # type: ignore[no-untyped-def]
        if self.fail:
            raise RuntimeError("persist failed")
        self.saved.append((scope, signal.signal_id))


class _MisinformationContextRepository:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.saved: list[tuple[str, object]] = []
        self.query_scopes: list[str] = []

    async def save(self, signal, scope: str = "live"):  # type: ignore[no-untyped-def]
        self.saved.append((scope, signal))

    async def query_by_jurisdiction(
        self,
        jurisdiction_id: str,
        *,
        scope: str,
        category: str | None = None,
        since=None,
        limit: int = 200,
    ):
        self.query_scopes.append(scope)
        filtered: list[dict] = []
        for row in self.rows:
            if str(row.get("scope", "")) != scope:
                continue
            if category and str(row.get("category", "")) != category:
                continue
            if str(row.get("jurisdictionId", "national")) != jurisdiction_id:
                continue
            if since is not None:
                occurred = row.get("occurredAt")
                if not isinstance(occurred, str):
                    continue
                from datetime import datetime

                try:
                    occurred_dt = datetime.fromisoformat(occurred.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if occurred_dt < since:
                    continue
            filtered.append(row)
            if len(filtered) >= limit:
                break
        return filtered


class _RecordingAuditWriter:
    def __init__(self) -> None:
        self.outcomes: list[str] = []
        self.entries: list[dict[str, object]] = []

    async def write_entry(self, **kwargs):  # type: ignore[no-untyped-def]
        self.outcomes.append(str(kwargs.get("outcome", "")))
        self.entries.append(kwargs)


class _RecordingDedupService:
    def __init__(self) -> None:
        self.claimed: set[str] = set()
        self.committed: set[str] = set()
        self.stored: list[str] = []
        self.claim_ttls: list[int] = []
        self.commit_ttls: list[int] = []

    async def try_claim(self, key: str, ttl_seconds: int | None = None) -> bool:
        if ttl_seconds is not None:
            self.claim_ttls.append(ttl_seconds)
        if key in self.claimed or key in self.committed:
            return False
        self.claimed.add(key)
        return True

    async def commit(self, key: str, signal_id: str, ttl_seconds: int | None = None) -> None:
        if ttl_seconds is not None:
            self.commit_ttls.append(ttl_seconds)
        self.claimed.discard(key)
        self.committed.add(key)
        self.stored.append(signal_id)

    async def release(self, key: str) -> None:
        self.claimed.discard(key)


class _Aud005Pipeline(MockPipeline):
    def normalise(self, raw_payload):
        if raw_payload.get("malformed"):
            raise ValueError("malformed payload")
        return super().normalise(raw_payload)


class _SocialPipeline(MockPipeline):
    def normalise(self, raw_payload):
        envelope = super().normalise(raw_payload)
        occurred_at = raw_payload.get("occurredAt")
        if isinstance(occurred_at, str) and occurred_at.strip():
            envelope["occurredAt"] = occurred_at
            envelope["receivedAt"] = occurred_at
        envelope["source"] = {
            "dataSourceId": "mock-source",
            "name": "Twitter",
            "kind": "social",
        }
        envelope["provenance"]["trustTier"] = "tier_6_social_unverified"
        envelope["category"] = "fire"
        envelope["payload"] = {
            "text": raw_payload.get("text", "fire smoke at ridge"),
            "topic": raw_payload.get("topic", "bushfire"),
            "accountId": raw_payload.get("accountId", "acct-current"),
        }
        envelope["jurisdictionId"] = raw_payload.get("jurisdictionId", "nsw")
        envelope["signalId"] = raw_payload.get("signalId", "sig-social-current")
        return envelope


class _StaticEligibilityRegistry:
    def __init__(self, allowed: bool, reason: str) -> None:
        self._decision = EligibilityDecision(allowed=allowed, reason=reason)

    def evaluate_source_eligibility(self, _data_source_id: str):  # type: ignore[no-untyped-def]
        return self._decision, None


@pytest.mark.asyncio
async def test_aud005_no_persistence_means_no_success_and_no_dedup_store() -> None:
    dedup = _RecordingDedupService()
    audit = _RecordingAuditWriter()
    pipeline = _Aud005Pipeline(
        payloads=[{"id": "one"}],
        dedup_service=dedup,
        audit_writer=audit,
        signal_repository=None,
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 0
    assert pipeline._metrics.persistence_failures == 1
    assert dedup.stored == []
    assert audit.outcomes == ["degraded"]


@pytest.mark.asyncio
async def test_aud005_one_malformed_payload_does_not_block_valid_siblings() -> None:
    dedup = _RecordingDedupService()
    audit = _RecordingAuditWriter()
    repo = _RecordingRepository(fail=False)
    pipeline = _Aud005Pipeline(
        payloads=[{"id": "ok-1"}, {"id": "bad-1", "malformed": True}, {"id": "ok-2"}],
        dedup_service=dedup,
        audit_writer=audit,
        signal_repository=repo,
        scope="sim-nsw",
        allow_simulation_scope=True,
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 2
    assert pipeline._metrics.persistence_failures == 0
    assert len(repo.saved) == 2
    assert all(scope == "sim-nsw" for scope, _ in repo.saved)
    assert len(dedup.stored) == 2
    assert audit.outcomes.count("success") == 2
    assert "failed" in audit.outcomes


@pytest.mark.asyncio
async def test_aud005_failed_persistence_records_degraded_without_success_side_effects() -> None:
    dedup = _RecordingDedupService()
    audit = _RecordingAuditWriter()
    repo = _RecordingRepository(fail=True)
    pipeline = _Aud005Pipeline(
        payloads=[{"id": "persist-fail"}],
        dedup_service=dedup,
        audit_writer=audit,
        signal_repository=repo,
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 0
    assert pipeline._metrics.persistence_failures == 1
    assert dedup.stored == []
    assert audit.outcomes == ["degraded"]
    assert dedup.claimed == set()


@pytest.mark.asyncio
async def test_aud002_blocked_source_skips_normalize_dedup_and_persist() -> None:
    dedup = _RecordingDedupService()
    audit = _RecordingAuditWriter()
    repo = _RecordingRepository(fail=False)
    pipeline = _Aud005Pipeline(
        payloads=[{"id": "blocked-1"}],
        dedup_service=dedup,
        audit_writer=audit,
        signal_repository=repo,
        governance_registry=_StaticEligibilityRegistry(False, "source_non_compliant"),
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 0
    assert pipeline._metrics.persistence_failures == 0
    assert dedup.stored == []
    assert repo.saved == []
    assert audit.outcomes == ["blocked"]


class _RecordingDeadLetterService:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []

    def create_entry(self, **kwargs):  # type: ignore[no-untyped-def]
        self.entries.append(kwargs)
        return type("DeadLetter", (), {"entry_id": f"dlq-{len(self.entries)}"})()


@pytest.mark.asyncio
async def test_validation_failure_creates_dead_letter_and_does_not_block_valid_sibling() -> None:
    dead_letters = _RecordingDeadLetterService()
    dedup = _RecordingDedupService()
    audit = _RecordingAuditWriter()
    repo = _RecordingRepository(fail=False)

    class _BadDatetimePipeline(MockPipeline):
        def normalise(self, raw_payload):
            envelope = super().normalise(raw_payload)
            if raw_payload.get("bad_datetime"):
                envelope["occurredAt"] = "2026-99-99"
            return envelope

    pipeline = _BadDatetimePipeline(
        payloads=[{"id": "bad", "bad_datetime": True}, {"id": "good"}],
        dedup_service=dedup,
        audit_writer=audit,
        signal_repository=repo,
        dead_letter_service=dead_letters,
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 1
    assert len(repo.saved) == 1
    assert audit.outcomes.count("rejected") == 1
    assert audit.outcomes.count("success") == 1
    assert len(dead_letters.entries) == 1
    assert dead_letters.entries[0]["failure_code"] in {"schema_validation_failed", "payload_model_validation_failed"}


@pytest.mark.asyncio
async def test_empty_source_uri_is_rejected_with_raw_reference_and_dlq() -> None:
    dead_letters = _RecordingDeadLetterService()
    audit = _RecordingAuditWriter()
    repo = _RecordingRepository(fail=False)

    class _EmptySourceUriPipeline(MockPipeline):
        def normalise(self, raw_payload):
            envelope = super().normalise(raw_payload)
            envelope["provenance"]["sourceUri"] = ""
            envelope["jurisdictionId"] = None
            return envelope

    class _RawStore:
        async def store_raw_payload(self, **kwargs):  # type: ignore[no-untyped-def]
            return f"raw://{kwargs['signal_id']}"

    pipeline = _EmptySourceUriPipeline(
        payloads=[{"id": "bad-uri"}],
        audit_writer=audit,
        signal_repository=repo,
        blob_storage=_RawStore(),
        dead_letter_service=dead_letters,
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 0
    assert audit.outcomes == ["rejected"]
    assert len(dead_letters.entries) == 1
    assert "raw_payload_blob_uri" in dead_letters.entries[0]["original_payload"]


@pytest.mark.asyncio
async def test_pipeline_passes_effective_dedup_ttl_to_claim_and_commit() -> None:
    dedup = _RecordingDedupService()
    repo = _RecordingRepository(fail=False)
    audit = _RecordingAuditWriter()
    pipeline = _Aud005Pipeline(
        payloads=[{"id": "ttl-test"}],
        dedup_service=dedup,
        signal_repository=repo,
        audit_writer=audit,
        dedup_ttl_seconds=777,
        scope="live",
    )

    await pipeline._poll_cycle()

    assert dedup.claim_ttls == [777]
    assert dedup.commit_ttls == [777]


@pytest.mark.asyncio
async def test_associate_multi_persists_one_record_per_incident_match() -> None:
    dedup = _RecordingDedupService()
    repo = _RecordingRepository(fail=False)
    audit = _RecordingAuditWriter()

    class _FanoutAssociation:
        async def associate_multi(self, envelope, scope="live"):
            a = dict(envelope)
            b = dict(envelope)
            a["incidentId"] = "inc-a"
            b["incidentId"] = "inc-b"
            return [a, b]

        async def associate(self, envelope, scope="live"):
            return envelope

    pipeline = _Aud005Pipeline(
        payloads=[{"id": "fanout-1"}],
        dedup_service=dedup,
        signal_repository=repo,
        audit_writer=audit,
        incident_association=_FanoutAssociation(),
        scope="live",
    )

    await pipeline._poll_cycle()

    assert pipeline._metrics.signals_ingested == 2
    assert len(repo.saved) == 2
    persisted_ids = [signal_id for _scope, signal_id in repo.saved]
    assert len(set(persisted_ids)) == 2
    assert audit.outcomes.count("success") == 2
    assert [entry["validation_status"] for entry in audit.entries] == ["validated", "validated"]


def _social_context_row(*, signal_id: str, account_id: str, scope: str, occurred_at: str, kind: str = "social") -> dict:
    return {
        "scope": scope,
        "signalId": signal_id,
        "category": "fire",
        "occurredAt": occurred_at,
        "receivedAt": occurred_at,
        "jurisdictionId": "nsw",
        "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 500},
        "payload": {
            "text": f"fire report {signal_id}",
            "topic": "bushfire",
            "accountId": account_id,
        },
        "source": {
            "dataSourceId": "mock-source" if kind == "social" else "bom-warnings",
            "name": "Twitter" if kind == "social" else "BoM",
            "kind": kind,
        },
        "confidenceScore": 0.3 if kind == "social" else 0.95,
        "freshnessScore": 0.9,
        "validationStatus": "pending" if kind == "social" else "validated",
        "provenance": {"sourceUri": "https://example.com", "collectionMethod": "api_pull"},
    }


@pytest.mark.asyncio
async def test_aud013_social_ingestion_applies_tier1_and_persists_flags() -> None:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    context = [
        _social_context_row(
            signal_id=f"sig-context-{i}",
            account_id=f"acct-{i}",
            scope="live",
            occurred_at=(now - timedelta(seconds=30 + i)).isoformat(),
        )
        for i in range(19)
    ]
    repo = _MisinformationContextRepository(context)
    pipeline = _SocialPipeline(
        payloads=[
            {
                "id": "social-1",
                "signalId": "sig-current",
                "accountId": "acct-current",
                "occurredAt": now.isoformat(),
            }
        ],
        signal_repository=repo,
        misinformation_detector=MisinformationDetector(),
        scope="live",
    )

    await pipeline._poll_cycle()

    assert len(repo.saved) == 1
    saved_signal = repo.saved[0][1]
    assert saved_signal.validation_status == "escalated"
    assert "burst_detected" in saved_signal.payload.get("misinformationFlags", [])
    assert saved_signal.payload.get("misinformationTier1Result", {}).get("status") == "escalated"
    assert "tier1_misinformation" in str(saved_signal.provenance.get("validationNotes", ""))


@pytest.mark.asyncio
async def test_aud013_context_is_scope_bounded_for_cross_tenant_isolation() -> None:
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    context = [
        _social_context_row(signal_id="sig-live-a", account_id="acct-live-a", scope="live", occurred_at=now),
        _social_context_row(signal_id="sig-sim-a", account_id="acct-sim-a", scope="sim-run-77", occurred_at=now),
        _social_context_row(
            signal_id="sig-sim-auth",
            account_id="acct-auth",
            scope="sim-run-77",
            occurred_at=now,
            kind="authoritative",
        ),
    ]
    repo = _MisinformationContextRepository(context)
    pipeline = _SocialPipeline(
        payloads=[
            {
                "id": "social-2",
                "signalId": "sig-live-current",
                "accountId": "acct-live-current",
                "occurredAt": now,
            }
        ],
        signal_repository=repo,
        misinformation_detector=MisinformationDetector(),
        scope="live",
    )

    await pipeline._poll_cycle()

    assert repo.query_scopes == ["live"]
    assert len(repo.saved) == 1
    saved_signal = repo.saved[0][1]
    # No authoritative corroboration in live scope; authoritative in sim scope must not affect this decision.
    assert "no_authoritative_corroboration" in saved_signal.payload.get("misinformationFlags", [])


@pytest.mark.asyncio
async def test_aud013_detector_is_deterministic_across_restart_with_same_scope_context() -> None:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    context = [
        _social_context_row(
            signal_id=f"sig-restart-{i}",
            account_id=f"acct-restart-{i}",
            scope="live",
            occurred_at=(now - timedelta(seconds=i * 5)).isoformat(),
        )
        for i in range(19)
    ]

    repo_first = _MisinformationContextRepository(context)
    first = _SocialPipeline(
        payloads=[
            {
                "id": "restart-1",
                "signalId": "sig-restart-current",
                "accountId": "acct-current",
                "occurredAt": now.isoformat(),
            }
        ],
        signal_repository=repo_first,
        misinformation_detector=MisinformationDetector(),
        scope="live",
    )
    await first._poll_cycle()

    repo_second = _MisinformationContextRepository(context)
    second = _SocialPipeline(
        payloads=[
            {
                "id": "restart-2",
                "signalId": "sig-restart-current",
                "accountId": "acct-current",
                "occurredAt": now.isoformat(),
            }
        ],
        signal_repository=repo_second,
        misinformation_detector=MisinformationDetector(),
        scope="live",
    )
    await second._poll_cycle()

    first_signal = repo_first.saved[0][1]
    second_signal = repo_second.saved[0][1]
    assert first_signal.validation_status == second_signal.validation_status == "escalated"
    assert first_signal.payload.get("misinformationFlags") == second_signal.payload.get("misinformationFlags")
