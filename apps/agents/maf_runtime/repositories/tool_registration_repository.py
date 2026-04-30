"""Tool Registration repository — Cosmos-backed (T017, FR-019, FR-019a).

A new major version is a NEW document with a NEW composite id (``<tool_name>:v<major>``);
in-place updates of an existing ``(tool_name, major_version)`` are refused so the
audit trail is preserved (per FR-014, FR-019a).
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from ..errors import ToolRegistrationConflictError

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ToolRegistrationRepository:
    """Cosmos-backed repository for the ``tool_registrations`` container."""

    def __init__(
        self,
        cosmos_client: Any = None,
        database_name: str = "platform",
        container_name: str = "tool_registrations",
    ) -> None:
        self._db_name = database_name
        self._container_name = container_name
        self._in_memory: dict[str, dict[str, Any]] = {}
        self._mem_lock = Lock()

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT") or os.environ.get("AZURE_COSMOS_ENDPOINT"):
            try:
                self._client = self._build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning("ToolRegistrationRepository Cosmos init failed (%s); using in-memory", exc)
                self._client = None
        else:
            self._client = None

    @staticmethod
    def _build_cosmos_client() -> Any:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential

        endpoint = os.environ.get("COSMOS_ENDPOINT") or os.environ["AZURE_COSMOS_ENDPOINT"]
        return CosmosClient(endpoint, credential=DefaultAzureCredential())

    def _container(self) -> Any | None:
        if self._client is None:
            return None
        return self._client.get_database_client(self._db_name).get_container_client(self._container_name)

    @staticmethod
    def _composite_id(tool_name: str, major_version: int) -> str:
        return f"{tool_name}:v{int(major_version)}"

    def register(
        self,
        *,
        tool_name: str,
        major_version: int,
        address: str,
        bound_agents: list[str],
        capability_description: str,
        registered_by: str,
    ) -> dict[str, Any]:
        """Register a new (tool_name, major_version) tuple.

        Raises ToolRegistrationConflictError if an entry already exists for the pair.
        """
        composite_id = self._composite_id(tool_name, major_version)
        existing = self.get(tool_name, major_version)
        if existing is not None:
            raise ToolRegistrationConflictError(
                f"Tool {tool_name} v{major_version} already registered as {composite_id}; "
                "bump the major version and register a new entry.",
                correlation_id="tool-register",
                details={"tool_name": tool_name, "major_version": major_version},
            )
        doc = {
            "id": composite_id,
            "tool_name": tool_name,
            "address": address,
            "pinned_major_version": int(major_version),
            "bound_agents": list(bound_agents),
            "capability_description": capability_description,
            "registered_at": _now_iso(),
            "registered_by": registered_by,
        }
        container = self._container()
        if container is not None:
            container.create_item(body=doc)
        else:
            with self._mem_lock:
                self._in_memory[composite_id] = doc
        return doc

    def get(self, tool_name: str, major_version: int) -> dict[str, Any] | None:
        composite_id = self._composite_id(tool_name, major_version)
        container = self._container()
        if container is not None:
            try:
                return container.read_item(item=composite_id, partition_key=tool_name)
            except Exception:  # noqa: BLE001 - including 404
                return None
        with self._mem_lock:
            return self._in_memory.get(composite_id)

    def get_for_agent(self, agent_name: str) -> list[dict[str, Any]]:
        container = self._container()
        if container is not None:
            try:
                return list(
                    container.query_items(
                        query="SELECT * FROM c WHERE ARRAY_CONTAINS(c.bound_agents, @a)",
                        parameters=[{"name": "@a", "value": agent_name}],
                        enable_cross_partition_query=True,
                    )
                )
            except Exception:  # noqa: BLE001
                logger.exception("get_for_agent(%s) failed", agent_name)
                return []
        with self._mem_lock:
            return [d for d in self._in_memory.values() if agent_name in d.get("bound_agents", [])]


__all__ = ["ToolRegistrationRepository"]
