import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from apps.ingestion.pipeline_config import IngestionPipelineConfig, resolve_pipeline_configs
from apps.ingestion.pipeline_factory import create_pipeline
from apps.ingestion.worker import PipelineWorker


def _config(**overrides: object) -> IngestionPipelineConfig:
    return IngestionPipelineConfig.model_validate(
        {
            "pipeline_id": "bom-aws-stations",
            "source_class": "sensor",
            "data_source_ids": ["bom-aws-stations"],
            "poll_interval_seconds": 300,
            "endpoint_url": "https://example.com",
            "endpoint_format": "json",
            **overrides,
        }
    )


def test_absent_override_preserves_default_and_explicit_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INGESTION_MAX_RECORDS_PER_CYCLE", raising=False)
    configs = [_config(), _config(max_records_per_cycle=42)]

    resolved = resolve_pipeline_configs(configs)

    assert [config.max_records_per_cycle for config in resolved] == [100, 42]


@pytest.mark.parametrize("limit", [1, 250, 5000])
def test_environment_overrides_every_config_without_mutation(monkeypatch: pytest.MonkeyPatch, limit: int) -> None:
    monkeypatch.setenv("INGESTION_MAX_RECORDS_PER_CYCLE", str(limit))
    configs = [_config(), _config(max_records_per_cycle=42, enabled=False)]

    resolved = resolve_pipeline_configs(configs)

    assert [config.max_records_per_cycle for config in resolved] == [limit, limit]
    assert [config.max_records_per_cycle for config in configs] == [100, 42]
    assert resolved[0].model_dump(exclude={"max_records_per_cycle"}) == configs[0].model_dump(
        exclude={"max_records_per_cycle"}
    )
    assert resolved[1].enabled is False


@pytest.mark.parametrize("limit", ["", " ", "abc", "1.0", "1.5", "0", "-1", "5001"])
@pytest.mark.asyncio
async def test_invalid_environment_fails_before_starting_pipelines(monkeypatch: pytest.MonkeyPatch, limit: str) -> None:
    monkeypatch.setenv("INGESTION_MAX_RECORDS_PER_CYCLE", limit)
    factory = Mock()
    worker = PipelineWorker()

    with pytest.raises(ValueError, match="INGESTION_MAX_RECORDS_PER_CYCLE"):
        await worker.start([_config()], pipeline_factory=factory)

    factory.assert_not_called()
    assert worker._running is False
    assert not worker._pipelines
    assert not worker._tasks


@pytest.mark.asyncio
async def test_worker_passes_override_to_actual_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INGESTION_MAX_RECORDS_PER_CYCLE", "3")
    monkeypatch.setattr(asyncio.get_running_loop(), "add_signal_handler", Mock())
    config = _config(max_records_per_cycle=7)
    worker = PipelineWorker()

    def factory(resolved: IngestionPipelineConfig) -> object:
        pipeline = create_pipeline(resolved)
        pipeline.run = AsyncMock()
        pipeline.stop = AsyncMock()
        return pipeline

    try:
        await worker.start([config], pipeline_factory=factory)
        assert worker._pipelines[config.pipeline_id].max_records_per_cycle == 3
        assert config.max_records_per_cycle == 7
    finally:
        await worker.stop()
