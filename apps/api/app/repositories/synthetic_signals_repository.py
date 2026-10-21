"""Synthetic-signals Cosmos repository — spec-036 Phase L (T-L03).

Targets the ``simulation_synthetic_signals`` container shipped via Wave 1
T-A09 (`infra/bicep/modules/cosmos-simulation-containers.bicep:54`),
partitioned by ``/simulationId``.

Methods
-------
* ``persist(signal)`` — durably write a :class:`SyntheticSignal` (idempotent
  via Cosmos upsert; partition key is ``simulation_id``).
* ``list_recent(sim_id, window_seconds)`` — return signals whose
  ``observed_at`` is within the window. Used by Phase L fan-out to feed
  the FR-051 read-your-own-write loop.

Follows the auto-connect pattern from
:class:`apps.api.app.repositories.signal_repository.SignalRepository` —
when ``COSMOS_ENDPOINT`` is set the repository talks to Cosmos via
DefaultAzureCredential; otherwise it falls back to an in-memory dict so
unit / contract tests can exercise the round-trip without infrastructure.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.async_io import run_blocking

from packages.domain.src.domain.models.synthetic_signal import SyntheticSignal

logger = logging.getLogger(__name__)


def _build_cosmos_client() -> Any:
    """Build a CosmosClient from the ``COSMOS_ENDPOINT`` env var."""

    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class SyntheticSignalsRepository:
    """Cosmos repository for the ``simulation_synthetic_signals`` container."""

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._db_name = database_name
        self._container_name = "simulation_synthetic_signals"
        self._partition_key_path = "/simulationId"
        # In-memory store keyed by (simulation_id, signal_id).
        self._in_memory: dict[tuple[str, str], SyntheticSignal] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SyntheticSignalsRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    async def persist(self, signal: SyntheticSignal) -> SyntheticSignal:
        """Durably write ``signal`` (idempotent upsert; partition by simulation_id)."""

        container = self._get_container()
        if container is not None:
            doc = signal.model_dump(mode="json")
            # Cosmos partition path is ``/simulationId`` — surface the value
            # alongside the existing snake_case ``simulation_id`` field so
            # the Bicep partition path still resolves.
            doc.setdefault("simulationId", signal.simulation_id)
            doc["id"] = signal.signal_id
            await run_blocking(container.upsert_item, doc)
        else:
            self._in_memory[(signal.simulation_id, signal.signal_id)] = signal
        return signal

    async def list_recent(self, simulation_id: str, window_seconds: int) -> list[SyntheticSignal]:
        """Return signals for ``simulation_id`` whose ``observed_at`` is
        within ``window_seconds`` of now.

        The window is anchored on UTC ``now``; signals with ``observed_at``
        in the future are still returned (clock-skew tolerance) — only
        signals strictly older than the window are filtered out.
        """

        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)

        container = self._get_container()
        if container is not None:
            query = (
                "SELECT * FROM c WHERE c.simulation_id = @sim AND c.observed_at >= @cutoff ORDER BY c.observed_at DESC"
            )
            params = [
                {"name": "@sim", "value": simulation_id},
                {"name": "@cutoff", "value": cutoff.isoformat()},
            ]
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=params,
                        partition_key=simulation_id,
                    )
                )
            )
            return [SyntheticSignal.model_validate(item) for item in items]

        return [
            sig for (sim, _sid), sig in self._in_memory.items() if sim == simulation_id and sig.observed_at >= cutoff
        ]


__all__ = [
    "SyntheticSignalsRepository",
    "get_synthetic_signals_repository",
    "reset_synthetic_signals_repository_for_tests",
]


_default_repository: SyntheticSignalsRepository | None = None


def get_synthetic_signals_repository() -> SyntheticSignalsRepository:
    """Return the process-wide :class:`SyntheticSignalsRepository` (lazy)."""

    global _default_repository
    if _default_repository is None:
        _default_repository = SyntheticSignalsRepository()
    return _default_repository


def reset_synthetic_signals_repository_for_tests() -> None:
    """Reset the process-wide singleton — tests only."""

    global _default_repository
    _default_repository = None
