"""GET /api/v1/incidents/map — GeoJSON FeatureCollection for the Disaster Mapper UI.

Returns incidents with valid geographic locations as GeoJSON Features.
Supports multi-value filtering (AND across categories, OR within).
Always excludes rehearsal-status incidents server-side.
"""

import logging
import time
from datetime import UTC, datetime
from typing import Annotated, TypedDict

from app.models.geojson import (
    SEVERITY_TO_AWS_TIER,
    GeoJSONPoint,
    IncidentFeature,
    IncidentFeatureCollection,
    IncidentFeatureProperties,
    IncidentMapMetadata,
)
from app.repositories.incident_map_repository import IncidentMapRepository
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)


class IncidentMapLocation(TypedDict, total=False):
    coordinates: list[float]


class IncidentMapDocument(TypedDict, total=False):
    incident_id: str
    location: IncidentMapLocation
    severity: str
    started_at: str | datetime
    title: str
    incident_type: str
    status: str
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str]
    pprr_phase: str | None
    incident_level: int


router = APIRouter(prefix="/incidents", tags=["incidents"])

_repo = IncidentMapRepository()

# ── Telemetry counters (T032) ──
_request_count = 0
_error_count = 0

# ── Allowed enum values ──────────────────────────────────────────────────

VALID_TYPES = {
    "biosecurity",
    "bushfire",
    "criminal",
    "cyclone",
    "earthquake",
    "environment",
    "extreme_heat",
    "flood",
    "health",
    "industrial",
    "landslide",
    "maritime_coastal",
    "other",
    "pandemic",
    "storm",
    "tornado",
    "transport",
    "tsunami",
    "urban_fire",
}
VALID_SEVERITIES = {"advisory", "watch", "warning", "emergency"}
VALID_STATUSES = {"monitoring", "active", "stabilising", "recovery", "closed"}
VALID_PPRR = {"prevention", "preparedness", "response", "recovery"}


def _parse_csv(raw: str | None, allowed: set[str], name: str) -> list[str] | None:
    """Parse a comma-separated query param into a validated list."""
    if not raw:
        return None
    values = [v.strip().lower() for v in raw.split(",") if v.strip()]
    invalid = [v for v in values if v not in allowed]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value for '{name}': {', '.join(invalid)}. Must be one of {', '.join(sorted(allowed))}",
        )
    return values or None


def _sanitise_keyword(keyword: str | None) -> str | None:
    """Sanitise keyword input — strip and enforce length limit."""
    if not keyword:
        return None
    keyword = keyword.strip()[:200]
    return keyword or None


def _to_feature(doc: IncidentMapDocument) -> IncidentFeature:
    """Convert a Cosmos DB incident document to a GeoJSON Feature."""
    location = doc.get("location", {})
    severity = doc.get("severity", "advisory")
    started_at = doc.get("started_at", "")
    if isinstance(started_at, datetime):
        started_at = started_at.isoformat()

    return IncidentFeature(
        id=doc["incident_id"],
        geometry=GeoJSONPoint(coordinates=location.get("coordinates", [0, 0])),
        properties=IncidentFeatureProperties(
            incident_id=doc["incident_id"],
            title=doc.get("title", ""),
            incident_type=doc.get("incident_type", "other"),
            status=doc.get("status", "monitoring"),
            severity=severity,
            severity_tier=SEVERITY_TO_AWS_TIER.get(severity, "advice"),
            affected_jurisdiction_ids=doc.get("affected_jurisdiction_ids", []),
            participating_organisation_ids=doc.get("participating_organisation_ids", []),
            started_at=started_at,
            pprr_phase=doc.get("pprr_phase"),
            incident_level=doc.get("incident_level", 1),
        ),
    )


@router.get("/map", response_model=IncidentFeatureCollection)
async def get_incidents_map(
    type: Annotated[str | None, Query(description="Comma-separated incident types")] = None,
    severity: Annotated[str | None, Query(description="Comma-separated severities")] = None,
    status: Annotated[str | None, Query(description="Comma-separated statuses")] = None,
    pprr_phase: Annotated[str | None, Query(description="Comma-separated PPRR phases")] = None,
    keyword: Annotated[str | None, Query(max_length=200, description="Keyword search on title")] = None,
    year_start: Annotated[int | None, Query(ge=1900, le=2100, description="Start year filter")] = None,
    year_end: Annotated[int | None, Query(ge=1900, le=2100, description="End year filter")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=500, description="Items per page")] = 200,
) -> IncidentFeatureCollection:
    """Return map incidents as a GeoJSON FeatureCollection."""
    global _request_count, _error_count
    _request_count += 1
    request_start = time.monotonic()

    # Validate comma-separated params
    incident_types = _parse_csv(type, VALID_TYPES, "type")
    severities_list = _parse_csv(severity, VALID_SEVERITIES, "severity")
    statuses_list = _parse_csv(status, VALID_STATUSES, "status")
    pprr_phases_list = _parse_csv(pprr_phase, VALID_PPRR, "pprr_phase")
    kw = _sanitise_keyword(keyword)

    if year_start is not None and year_end is not None and year_start > year_end:
        return IncidentFeatureCollection(
            features=[],
            metadata=IncidentMapMetadata(
                total=0,
                unmapped_count=0,
                page=page,
                page_size=page_size,
                fetched_at=datetime.now(UTC).isoformat(),
            ),
        )

    filter_kwargs = dict(
        incident_types=incident_types,
        severities=severities_list,
        statuses=statuses_list,
        pprr_phases=pprr_phases_list,
        keyword=kw,
        year_start=year_start,
        year_end=year_end,
    )

    try:
        items, total = await _repo.query_incidents(page=page, page_size=page_size, **filter_kwargs)
        unmapped_count = await _repo.count_unmapped(**filter_kwargs)
    except Exception:
        _error_count += 1
        error_rate = _error_count / max(_request_count, 1)
        logger.exception(
            "Cosmos DB query failed for /incidents/map",
            extra={
                "metric": "disaster_mapper.api_error_rate",
                "error_rate": error_rate,
                "request_count": _request_count,
                "error_count": _error_count,
            },
        )
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    elapsed_ms = (time.monotonic() - request_start) * 1000
    logger.info(
        "incidents/map served %d features in %.1fms (page %d)",
        len(items),
        elapsed_ms,
        page,
        extra={
            "metric": "disaster_mapper.api_response_ms",
            "elapsed_ms": elapsed_ms,
            "feature_count": len(items),
            "total": total,
            "unmapped_count": unmapped_count,
        },
    )

    features = [_to_feature(doc) for doc in items]

    return IncidentFeatureCollection(
        features=features,
        metadata=IncidentMapMetadata(
            total=total,
            unmapped_count=unmapped_count,
            page=page,
            page_size=page_size,
            fetched_at=datetime.now(UTC).isoformat(),
        ),
    )
