from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from apps.api.app.repositories.signal_repository import SignalRepository
from apps.ingestion.pipeline_config import IngestionPipelineConfig
from apps.ingestion.pipeline_factory import create_pipeline
from apps.ingestion.worker import _build_signal_repository
from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.repositories.signal_repository import SignalRepository as DomainSignalRepository


def test_ingestion_worker_uses_domain_repository_without_api_dependency(monkeypatch) -> None:
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "test")

    repository, init_error = _build_signal_repository()

    assert isinstance(repository, DomainSignalRepository)
    assert init_error is None


def test_ingestion_worker_requires_cosmos_endpoint_in_production(monkeypatch) -> None:
    monkeypatch.delenv("COSMOS_ENDPOINT", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "production")

    with pytest.raises(RuntimeError, match="COSMOS_ENDPOINT"):
        _build_signal_repository()


def test_signal_repository_save_sets_partition_metadata() -> None:
    repo = SignalRepository(cosmos_client=None)
    signal = Signal(
        signal_id="sig-1",
        incident_id="inc-1",
        data_source_id="bom-warnings",
        category="weather",
        occurred_at=datetime.now(UTC),
        received_at=datetime.now(UTC),
        jurisdiction_id="nsw",
        location={"type": "Point", "coordinates": [151.2, -33.8]},
        payload={"headline": "Storm warning"},
        classification="official",
        retention_until=datetime.now(UTC),
        confidence_score=0.9,
        freshness_score=0.9,
        validation_status="validated",
        provenance={"collector": "bom-warnings"},
    )

    asyncio.run(repo.save(signal, scope="live"))

    stored = repo._in_memory["live:sig-1"]
    assert stored["scope"] == "live"
    assert stored["jurisdictionId"] == "nsw"
    assert stored["dataSourceId"] == "bom-warnings"
    assert stored["partitionKey"] == "live/nsw/bom-warnings"


def test_pipeline_factory_injects_signal_repository_dependency() -> None:
    config = IngestionPipelineConfig(
        pipeline_id="bom-warnings",
        source_class="authoritative",
        data_source_ids=["bom-warnings"],
        poll_interval_seconds=120,
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="xml_bom",
    )
    repo = SignalRepository(cosmos_client=None)

    pipeline = create_pipeline(config, signal_repository=repo)

    assert pipeline is not None
    assert getattr(pipeline, "signal_repository", None) is repo


def test_signal_repository_cosmos_point_read_enforces_tenant_scope() -> None:
    class _Container:
        def read_item(self, signal_id: str, partition_key: str | None = None) -> dict[str, str]:  # noqa: ARG002
            return {"id": signal_id, "scope": "sim-tenant"}

    class _Db:
        def get_container_client(self, _container_name: str) -> _Container:
            return _Container()

    class _Client:
        def get_database_client(self, _db_name: str) -> _Db:
            return _Db()

    repo = SignalRepository(cosmos_client=_Client())
    result = asyncio.run(repo.get_signal("live", "sig-42", partition_key="live/nsw/ds"))
    assert result is None


def test_signal_repository_raises_on_configured_cosmos_init_failure(monkeypatch) -> None:
    monkeypatch.setenv("COSMOS_ENDPOINT", "https://example.invalid")

    from apps.api.app.repositories import signal_repository as signal_repo_module

    def _explode() -> object:
        raise RuntimeError("cosmos init failed")

    monkeypatch.setattr(signal_repo_module, "_build_cosmos_client", _explode)

    repo = SignalRepository()
    signal = Signal(
        signal_id="sig-fail",
        incident_id="inc-1",
        data_source_id="bom-warnings",
        category="weather",
        occurred_at=datetime.now(UTC),
        received_at=datetime.now(UTC),
        jurisdiction_id="nsw",
        location={"type": "Point", "coordinates": [151.2, -33.8]},
        payload={},
        classification="official",
        retention_until=datetime.now(UTC),
        confidence_score=0.9,
        freshness_score=0.9,
        validation_status="validated",
        provenance={"collector": "test"},
    )

    with pytest.raises(RuntimeError, match="SignalRepository unavailable for mutations"):
        asyncio.run(repo.save(signal, scope="live"))
