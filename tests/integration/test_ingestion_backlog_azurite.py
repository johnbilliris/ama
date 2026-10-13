"""Optional real-storage restart test using a disposable Azurite container."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from apps.ingestion.backlog import BlobIngestionBacklog

_CHILD = """
import asyncio
import json
import os
from azure.storage.blob import BlobServiceClient
from apps.ingestion.backlog import BlobIngestionBacklog
from app.services.ingestion.pipeline_base import IngestionPipelineBase, PipelineProcessingResult

class Pipeline(IngestionPipelineBase):
    def __init__(self, container):
        super().__init__(
            pipeline_id="restart-test", data_source_ids=["test"], poll_interval_seconds=60,
            max_records_per_cycle=2, backlog_store=BlobIngestionBacklog(container),
        )
        self.processed = []
        self.polls = 0

    async def poll_source(self):
        self.polls += 1
        return [{"id": i} for i in range(5)] if os.environ["TEST_FIRST_PROCESS"] == "1" else []

    def normalise(self, raw):
        return raw

    def compute_canonical_key(self, raw):
        return str(raw["id"])

    async def _process_payload(self, raw):
        self.processed.append(raw["id"])
        return PipelineProcessingResult(True, "accepted")

with BlobServiceClient.from_connection_string(
    os.environ["AMA_INGESTION_BACKLOG_TEST_CONNECTION_STRING"], api_version="2025-11-05",
) as service:
    pipeline = Pipeline(service.get_container_client(os.environ["TEST_CONTAINER"]))
    asyncio.run(pipeline._poll_cycle())
    print(json.dumps({"processed": pipeline.processed, "polls": pipeline.polls}))
"""


@pytest.mark.integration
def test_bounded_snapshot_survives_three_separate_worker_processes() -> None:
    connection = os.environ.get("AMA_INGESTION_BACKLOG_TEST_CONNECTION_STRING")
    if not connection:
        pytest.skip("Set AMA_INGESTION_BACKLOG_TEST_CONNECTION_STRING to a local Azurite endpoint")
    root = Path(__file__).resolve().parents[2]
    env = {
        **os.environ,
        "TEST_CONTAINER": f"ingestion-backlog-test-{uuid4().hex}",
        "PYTHONPATH": os.pathsep.join((str(root), str(root / "apps" / "api"))),
    }
    results = []
    with BlobServiceClient.from_connection_string(connection, api_version="2025-11-05") as service:
        container = service.get_container_client(env["TEST_CONTAINER"])
        container.create_container()
        try:
            for first in ("1", "0", "0"):
                completed = subprocess.run(
                    [sys.executable, "-c", _CHILD],
                    env={**env, "TEST_FIRST_PROCESS": first},
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60,
                )
                results.append(json.loads(completed.stdout.strip().splitlines()[-1]))
            assert results == [
                {"processed": [0, 1], "polls": 1},
                {"processed": [2, 3], "polls": 0},
                {"processed": [4], "polls": 0},
            ]
            assert not any("/batches/" in blob.name for blob in container.list_blobs())
        finally:
            container.delete_container()


@pytest.mark.integration
def test_real_lease_contention_preserves_snapshot_and_resumes_after_release() -> None:
    connection = os.environ.get("AMA_INGESTION_BACKLOG_TEST_CONNECTION_STRING")
    if not connection:
        pytest.skip("Set AMA_INGESTION_BACKLOG_TEST_CONNECTION_STRING to a local Azurite endpoint")
    with BlobServiceClient.from_connection_string(connection, api_version="2025-11-05") as service:
        container = service.get_container_client(f"ingestion-backlog-test-{uuid4().hex}")
        container.create_container()
        try:

            async def exercise() -> None:
                owner = BlobIngestionBacklog(container)
                contender = BlobIngestionBacklog(container)
                async with owner.open("live", "contention-test") as batch:
                    await batch.stage([{"id": 0}, {"id": 1}])
                    with pytest.raises(ResourceExistsError) as caught:
                        async with contender.open("live", "contention-test"):
                            pytest.fail("contender acquired a held lease")
                    assert caught.value.error_code == "LeaseAlreadyPresent"
                    assert batch.offset == 0
                    assert batch.pending == 2
                async with contender.open("live", "contention-test") as resumed:
                    assert resumed.payloads == [{"id": 0}, {"id": 1}]
                    assert resumed.offset == 0
                    await resumed.commit(2)
                    await resumed.cleanup()

            asyncio.run(exercise())
            assert not any("/batches/" in blob.name for blob in container.list_blobs())
        finally:
            container.delete_container()
