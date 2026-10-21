from datetime import UTC, datetime

import pytest
from app.services.scenario_seeding_service import ScenarioSeedingService
from app.services.simulation_signal_adapter import template_entry_to_signal

from packages.domain.src.domain.models.scenario_template import (
    BenchmarkTargets,
    ScenarioTemplate,
    SignalTimelineEntry,
)
from packages.domain.src.domain.repositories.signal_wire import partition_key_of, to_signal_document


class TestScenarioTemplate:
    def test_timeline_sorted_ascending(self):
        template = ScenarioTemplate(
            template_id="test-template",
            scenario_type="Bushfire",
            name="Test",
            signal_timeline=[
                SignalTimelineEntry(offset_seconds=0, signal_envelope={"type": "smoke"}),
                SignalTimelineEntry(offset_seconds=60, signal_envelope={"type": "fire"}),
            ],
        )
        assert len(template.signal_timeline) == 2

    def test_timeline_unsorted_raises(self):
        with pytest.raises(ValueError, match="sorted ascending"):
            ScenarioTemplate(
                template_id="bad-template",
                scenario_type="Bushfire",
                name="Bad",
                signal_timeline=[
                    SignalTimelineEntry(offset_seconds=60, signal_envelope={"type": "fire"}),
                    SignalTimelineEntry(offset_seconds=0, signal_envelope={"type": "smoke"}),
                ],
            )

    def test_negative_offset_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            SignalTimelineEntry(offset_seconds=-1, signal_envelope={"type": "test"})

    def test_positive_benchmarks_required(self):
        with pytest.raises(ValueError):
            BenchmarkTargets(time_to_first_recommendation_s=0)


@pytest.mark.asyncio
async def test_template_lookup_enables_cross_partition_query() -> None:
    class _SeedContainer:
        def query_items(self, query, *, parameters, enable_cross_partition_query=False):  # noqa: ANN001, ANN202
            if not enable_cross_partition_query:
                raise RuntimeError("Cross partition query is required but disabled")
            return []

    class _CosmosClient:
        def get_database_client(self, name):  # noqa: ANN001, ANN201
            assert name == "disaster-hub"
            return self

        def get_container_client(self, name):  # noqa: ANN001, ANN201
            assert name == "seed"
            return _SeedContainer()

    service = ScenarioSeedingService(signal_repository=object(), cosmos_client=_CosmosClient())

    template = await service._load_template("nsw-bushfire-multi-agency")

    assert template is not None
    assert template.template_id == "nsw-bushfire-multi-agency"


def test_curated_signal_normalizes_to_live_model_and_hpk_document() -> None:
    signal = template_entry_to_signal(
        {
            "data_source_id": "bom-warnings",
            "category": "weather",
            "jurisdiction_id": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8]},
            "payload": {"summary": "Exercise warning"},
            "confidence_score": 0.9,
            "freshness_score": 1.0,
            "validation_status": "validated",
            "provenance": {"source": "bom-warnings", "source_context": "simulation"},
        },
        tenant_id="sim-12345678-1234-1234-1234-123456789012",
        offset_seconds=60,
        exercise_start=datetime(2026, 1, 1, tzinfo=UTC),
    )

    document = to_signal_document(signal, "sim-12345678-1234-1234-1234-123456789012")
    assert signal.occurred_at == datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
    assert signal.location["precisionMeters"] == 1000.0
    assert signal.provenance["simulationRunId"] == "12345678-1234-1234-1234-123456789012"
    assert partition_key_of(document) == [
        "sim-12345678-1234-1234-1234-123456789012",
        "nsw",
        "bom-warnings",
    ]


@pytest.mark.asyncio
async def test_curated_template_seeding_persists_signals_and_context() -> None:
    class _Signals:
        def __init__(self) -> None:
            self.saved = []

        async def save(self, signal, *, scope):  # noqa: ANN001, ANN202
            self.saved.append((scope, signal))

    class _SimulationRepository:
        def __init__(self) -> None:
            self.documents = []

        async def upsert_document(self, document):  # noqa: ANN001, ANN202
            self.documents.append(document)

    class _Scheduler:
        def __init__(self) -> None:
            self.timeline = []
            self.started = []

        def initialize(self, tenant_id, timeline, warp_speed=1.0):  # noqa: ANN001, ANN201
            self.timeline = list(timeline)

        def start_delivery_loop(self, tenant_id):  # noqa: ANN001, ANN201
            self.started.append(tenant_id)
            return True

    signals = _Signals()
    simulations = _SimulationRepository()
    service = ScenarioSeedingService(
        signal_repository=signals,
        simulation_repository=simulations,
        warp_scheduler=_Scheduler(),
    )
    tenant_id = "sim-12345678-1234-1234-1234-123456789012"

    result = await service.seed_from_template(tenant_id, "nsw-bushfire-multi-agency")

    assert result["signals_injected"] == 0
    assert result["signals_scheduled"] > 0
    assert signals.saved == []
    assert result["organisations_seeded"] == 7
    assert all(scope == tenant_id for scope, _ in signals.saved)
    assert all(signal.provenance["simulationRunId"] == tenant_id.removeprefix("sim-") for _, signal in signals.saved)
    assert {document["document_type"] for document in simulations.documents} == {
        "simulation_seed_organisation",
        "simulation_seed_framework",
        "simulation_seed_jurisdictions",
        "simulation_seed_template",
    }
