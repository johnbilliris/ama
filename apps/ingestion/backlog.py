"""Leased, durable source snapshots and batch checkpoints in Blob Storage."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobClient, BlobLeaseClient, ContainerClient


class BacklogBatch:
    def __init__(
        self, store: BlobIngestionBacklog, prefix: str, checkpoint: BlobClient, lease: BlobLeaseClient
    ) -> None:
        self.store = store
        self.prefix = prefix
        self.checkpoint = checkpoint
        self.lease = lease
        self.name: str | None = None
        self.offset = 0
        self.total = 0
        self.payloads: list[dict[str, Any]] = []

    @property
    def pending(self) -> int:
        return self.total - self.offset

    async def load(self) -> None:
        content = await asyncio.to_thread(lambda: self.checkpoint.download_blob(lease=self.lease).readall())
        state = json.loads(content)
        if not isinstance(state, dict):
            raise ValueError("Invalid ingestion backlog checkpoint")
        self.name = state.get("batch")
        self.offset = state.get("offset", 0)
        self.total = state.get("total", 0)
        if (
            not isinstance(self.offset, int)
            or not isinstance(self.total, int)
            or not 0 <= self.offset <= self.total
            or (self.name is not None and not isinstance(self.name, str))
            or (self.name is not None and not self.name.startswith(f"{self.prefix}/batches/"))
            or (self.total > 0 and self.name is None)
        ):
            raise ValueError("Invalid ingestion backlog checkpoint")
        if self.pending:
            if not self.name or not self.name.startswith(f"{self.prefix}/batches/"):
                raise ValueError("Invalid ingestion backlog batch path")
            cached = self.store._cache.get(self.prefix)
            if cached is not None and cached[0] == self.name:
                self.payloads = cached[1]
            else:
                blob = self.store.container.get_blob_client(self.name)
                data = await asyncio.to_thread(lambda: blob.download_blob().readall())
                self.payloads = json.loads(data)
                if not isinstance(self.payloads, list) or any(not isinstance(row, dict) for row in self.payloads):
                    raise ValueError("Invalid ingestion backlog payloads")
                self.store._cache[self.prefix] = (self.name, self.payloads)
            if len(self.payloads) != self.total:
                raise ValueError("Ingestion backlog size does not match its checkpoint")

    async def recover(self) -> bool:
        if self.pending:
            return True

        # An upload can finish before its checkpoint write; discover it after a crash.
        names = await asyncio.to_thread(
            lambda: sorted(
                blob.name for blob in self.store.container.list_blobs(name_starts_with=f"{self.prefix}/batches/")
            )
        )
        for name in names:
            if name == self.name:
                continue
            blob = self.store.container.get_blob_client(name)
            data = await asyncio.to_thread(lambda: blob.download_blob().readall())
            payloads = json.loads(data)
            if not isinstance(payloads, list) or any(not isinstance(row, dict) for row in payloads):
                raise ValueError("Invalid ingestion backlog payloads")
            await self._select(name, payloads)
            return True
        return False

    async def stage(self, payloads: list[dict[str, Any]]) -> None:
        if self.pending:
            raise RuntimeError("Cannot replace an unfinished ingestion batch")
        if not payloads:
            return
        name = f"{self.prefix}/batches/{datetime.now(UTC):%Y%m%dT%H%M%S%f}-{uuid4().hex}.json"
        data = await asyncio.to_thread(json.dumps, payloads)
        blob = self.store.container.get_blob_client(name)
        await asyncio.to_thread(blob.upload_blob, data.encode("utf-8"), overwrite=False)
        await self._select(name, payloads)

    async def _select(self, name: str, payloads: list[dict[str, Any]]) -> None:
        self.name = name
        self.payloads = payloads
        self.offset = 0
        self.total = len(payloads)
        self.store._cache[self.prefix] = (name, payloads)
        await self.commit(0)

    async def commit(self, offset: int) -> None:
        if not self.offset <= offset <= self.total:
            raise ValueError("Ingestion checkpoint must advance within the current batch")
        state = json.dumps({"batch": self.name, "offset": offset, "total": self.total})
        await asyncio.to_thread(self.checkpoint.upload_blob, state, overwrite=True, lease=self.lease)
        self.offset = offset

    async def retain_rejection(self, index: int, reason: str | None, status: str) -> None:
        if self.name is None:
            raise RuntimeError("Cannot retain a rejection without a source snapshot")
        batch_id = self.name.rsplit("/", 1)[-1]
        blob = self.store.container.get_blob_client(f"{self.prefix}/rejected/{batch_id}/{index}.json")
        data = json.dumps({"payload": self.payloads[index], "status": status, "reason": reason})
        await asyncio.to_thread(blob.upload_blob, data, overwrite=True)

    async def cleanup(self) -> None:
        if self.name is not None and not self.pending:
            from azure.core.exceptions import ResourceNotFoundError

            blob = self.store.container.get_blob_client(self.name)
            try:
                await asyncio.to_thread(blob.delete_blob)
            except ResourceNotFoundError:
                pass
            self.store._cache.pop(self.prefix, None)


class BlobIngestionBacklog:
    """One leased checkpoint per scope/source; unfinished snapshots survive restarts."""

    def __init__(self, container: ContainerClient) -> None:
        self.container = container
        self._cache: dict[str, tuple[str, list[dict[str, Any]]]] = {}

    @asynccontextmanager
    async def open(self, scope: str, pipeline_id: str) -> AsyncIterator[BacklogBatch]:
        identity = hashlib.sha256(json.dumps([scope, pipeline_id]).encode()).hexdigest()
        prefix = f"ingestion-backlog/{identity}"
        checkpoint = self.container.get_blob_client(f"{prefix}/checkpoint.json")
        try:
            await asyncio.to_thread(checkpoint.upload_blob, "{}", overwrite=False)
        except ResourceExistsError:
            pass
        lease = await asyncio.to_thread(checkpoint.acquire_lease, lease_duration=60)

        async def renew() -> None:
            while True:
                await asyncio.sleep(20)
                await asyncio.to_thread(lease.renew)

        try:
            async with asyncio.TaskGroup() as tasks:
                renewal = tasks.create_task(renew())
                try:
                    batch = BacklogBatch(self, prefix, checkpoint, lease)
                    await batch.load()
                    yield batch
                finally:
                    renewal.cancel()
        finally:
            await asyncio.to_thread(lease.release)
