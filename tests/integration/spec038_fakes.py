"""Spec-038 — fakes for integration tests (in-memory Cosmos)."""

from __future__ import annotations

from typing import Any


class FakeContainer:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self.upsert_calls = 0

    def upsert_item(self, doc: dict) -> dict:
        self.upsert_calls += 1
        self.items[doc["id"]] = dict(doc)
        return doc

    def query_items(self, query: str, **kw: Any):  # pragma: no cover
        return list(self.items.values())


class FakeDatabase:
    def __init__(self) -> None:
        self._containers: dict[str, FakeContainer] = {}

    def get_container_client(self, name: str) -> FakeContainer:
        return self._containers.setdefault(name, FakeContainer())


class FakeCosmosClient:
    def __init__(self, *args: Any, **kw: Any) -> None:
        self.db = FakeDatabase()

    def get_database_client(self, name: str) -> FakeDatabase:
        return self.db
