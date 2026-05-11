"""Simulation lifecycle-state repository — spec-036 Phase P (T-P01) / FR-059.

Persists the simulation lifecycle ``state`` (``active`` / ``paused`` /
``aborted``) durably with **ETag-conditional concurrency** so concurrent
pause / resume / abort requests can never produce a torn write
(constitution v1.2.0 fail-closed invariant).

Per tasks.md T-P01 the implementation **augments the existing
``simulation`` container** rather than creating a new one. In Cosmos the
state is stored on the simulation document under the ``lifecycle_state``
field (alongside the existing ``status`` business-state); ETag is the
Cosmos-native ``_etag`` system property.

Auto-connect pattern
--------------------
* If ``COSMOS_ENDPOINT`` is set we bind a real :class:`CosmosClient` via
  :class:`DefaultAzureCredential`.
* Otherwise the repository operates against an in-memory dict so unit /
  contract tests can exercise the round-trip without infrastructure.
  In that mode we simulate ETag with an integer counter formatted as a
  string so callers see opaque tokens.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Final, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

LifecycleState = Literal["active", "paused", "aborted"]

_VALID_STATES: Final[tuple[LifecycleState, ...]] = ("active", "paused", "aborted")


class UnknownSimulationError(LookupError):
    """The requested ``simulation_id`` has no lifecycle-state document."""


class ETagConflictError(RuntimeError):
    """The supplied ``expected_etag`` did not match the stored ETag."""


class SimulationLifecycleState(BaseModel):
    """Immutable snapshot of one simulation's lifecycle state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    simulation_id: str
    state: LifecycleState
    etag: str


def _build_cosmos_client() -> Any:
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class SimulationStateRepository:
    """Lifecycle-state persistence with ETag-conditional updates."""

    def __init__(
        self, cosmos_client: Any = None, database_name: str = "disaster-hub"
    ) -> None:
        self._db_name = database_name
        self._container_name = "simulation"
        self._in_memory: dict[str, dict[str, Any]] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SimulationStateRepository: Cosmos init failed (%s); "
                    "falling back to in-memory store",
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

    @staticmethod
    def _validate_state(new_state: object) -> LifecycleState:
        if new_state not in _VALID_STATES:
            raise ValueError(
                f"Unknown lifecycle state {new_state!r}; expected one of "
                f"{_VALID_STATES!r}"
            )
        return new_state  # type: ignore[return-value]

    async def bootstrap(self, simulation_id: str) -> SimulationLifecycleState:
        """Initialise the lifecycle-state document for a new simulation."""

        container = self._get_container()
        if container is not None:
            doc = {
                "id": f"{simulation_id}:lifecycle",
                "simulation_id": simulation_id,
                "lifecycle_state": "active",
                "document_type": "simulation_lifecycle_state",
            }
            saved = container.upsert_item(doc)
            return SimulationLifecycleState(
                simulation_id=simulation_id,
                state="active",
                etag=saved.get("_etag", str(uuid4())),
            )

        etag = str(uuid4())
        self._in_memory[simulation_id] = {
            "state": "active",
            "_etag": etag,
        }
        return SimulationLifecycleState(
            simulation_id=simulation_id, state="active", etag=etag
        )

    async def read(self, simulation_id: str) -> SimulationLifecycleState:
        container = self._get_container()
        if container is not None:
            try:
                doc = container.read_item(
                    f"{simulation_id}:lifecycle",
                    partition_key=simulation_id,
                )
            except Exception as exc:  # noqa: BLE001
                raise UnknownSimulationError(
                    f"No lifecycle-state document for simulation_id={simulation_id!r}"
                ) from exc
            return SimulationLifecycleState(
                simulation_id=simulation_id,
                state=doc.get("lifecycle_state", "active"),
                etag=doc.get("_etag", ""),
            )

        record = self._in_memory.get(simulation_id)
        if record is None:
            raise UnknownSimulationError(
                f"No lifecycle-state document for simulation_id={simulation_id!r}"
            )
        return SimulationLifecycleState(
            simulation_id=simulation_id,
            state=record["state"],
            etag=record["_etag"],
        )

    async def update_state(
        self,
        simulation_id: str,
        new_state: LifecycleState,
        expected_etag: str,
    ) -> SimulationLifecycleState:
        """Conditionally update the lifecycle state.

        Raises :class:`ETagConflictError` when ``expected_etag`` does not
        match the stored ETag (enforces the constitution fail-closed
        invariant under concurrent pause/resume/abort).
        """

        target = self._validate_state(new_state)

        # Read first to surface existence + state-machine validation.
        current = await self.read(simulation_id)
        if current.state == "aborted":
            raise ValueError(
                f"Simulation {simulation_id!r} is in terminal state 'aborted'; "
                "no further lifecycle transitions are permitted."
            )

        if current.etag != expected_etag:
            raise ETagConflictError(
                f"ETag mismatch for simulation_id={simulation_id!r}: expected "
                f"{expected_etag!r}, current {current.etag!r}"
            )

        container = self._get_container()
        if container is not None:
            doc_id = f"{simulation_id}:lifecycle"
            doc = container.read_item(doc_id, partition_key=simulation_id)
            doc["lifecycle_state"] = target
            try:
                replaced = container.replace_item(
                    doc_id,
                    doc,
                    if_match=expected_etag,
                )
            except Exception as exc:  # noqa: BLE001
                raise ETagConflictError(
                    f"Cosmos replace_item rejected the conditional update: {exc}"
                ) from exc
            return SimulationLifecycleState(
                simulation_id=simulation_id,
                state=target,
                etag=replaced.get("_etag", str(uuid4())),
            )

        new_etag = str(uuid4())
        self._in_memory[simulation_id] = {
            "state": target,
            "_etag": new_etag,
        }
        return SimulationLifecycleState(
            simulation_id=simulation_id, state=target, etag=new_etag
        )


__all__ = [
    "ETagConflictError",
    "LifecycleState",
    "SimulationLifecycleState",
    "SimulationStateRepository",
    "UnknownSimulationError",
    "get_simulation_state_repository",
    "reset_simulation_state_repository_for_tests",
]


_default_repository: SimulationStateRepository | None = None


def get_simulation_state_repository() -> SimulationStateRepository:
    """Return the process-wide :class:`SimulationStateRepository` (lazy)."""

    global _default_repository
    if _default_repository is None:
        _default_repository = SimulationStateRepository()
    return _default_repository


def reset_simulation_state_repository_for_tests() -> None:
    """Reset the process-wide singleton — tests only."""

    global _default_repository
    _default_repository = None
