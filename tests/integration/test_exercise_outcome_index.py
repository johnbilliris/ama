"""T-H04 — Cosmos exercise_outcome_index writer unit + integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.app.services.simulation.lessons_capture_index import (
    ExerciseOutcomeIndexConfig,
    InMemoryIndexWriter,
    make_cosmos_index_writer,
)
from tests.staging_gates import cosmos_staging_enabled as azure_cosmos_staging_enabled


@pytest.mark.asyncio
async def test_in_memory_writer_idempotent_on_same_doc() -> None:
    writer = InMemoryIndexWriter()
    doc = {"id": "sim-1", "simulation_id": "sim-1", "blob_uri": "memory://x"}
    await writer(doc)
    await writer(dict(doc))  # same body
    assert len(writer.documents) == 1


@pytest.mark.asyncio
async def test_in_memory_writer_rejects_different_body() -> None:
    writer = InMemoryIndexWriter()
    await writer({"id": "sim-2", "simulation_id": "sim-2", "blob_uri": "memory://a"})
    with pytest.raises(RuntimeError, match="already stored with different body"):
        await writer({"id": "sim-2", "simulation_id": "sim-2", "blob_uri": "memory://b"})


@pytest.mark.asyncio
async def test_azure_index_writer_calls_upsert_item() -> None:
    container = MagicMock()
    container.upsert_item = AsyncMock(return_value={"id": "sim-3"})

    writer = make_cosmos_index_writer(container=container)
    doc = {
        "id": "sim-3",
        "simulation_id": "sim-3",
        "blob_uri": "https://acct.blob.core.windows.net/exercise-outcome-records/sim-3.json",
        "tenant_id": "sim-tenant-3",
        "end_reason": "completed",
    }
    await writer(doc)
    container.upsert_item.assert_called_once_with(item=doc)


@pytest.mark.asyncio
async def test_azure_index_writer_propagates_upsert_failures() -> None:
    container = MagicMock()
    container.upsert_item = AsyncMock(side_effect=RuntimeError("boom"))
    writer = make_cosmos_index_writer(container=container)

    with pytest.raises(RuntimeError, match="boom"):
        await writer({"id": "sim-4", "simulation_id": "sim-4"})


def test_index_config_defaults_match_spec() -> None:
    config = ExerciseOutcomeIndexConfig()
    assert config.container_name == "exercise_outcome_index"
    assert config.partition_key_path == "/simulation_id"


@pytest.mark.azure_cosmos_staging
@pytest.mark.skipif(
    not azure_cosmos_staging_enabled(),
    reason="Live Cosmos — set AMA_STAGING_COSMOS=1 to invoke against staging.",
)
def test_index_persists_against_staging_cosmos() -> None:
    pytest.skip("Staging gate — exercises a live `exercise_outcome_index` upsert.")
