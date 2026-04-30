"""Cosmos DB repository for simulation chat history.

Each ``SimChatTurn`` is stored as a document in the ``sim-chat`` container
partitioned by ``/tenant_id``. This matches the pattern used by
``SimulationRepository`` (in-memory fallback when ``COSMOS_ENDPOINT`` is
not set) so unit / contract tests keep working without infrastructure.

The design follows Azure OpenAI conversation-history best practice
(https://learn.microsoft.com/azure/ai-services/openai/how-to/chatgpt):
maintain an ordered ``[{role, content}, …]`` array per conversation and
replay it on every completion request.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from packages.domain.src.domain.models.sim_chat_turn import SimChatTurn

logger = logging.getLogger(__name__)

_CONTAINER = "sim-chat"
_DEFAULT_DB = "disaster-hub"


class SimChatHistoryRepository:
    """Append-only store for ``SimChatTurn`` documents.

    * When ``COSMOS_ENDPOINT`` is set, writes/reads to the ``sim-chat``
      container in the configured database.
    * Otherwise keeps turns in an in-memory dict keyed by ``tenant_id``.
    """

    def __init__(self, cosmos_client: Any | None = None, database_name: str | None = None):
        self._db_name = database_name or os.environ.get("COSMOS_DATABASE", _DEFAULT_DB)
        self._container_name = _CONTAINER
        self._in_memory: dict[str, list[SimChatTurn]] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "SimChatHistoryRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    # ------------------------------------------------------------------
    # container helper
    # ------------------------------------------------------------------

    def _get_container(self) -> Any | None:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ------------------------------------------------------------------
    # sequence bookkeeping
    # ------------------------------------------------------------------

    def next_sequence(self, tenant_id: str) -> int:
        """Return the next monotonic ``sequence`` value for this tenant."""
        container = self._get_container()
        if container is None:
            return len(self._in_memory.get(tenant_id, [])) + 1
        query = "SELECT VALUE MAX(c.sequence) FROM c WHERE c.document_type = 'sim_chat_turn' AND c.tenant_id = @tid"
        try:
            items = list(
                container.query_items(
                    query,
                    parameters=[{"name": "@tid", "value": tenant_id}],
                    partition_key=tenant_id,
                )
            )
            current = items[0] if items and items[0] is not None else 0
            return int(current) + 1
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "next_sequence: Cosmos query failed (%s); using in-memory counter",
                exc,
            )
            return len(self._in_memory.get(tenant_id, [])) + 1

    # ------------------------------------------------------------------
    # writes
    # ------------------------------------------------------------------

    def append_turn(self, turn: SimChatTurn) -> SimChatTurn:
        container = self._get_container()
        if container is None:
            self._in_memory.setdefault(turn.tenant_id, []).append(turn)
            return turn
        doc = turn.model_dump(mode="json")
        try:
            container.upsert_item(doc)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "append_turn: Cosmos write failed (%s); caching turn in-memory",
                exc,
            )
            self._in_memory.setdefault(turn.tenant_id, []).append(turn)
        return turn

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------

    def list_turns(
        self,
        tenant_id: str,
        *,
        limit: int | None = None,
    ) -> list[SimChatTurn]:
        """Return turns for ``tenant_id`` in ascending ``sequence`` order.

        When ``limit`` is provided, returns the *last* N turns (tail).
        This is the shape needed to replay context on the next chat call.
        """
        container = self._get_container()
        if container is None:
            turns = sorted(self._in_memory.get(tenant_id, []), key=lambda t: t.sequence)
        else:
            query = (
                "SELECT * FROM c WHERE c.document_type = 'sim_chat_turn' AND c.tenant_id = @tid ORDER BY c.sequence ASC"
            )
            try:
                items = list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@tid", "value": tenant_id}],
                        partition_key=tenant_id,
                    )
                )
                turns = [SimChatTurn.model_validate(i) for i in items]
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "list_turns: Cosmos query failed (%s); returning in-memory cache",
                    exc,
                )
                turns = sorted(self._in_memory.get(tenant_id, []), key=lambda t: t.sequence)
        if limit is not None and len(turns) > limit:
            turns = turns[-limit:]
        return turns

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------

    def delete_history(self, tenant_id: str) -> int:
        """Remove all turns for a tenant. Returns count deleted. Safe to call
        when archiving a simulation to keep the container lean."""
        container = self._get_container()
        if container is None:
            turns = self._in_memory.pop(tenant_id, [])
            return len(turns)
        query = "SELECT c.id FROM c WHERE c.document_type = 'sim_chat_turn' AND c.tenant_id = @tid"
        items = list(
            container.query_items(
                query,
                parameters=[{"name": "@tid", "value": tenant_id}],
                partition_key=tenant_id,
            )
        )
        for item in items:
            container.delete_item(item=item["id"], partition_key=tenant_id)
        return len(items)


def _build_cosmos_client() -> Any:
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


# Module-level singleton — mirrors other repositories in the API layer.
_default_repo: SimChatHistoryRepository | None = None


def default_history_repo() -> SimChatHistoryRepository:
    """Return a process-wide default history repository."""
    global _default_repo
    if _default_repo is None:
        _default_repo = SimChatHistoryRepository()
    return _default_repo
