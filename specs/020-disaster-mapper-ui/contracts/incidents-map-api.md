# API Contract: GET /api/v1/incidents/map

**Feature**: 020-disaster-mapper-ui
**Date**: 2025-07-17
**Spec references**: FR-029, FR-030, FR-035

---

## Endpoint

```
GET /api/v1/incidents/map
```

**Tags**: `incidents`
**Auth**: Existing application authentication (Assumption §7)
**Description**: Returns incidents with geographic location data as a GeoJSON FeatureCollection for map rendering. Supports server-side filtering by multiple criteria. Excludes rehearsal-status incidents.

## Request

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | `string` | No | — | Filter by incident type(s). Comma-separated list of: `bushfire`, `flood`, `cyclone`, `storm`, `earthquake`, `tsunami`, `extreme_heat`, `pandemic`, `other`. Example: `type=bushfire,flood` |
| `severity` | `string` | No | — | Filter by severity level(s). Comma-separated list of: `advisory`, `watch`, `warning`, `emergency`. Example: `severity=warning,emergency` |
| `status` | `string` | No | — | Filter by operational status(es). Comma-separated list of: `monitoring`, `active`, `stabilising`, `recovery`, `closed`. Example: `status=active,monitoring` |
| `pprr_phase` | `string` | No | — | Filter by PPRR phase(s). Comma-separated list of: `prevention`, `preparedness`, `response`, `recovery`. Example: `pprr_phase=response,recovery` |
| `keyword` | `string` | No | — | Case-insensitive keyword search against incident title |
| `year_start` | `integer` | No | — | Filter incidents with `started_at` year ≥ this value |
| `year_end` | `integer` | No | — | Filter incidents with `started_at` year ≤ this value |
| `page` | `integer` | No | `1` | Page number (1-based). Must be ≥ 1 |
| `page_size` | `integer` | No | `200` | Items per page. Must be 1–500 |

### Validation Rules

- `type` accepts a comma-separated list of valid `IncidentType` enum values if provided; each value is validated individually
- `severity` accepts a comma-separated list of valid `Severity` enum values if provided; each value is validated individually
- `status` accepts a comma-separated list of valid operational statuses (not `rehearsal`) if provided; each value is validated individually
- `pprr_phase` accepts a comma-separated list of valid `PprrPhase` enum values if provided; each value is validated individually
- When both year bounds are provided and `year_start` > `year_end`, return `200 OK` with an empty `FeatureCollection`, `total=0`, and `unmapped_count=0`. Preserve the requested `page` and `page_size` and include `fetched_at`; do not query the repository.
- `keyword` max length: 200 characters; sanitised to prevent injection
- `page` ≥ 1
- `page_size` between 1 and 500 (inclusive)
- All filters combine with AND logic (FR-013)

### Example Request

```
GET /api/v1/incidents/map?type=bushfire,flood&severity=warning,emergency&status=active&year_start=2020&page=1&page_size=200
```

## Response

### 200 OK

**Content-Type**: `application/json`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "incident-2024-nsw-001",
      "geometry": {
        "type": "Point",
        "coordinates": [151.2093, -33.8688]
      },
      "properties": {
        "incident_id": "incident-2024-nsw-001",
        "title": "Sydney Basin Bushfire Complex",
        "incident_type": "bushfire",
        "status": "active",
        "severity": "warning",
        "severity_tier": "emergency",
        "affected_jurisdiction_ids": ["nsw", "act"],
        "participating_organisation_ids": ["rfs-nsw", "act-esa"],
        "started_at": "2024-01-15T08:30:00Z",
        "pprr_phase": "response",
        "incident_level": 3
      }
    },
    {
      "type": "Feature",
      "id": "incident-2024-qld-003",
      "geometry": {
        "type": "Point",
        "coordinates": [153.0251, -27.4698]
      },
      "properties": {
        "incident_id": "incident-2024-qld-003",
        "title": "Brisbane River Flood Warning",
        "incident_type": "flood",
        "status": "monitoring",
        "severity": "advisory",
        "severity_tier": "advice",
        "affected_jurisdiction_ids": ["qld"],
        "participating_organisation_ids": ["ses-qld"],
        "started_at": "2024-02-20T14:00:00Z",
        "pprr_phase": "preparedness",
        "incident_level": 1
      }
    }
  ],
  "metadata": {
    "total": 142,
    "unmapped_count": 3,
    "page": 1,
    "page_size": 200,
    "fetched_at": "2024-01-20T10:15:30Z"
  }
}
```

### Response Schema

#### FeatureCollection (root)

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"FeatureCollection"` | GeoJSON type identifier (always `"FeatureCollection"`) |
| `features` | `Feature[]` | Array of incident features with Point geometry |
| `metadata` | `Metadata` | Pagination and count metadata |

