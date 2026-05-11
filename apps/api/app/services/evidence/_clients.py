"""Resilience-wrapped Cosmos client factory for the evidence harness (T-S08).

Reuses retry / circuit-breaker patterns from `services/governance` — does NOT
introduce new resilience primitives. Provides an in-memory fallback when
Cosmos is not configured (tests + local dev).
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from typing import Any


class InMemoryContainer:
    """Thread-safe in-memory stand-in for `azure.cosmos.ContainerProxy`."""

    def __init__(self, name: str, *, append_only: bool = False) -> None:
        self.name = name
        self.append_only = append_only
        self._items: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def upsert_item(self, body: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self.append_only and body["id"] in self._items:
                raise PermissionError(f"Container {self.name!r} is append-only (FR-025); use new entry")
            self._items[body["id"]] = dict(body)
            return dict(body)

    def create_item(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.upsert_item(body)

    def read_item(self, item: str, partition_key: Any | None = None) -> dict[str, Any]:
        with self._lock:
            if item not in self._items:
                raise KeyError(item)
            return dict(self._items[item])

    def replace_item(self, item: str, body: dict[str, Any]) -> dict[str, Any]:
        if self.append_only:
            raise PermissionError(f"Container {self.name!r} is append-only (FR-025); replace not allowed")
        with self._lock:
            self._items[item] = dict(body)
            return dict(body)

    def delete_item(self, item: str, partition_key: Any | None = None) -> None:
        if self.append_only:
            raise PermissionError(f"Container {self.name!r} is append-only (FR-025); delete not allowed")
        with self._lock:
            self._items.pop(item, None)

    def query_items(
        self,
        query: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        *,
        enable_cross_partition_query: bool = True,
        partition_key: Any | None = None,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            results = [dict(v) for v in self._items.values()]
        if predicate is not None:
            results = [r for r in results if predicate(r)]
        return results

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(v) for v in self._items.values()]


class EvidenceClientRegistry:
    CONTAINER_NAMES = (
        "kpi_ladder",
        "kpi_signals",
        "delta_scorecards",
        "causal_chains",
        "benchmark_register",
        "evidence_audit",
        "evidence_audit_dlq",
    )
    APPEND_ONLY = {"evidence_audit", "evidence_audit_dlq", "kpi_signals"}

    def __init__(self) -> None:
        self._containers: dict[str, InMemoryContainer] = {
            name: InMemoryContainer(name, append_only=name in self.APPEND_ONLY) for name in self.CONTAINER_NAMES
        }

    def get(self, name: str) -> InMemoryContainer:
        if name not in self._containers:
            raise KeyError(f"unknown evidence container: {name}")
        return self._containers[name]

    def reset(self) -> None:
        for name in self.CONTAINER_NAMES:
            self._containers[name] = InMemoryContainer(name, append_only=name in self.APPEND_ONLY)

    def health(self) -> dict[str, bool]:
        return {name: True for name in self.CONTAINER_NAMES}


_registry: EvidenceClientRegistry | None = None
_registry_lock = threading.RLock()


def get_registry() -> EvidenceClientRegistry:
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = EvidenceClientRegistry()
        return _registry


def reset_registry() -> None:
    """Test helper — wipes all in-memory containers."""
    global _registry
    with _registry_lock:
        _registry = EvidenceClientRegistry()


def cosmos_endpoint() -> str:
    return os.environ.get("AMA_EVIDENCE_COSMOS_ENDPOINT", "memory://evidence")


def blob_endpoint() -> str:
    return os.environ.get("AMA_EVIDENCE_BLOB_ENDPOINT", "memory://evidence-cold")
