"""Spec-036 Wave 4 — T-O08 idempotency-cache fail-closed contract test.

Per ADR-036-009 / FR-051 the idempotency cache is a critical correctness
boundary: an unreachable Cosmos cache cannot be silently bypassed because
doing so would allow duplicate side effects on retry. The route layer
MUST surface ``IdempotencyCacheUnavailable`` as HTTP 503 (problem-detail
``idempotency-cache-unavailable``) rather than letting the request
proceed without idempotency protection.

The repository's ``_read`` and ``_store`` paths are taught to distinguish
"not found" (404 / not-found message) from genuine transport failures.
This module asserts:

1. A 404 from Cosmos is treated as a cache miss (not an outage).
2. A non-404 transport error from Cosmos raises
   :class:`IdempotencyCacheUnavailable`.
3. A store-failure on miss also raises (fail-closed on write-side).
"""

from __future__ import annotations

import pytest

from apps.api.app.repositories.simulation_idempotency_repository import (
    IdempotencyCacheRepository,
    IdempotencyCacheUnavailable,
)


class _FakeContainer:
    def __init__(
        self,
        *,
        read_exc: Exception | None = None,
        store_exc: Exception | None = None,
        store_doc: dict | None = None,
    ) -> None:
        self._read_exc = read_exc
        self._store_exc = store_exc
        self._store_doc = store_doc

    def read_item(self, *, item, partition_key):  # type: ignore[no-untyped-def]
        if self._read_exc is not None:
            raise self._read_exc
        if self._store_doc is not None and self._store_doc.get("id") == item:
            return self._store_doc
        raise _NotFoundError(404)

    def upsert_item(self, doc):  # type: ignore[no-untyped-def]
        if self._store_exc is not None:
            raise self._store_exc
        return doc


class _NotFoundError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"Resource not found ({status_code})")
        self.status_code = status_code


class _TransportError(Exception):
    def __init__(self, status_code: int = 500) -> None:
        super().__init__(f"Cosmos returned {status_code}")
        self.status_code = status_code


class _FakeDatabase:
    def __init__(self, container: _FakeContainer) -> None:
        self._container = container

    def get_container_client(self, _name):  # type: ignore[no-untyped-def]
        return self._container


class _FakeClient:
    def __init__(self, container: _FakeContainer) -> None:
        self._container = container

    def get_database_client(self, _name):  # type: ignore[no-untyped-def]
        return _FakeDatabase(self._container)


def _repo_with_container(container: _FakeContainer) -> IdempotencyCacheRepository:
    return IdempotencyCacheRepository(cosmos_client=_FakeClient(container))


@pytest.mark.asyncio
async def test_404_is_cache_miss_not_outage() -> None:
    """A 404 from Cosmos must NOT raise — it's an ordinary cache miss."""

    repo = _repo_with_container(_FakeContainer(read_exc=_NotFoundError(404)))
    result = await repo.lookup_or_store(
        sim_id="11111111-2222-3333-4444-555555555555",
        verb="pause",
        route="/api/simulations/11111111-2222-3333-4444-555555555555/pause",
        idempotency_key="key-1",
        body={"x": 1},
        rbac_subject_id="coord-1",
        current_state="active",
        response_status=200,
        response_body={"state": "paused"},
    )
    # CacheMiss → no exception.
    assert hasattr(result, "body_hash")


@pytest.mark.asyncio
async def test_500_transport_error_raises_unavailable() -> None:
    """A 500 from Cosmos must raise IdempotencyCacheUnavailable."""

    repo = _repo_with_container(_FakeContainer(read_exc=_TransportError(500)))
    with pytest.raises(IdempotencyCacheUnavailable):
        await repo.lookup_or_store(
            sim_id="11111111-2222-3333-4444-555555555555",
            verb="pause",
            route="/api/simulations/11111111-2222-3333-4444-555555555555/pause",
            idempotency_key="key-2",
            body={"x": 1},
            rbac_subject_id="coord-1",
            current_state="active",
            response_status=200,
            response_body={"state": "paused"},
        )


@pytest.mark.asyncio
async def test_503_transport_error_raises_unavailable() -> None:
    """Service-Unavailable from Cosmos must propagate to the caller."""

    repo = _repo_with_container(_FakeContainer(read_exc=_TransportError(503)))
    with pytest.raises(IdempotencyCacheUnavailable):
        await repo.lookup_or_store(
            sim_id="11111111-2222-3333-4444-555555555555",
            verb="resume",
            route="/api/simulations/11111111-2222-3333-4444-555555555555/resume",
            idempotency_key="key-3",
            body={"x": 1},
            rbac_subject_id="coord-1",
            current_state="paused",
            response_status=200,
            response_body={"state": "active"},
        )


@pytest.mark.asyncio
async def test_store_failure_raises_unavailable() -> None:
    """A failure on the upsert path must also fail-closed."""

    repo = _repo_with_container(
        _FakeContainer(
            read_exc=_NotFoundError(404),
            store_exc=_TransportError(500),
        )
    )
    with pytest.raises(IdempotencyCacheUnavailable):
        await repo.lookup_or_store(
            sim_id="11111111-2222-3333-4444-555555555555",
            verb="pause",
            route="/api/simulations/11111111-2222-3333-4444-555555555555/pause",
            idempotency_key="key-4",
            body={"x": 1},
            rbac_subject_id="coord-1",
            current_state="active",
            response_status=200,
            response_body={"state": "paused"},
        )