#### Feature

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"Feature"` | GeoJSON type identifier (always `"Feature"`) |
| `id` | `string` | Incident ID (same as `properties.incident_id`) |
| `geometry` | `Point` | GeoJSON Point with `[longitude, latitude]` coordinates |
| `properties` | `Properties` | Incident attribute data |

#### Point (geometry)

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"Point"` | GeoJSON geometry type |
| `coordinates` | `[number, number]` | `[longitude, latitude]` per RFC 7946 |

#### Properties

| Field | Type | Description |
|-------|------|-------------|
| `incident_id` | `string` | Unique incident identifier |
| `title` | `string` | Incident display title |
| `incident_type` | `string` | One of the 9 incident type values |
| `status` | `string` | Operational status (never `rehearsal`) |
| `severity` | `string` | Domain severity value (`advisory`/`watch`/`warning`/`emergency`) |
| `severity_tier` | `string` | Mapped AWS tier: `advice`, `watch`, or `emergency` |
| `affected_jurisdiction_ids` | `string[]` | Jurisdiction ID references |
| `participating_organisation_ids` | `string[]` | Organisation ID references |
| `started_at` | `string` | ISO 8601 datetime |
| `pprr_phase` | `string \| null` | PPRR lifecycle phase or null |
| `incident_level` | `integer` | AIIMS incident level (1, 2, or 3) |

#### Metadata

| Field | Type | Description |
|-------|------|-------------|
| `total` | `integer` | Total incidents matching filters (with valid location) |
| `unmapped_count` | `integer` | Incidents matching filters but missing location data (FR-030) |
| `page` | `integer` | Current page number |
| `page_size` | `integer` | Items per page |
| `fetched_at` | `string` | ISO 8601 timestamp of data retrieval |

### Error Responses

| Status | Condition | Response Body |
|--------|-----------|---------------|
| `400 Bad Request` | Invalid query parameter value | `{"detail": "Invalid value for 'severity': must be one of advisory, watch, warning, emergency"}` |
| `401 Unauthorized` | Missing/invalid authentication | `{"detail": "Not authenticated"}` |
| `403 Forbidden` | Insufficient permissions | `{"detail": "Insufficient permissions"}` |
| `500 Internal Server Error` | Cosmos DB or server failure | `{"detail": "Internal server error"}` |
| `503 Service Unavailable` | Cosmos DB unreachable | `{"detail": "Service temporarily unavailable"}` |

## Frontend Progressive Loading Strategy (FR-035)

The frontend loads incident data progressively:

1. **Initial load**: `GET /api/v1/incidents/map?page=1&page_size=200` — render first 200 immediately
2. **Second request**: `GET /api/v1/incidents/map?page=2&page_size=200` — background fetch
3. **Third request**: `GET /api/v1/incidents/map?page=3&page_size=200` — background fetch (cumulative: 500+)
4. **Continue**: Fetch subsequent pages until `features.length < page_size` (indicates last page)

When filters change, the sequence restarts from page 1.

## Server-Side Filter Behaviour

- **No filters applied**: Returns all non-rehearsal incidents with valid location, ordered by `started_at DESC`
- **Multiple filters**: Combined with AND logic across filter categories; within a multi-value filter, values combine with OR logic — e.g., `type=bushfire,flood&status=active` matches incidents that are (bushfire OR flood) AND (active)
- **Rehearsal exclusion**: Always applied, not exposed as a filter option
- **Location requirement**: Only incidents with valid `location.type = "Point"` geometry are included in `features`; `metadata.unmapped_count` reports incidents matching filters but lacking location
