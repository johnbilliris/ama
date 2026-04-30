"""GeoJSON Pydantic response models for the /api/v1/incidents/map endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Severity domain value → Australian Warning System tier mapping ──

SEVERITY_TO_AWS_TIER: dict[str, str] = {
    "advisory": "advice",
    "watch": "watch",
    "warning": "emergency",
    "emergency": "emergency",
}


# ── GeoJSON primitives ──


class GeoJSONPoint(BaseModel):
    """RFC 7946 GeoJSON Point geometry."""

    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[longitude, latitude] per RFC 7946",
    )


# ── Feature properties ──


class IncidentFeatureProperties(BaseModel):
    """Properties payload for a single incident GeoJSON Feature."""

    incident_id: str
    title: str
    incident_type: str
    status: str
    severity: str
    severity_tier: str = Field(..., description="Mapped AWS tier: advice | watch | emergency")
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str]
    started_at: str = Field(..., description="ISO 8601 datetime string")
    pprr_phase: str | None = None
    incident_level: int


# ── Feature ──


class IncidentFeature(BaseModel):
    """A single incident as a GeoJSON Feature."""

    type: Literal["Feature"] = "Feature"
    id: str = Field(..., description="incident_id")
    geometry: GeoJSONPoint
    properties: IncidentFeatureProperties


# ── Metadata ──


class IncidentMapMetadata(BaseModel):
    """Pagination and count metadata for the map endpoint response."""

    total: int = Field(..., description="Total matching incidents with location")
    unmapped_count: int = Field(..., description="Matching incidents missing location")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Items per page")
    fetched_at: str = Field(..., description="ISO 8601 timestamp of data retrieval")


# ── FeatureCollection ──


class IncidentFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection response envelope."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[IncidentFeature]
    metadata: IncidentMapMetadata
