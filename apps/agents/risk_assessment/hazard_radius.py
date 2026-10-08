"""Cosmos DB-backed hazard radius lookup table (FR-006 / R12).

Admin-editable severity-indexed radius lookup per hazard type
for GeoJSON polygon generation. Changes effective without restart.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default seed data for 5 hazard types x severity 1-5 (metres)
_DEFAULT_RADII: dict[str, dict[str, float]] = {
    "bushfire": {"1": 1000, "2": 2500, "3": 5000, "4": 7500, "5": 10000},
    "flood": {"1": 500, "2": 1500, "3": 3000, "4": 4500, "5": 5000},
    "earthquake": {"1": 2000, "2": 5000, "3": 10000, "4": 15000, "5": 20000},
    "cyclone": {"1": 5000, "2": 15000, "3": 30000, "4": 40000, "5": 50000},
    "chemical_spill": {"1": 200, "2": 500, "3": 1000, "4": 1500, "5": 2000},
}

_FALLBACK_RADII: dict[str, float] = {
    "1": 1000,
    "2": 2500,
    "3": 5000,
    "4": 7500,
    "5": 10000,
}


class HazardRadiusContainer(Protocol):
    def read_item(self, *, item: str, partition_key: str) -> dict[str, object]: ...

    def query_items(self, *, query: str, enable_cross_partition_query: bool) -> Iterable[dict[str, object]]: ...

    def upsert_item(self, *, body: dict[str, object]) -> object: ...


class HazardRadiusLookup(BaseModel):
    """Admin-editable radius lookup entry stored in Cosmos DB."""

    id: str = ""
    hazard_type: str
    radii: dict[str, float]
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_by: str = "system-seed"

    def model_post_init(self, __context: object) -> None:
        if not self.id:
            self.id = self.hazard_type


class HazardRadiusRepository:
    """Cosmos DB client wrapper for radius_lookup collection."""

    def __init__(self, cosmos_container: HazardRadiusContainer | None = None) -> None:
        self._container = cosmos_container
        # In-memory fallback for local dev
        self._local: dict[str, HazardRadiusLookup] = {}
        if cosmos_container is None:
            self._seed_local()

    def _seed_local(self) -> None:
        """Seed in-memory store with defaults."""
        for hazard_type, radii in _DEFAULT_RADII.items():
            self._local[hazard_type] = HazardRadiusLookup(
                hazard_type=hazard_type,
                radii=radii,
            )

    def get_radius(self, hazard_type: str, severity: int | str) -> float:
        """Get radius in metres for a hazard type and severity level."""
        severity_key = str(severity)
        entry = self._get_entry(hazard_type)
        if entry:
            return entry.radii.get(severity_key, _FALLBACK_RADII.get(severity_key, 5000))
        return _FALLBACK_RADII.get(severity_key, 5000)

    def _get_entry(self, hazard_type: str) -> HazardRadiusLookup | None:
        """Retrieve entry from Cosmos or local store."""
        if self._container is not None:
            try:
                doc = self._container.read_item(
                    item=hazard_type,
                    partition_key=hazard_type,
                )
                return HazardRadiusLookup.model_validate(doc)
            except Exception:
                return None
        return self._local.get(hazard_type)

    def list_all(self) -> list[HazardRadiusLookup]:
        """List all radius lookup entries."""
        if self._container is not None:
            docs = list(
                self._container.query_items(
                    query="SELECT * FROM c",
                    enable_cross_partition_query=True,
                )
            )
            return [HazardRadiusLookup.model_validate(doc) for doc in docs]
        return list(self._local.values())

    def upsert(self, entry: HazardRadiusLookup) -> None:
        """Create or update a radius entry."""
        if self._container is not None:
            doc = entry.model_dump(mode="json")
            doc["id"] = entry.hazard_type
            self._container.upsert_item(body=doc)
        else:
            self._local[entry.hazard_type] = entry

    def create(self, entry: HazardRadiusLookup) -> None:
        """Create a new radius entry. Raises ValueError on duplicate."""
        existing = self._get_entry(entry.hazard_type)
        if existing:
            raise ValueError(f"Hazard type '{entry.hazard_type}' already exists")
        self.upsert(entry)


def seed_radius_data(repo: HazardRadiusRepository) -> None:
    """Seed the radius lookup table with defaults for 5 hazard types."""
    for hazard_type, radii in _DEFAULT_RADII.items():
        entry = HazardRadiusLookup(hazard_type=hazard_type, radii=radii)
        try:
            repo.create(entry)
            logger.info("Seeded radius data for %s", hazard_type)
        except ValueError:
            pass  # Already exists
