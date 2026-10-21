"""Named-location coordinate resolution (FR-004a).

Resolves device names / location identifiers to geographic coordinates
when signals lack explicit lat/lon.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NamedLocationContainer(Protocol):
    def read_item(self, *, item: str, partition_key: str) -> dict[str, object]: ...

    def upsert_item(self, *, body: dict[str, object]) -> object: ...

    def query_items(self, *, query: str, enable_cross_partition_query: bool) -> Iterable[dict[str, object]]: ...


class NamedLocation(BaseModel):
    """Device name / location identifier → coordinate lookup."""

    location_id: str
    display_name: str
    latitude: float
    longitude: float
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LocationResolutionError(Exception):
    """Raised when a named location cannot be resolved."""


class NamedLocationRepository:
    """Cosmos DB client wrapper for named_locations collection."""

    def __init__(self, cosmos_container: NamedLocationContainer | None = None) -> None:
        self._container = cosmos_container
        self._local: dict[str, NamedLocation] = {}

    def resolve(self, location_id: str) -> tuple[float, float]:
        """Resolve a location identifier to (latitude, longitude).

        Raises LocationResolutionError if the location cannot be found.
        """
        location = self._get(location_id)
        if location is None:
            raise LocationResolutionError(f"Named location '{location_id}' not found in lookup table")
        logger.info(
            "named_location_resolved",
            extra={
                "location_id": location_id,
                "lat": location.latitude,
                "lon": location.longitude,
            },
        )
        return location.latitude, location.longitude

    def _get(self, location_id: str) -> NamedLocation | None:
        """Retrieve a named location by identifier."""
        if self._container is not None:
            try:
                doc = self._container.read_item(
                    item=location_id,
                    partition_key=location_id,
                )
                return NamedLocation.model_validate(doc)
            except Exception:
                return None
        return self._local.get(location_id)

    def upsert(self, location: NamedLocation) -> None:
        """Create or update a named location."""
        if self._container is not None:
            doc = location.model_dump(mode="json")
            doc["id"] = location.location_id
            self._container.upsert_item(body=doc)
        else:
            self._local[location.location_id] = location

    def list_all(self) -> list[NamedLocation]:
        """List all named locations."""
        if self._container is not None:
            docs = list(
                self._container.query_items(
                    query="SELECT * FROM c",
                    enable_cross_partition_query=True,
                )
            )
            return [NamedLocation.model_validate(doc) for doc in docs]
        return list(self._local.values())
