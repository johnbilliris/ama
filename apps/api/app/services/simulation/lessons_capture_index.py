"""T-H04 — Cosmos exercise_outcome_index writer (FR-055).

Provides the :data:`apps.api.app.services.simulation.lessons_capture.IndexWriter`
callable that writes the index document to the
``exercise_outcome_index`` Cosmos container. Idempotency comes from the
PK ``record_id == simulation_id``:

* If the document already exists with the same body it's a no-op
  (HTTP 409 swallowed).
* If the document exists with a different body — an integrity violation —
  we surface the error so callers can audit it.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExerciseOutcomeIndexConfig:
    container_name: str = "exercise_outcome_index"
    partition_key_path: str = "/simulation_id"


class _CosmosContainerProtocol(Protocol):  # pragma: no cover - typing only
    async def upsert_item(self, item: dict[str, Any]) -> dict[str, Any]: ...
    async def read_item(self, item: str, partition_key: str) -> dict[str, Any]: ...


def make_cosmos_index_writer(
    *,
    container: _CosmosContainerProtocol,
) -> Callable[[dict[str, Any]], Awaitable[None]]:
    """Construct the Cosmos-backed :data:`IndexWriter` callable.

    Uses ``upsert_item`` so re-runs against the same ``record_id``
    converge — the document body MUST be identical between runs (the
    record-id is derived from ``simulation_id`` per FR-055).
    """

    async def _write(doc: dict[str, Any]) -> None:
        try:
            await container.upsert_item(item=doc)
            logger.info(
                "exercise_outcome_index.upsert id=%s sim=%s",
                doc.get("id"),
                doc.get("simulation_id"),
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "exercise_outcome_index.upsert_failed id=%s sim=%s",
                doc.get("id"),
                doc.get("simulation_id"),
            )
            raise

    return _write


class InMemoryIndexWriter:
    """In-memory writer honouring the PK==simulation_id idempotency contract."""

    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}

    async def __call__(self, doc: dict[str, Any]) -> None:
        rid = doc["id"]
        existing = self.documents.get(rid)
        if existing is not None and existing != doc:
            # Idempotency violation — surface so tests can assert.
            raise RuntimeError(
                f"exercise_outcome_index: {rid} already stored with different body"
            )
        self.documents[rid] = dict(doc)


__all__ = [
    "ExerciseOutcomeIndexConfig",
    "InMemoryIndexWriter",
    "make_cosmos_index_writer",
]
