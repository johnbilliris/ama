from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any


class IncidentModeUnavailable(RuntimeError):
    """The configured authoritative incident-mode store could not be read."""


@dataclass(frozen=True)
class IncidentModeState:
    active: bool
    version: int
    available: bool
    source: str
    document: dict[str, Any]
    detail: str | None = None


def _default_document() -> dict[str, Any]:
    return {
        "id": "incident-mode",
        "partitionKey": "incident-mode",
        "document_type": "incident_mode",
        "active": False,
        "version": 0,
        "updated_at": None,
        "updated_by": None,
    }


class IncidentModeRepository:
    _memory_lock = Lock()
    _memory_document: dict[str, Any] = _default_document()

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub") -> None:
        self._database_name = database_name
        self._configured = cosmos_client is not None or bool(os.environ.get("COSMOS_ENDPOINT"))
        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential

            self._client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=DefaultAzureCredential())
        else:
            self._client = None

    def _container(self) -> Any | None:
        if self._client is None:
            return None
        return self._client.get_database_client(self._database_name).get_container_client("governance")

    async def get_state(self) -> IncidentModeState:
        """Read authoritative state, reporting an outage instead of faking ``normal``."""
        try:
            container = self._container()
        except Exception as exc:  # noqa: BLE001
            return IncidentModeState(False, 0, False, "cosmos", _default_document(), str(exc))

        if container is None:
            if self._configured:
                return IncidentModeState(
                    False,
                    0,
                    False,
                    "cosmos",
                    _default_document(),
                    "governance container unavailable",
                )
            with type(self)._memory_lock:
                document = dict(type(self)._memory_document)
            return IncidentModeState(bool(document["active"]), int(document["version"]), True, "memory", document)

        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        try:
            document = await asyncio.to_thread(
                container.read_item,
                item="incident-mode",
                partition_key="incident-mode",
            )
        except CosmosResourceNotFoundError:
            # No declaration has ever been persisted; that is a known-normal state.
            return IncidentModeState(False, 0, True, "cosmos", _default_document())
        except Exception as exc:  # noqa: BLE001
            return IncidentModeState(False, 0, False, "cosmos", _default_document(), str(exc))

        return IncidentModeState(
            bool(document.get("active")),
            int(document.get("version", 0)),
            True,
            "cosmos",
            dict(document),
        )

    async def get(self) -> dict[str, Any]:
        state = await self.get_state()
        if not state.available:
            raise IncidentModeUnavailable(state.detail or "incident mode store unavailable")
        return state.document

    async def transition(self, *, active: bool, actor_id: str) -> tuple[dict[str, Any], bool]:
        container = self._container()
        now = datetime.now(UTC).isoformat()
        if container is None:
            if self._configured:
                raise IncidentModeUnavailable("governance container unavailable")
            with type(self)._memory_lock:
                changed = bool(type(self)._memory_document["active"]) != active
                if changed:
                    type(self)._memory_document = {
                        **type(self)._memory_document,
                        "active": active,
                        "version": int(type(self)._memory_document["version"]) + 1,
                        "updated_at": now,
                        "updated_by": actor_id,
                    }
                return dict(type(self)._memory_document), changed

        from azure.core import MatchConditions
        from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosResourceNotFoundError

        for _ in range(5):
            try:
                document = await asyncio.to_thread(
                    container.read_item,
                    item="incident-mode",
                    partition_key="incident-mode",
                )
            except CosmosResourceNotFoundError:
                document = _default_document()
                try:
                    await asyncio.to_thread(container.create_item, document)
                except CosmosResourceExistsError:
                    continue
            if bool(document.get("active")) == active:
                return document, False
            document.update(
                {
                    "active": active,
                    "version": int(document.get("version", 0)) + 1,
                    "updated_at": now,
                    "updated_by": actor_id,
                }
            )
            try:
                updated = await asyncio.to_thread(
                    container.replace_item,
                    item=document["id"],
                    body=document,
                    etag=document.get("_etag"),
                    match_condition=MatchConditions.IfNotModified,
                )
                return updated, True
            except Exception as exc:
                if exc.__class__.__name__ not in {
                    "CosmosAccessConditionFailedError",
                    "CosmosHttpResponseError",
                }:
                    raise
        raise IncidentModeUnavailable("Incident mode transition contention exceeded retry budget")

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._memory_lock:
            cls._memory_document = _default_document()
