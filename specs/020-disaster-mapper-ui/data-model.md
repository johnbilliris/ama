# Data Model: Disaster Mapper UI

**Feature**: 020-disaster-mapper-ui
**Date**: 2025-07-17
**Source spec**: [spec.md](./spec.md) — Key Entities, FR-029, Clarifications

---

## Entity Diagram

```text
┌─────────────────────────────────────────────────────────┐
│                        Incident                          │
│─────────────────────────────────────────────────────────│
│  incident_id: str                         (PK)          │
│  title: str                               (searchable)  │
│  incident_type: IncidentType              (filterable)  │
│  status: IncidentStatus                   (filterable)  │
│  severity: Severity                       (filterable)  │
│  affected_jurisdiction_ids: list[str]     (FK → Juris.) │
│  participating_organisation_ids: list[str]              │
│  owning_framework_ids: list[str]                        │
│  started_at: datetime                     (filterable)  │
│  pprr_phase: PprrPhase | None             (filterable)  │
│  incident_level: IncidentLevel            (display)     │
│  location: GeoJSON Point | None           (NEW, map)    │
│─────────────────────────────────────────────────────────│
│  Domain values:                                          │
│  IncidentType = bushfire | flood | cyclone | storm |     │
│    earthquake | tsunami | extreme_heat | pandemic | other│
│  IncidentStatus = monitoring | active | stabilising |    │
│    recovery | closed | rehearsal                         │
│  Severity = advisory | watch | warning | emergency       │
│  PprrPhase = prevention | preparedness | response |      │
│    recovery                                              │
│  IncidentLevel = 1 | 2 | 3                              │
└──────────────────────────┬──────────────────────────────┘
                           │ affected_jurisdiction_ids
                           ▼
┌─────────────────────────────────────────────────────────┐
│                      Jurisdiction                        │
│─────────────────────────────────────────────────────────│
│  jurisdiction_id: str                     (PK)          │
│  name: str                                              │
│  level: commonwealth | state | territory |              │
│         regional | local                                │
│  parent_jurisdiction_id: str | None       (self-ref)    │
│  policy_set_id: str                                     │
│  geospatial_boundary: dict (GeoJSON)                    │
│  status: active | inactive                              │
└─────────────────────────────────────────────────────────┘
```

## Model Extension: Incident.location

### Current model (`packages/domain/src/domain/models/incident.py`)

```python
class Incident(BaseModel):
    incident_id: str
    title: str
    incident_type: IncidentType
    status: Literal["monitoring", "active", "stabilising", "recovery", "closed", "rehearsal"]
    severity: Literal["advisory", "watch", "warning", "emergency"]
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str] = Field(default_factory=list)
    owning_framework_ids: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pprr_phase: PprrPhase | None = None
    incident_level: IncidentLevel = 1
```

### New field

```python
location: dict[str, Any] | None = None
```

- **Type**: Optional GeoJSON Point geometry — `{"type": "Point", "coordinates": [longitude, latitude]}`
- **Default**: `None` (backwards-compatible with existing incidents)
- **Validation**: Structural validation at the API response layer, not domain layer (consistent with `Jurisdiction.geospatial_boundary` pattern)
- **Storage**: Persisted in Cosmos DB `incidents` container as a nested JSON object
- **Import required**: Add `Any` to the typing import: `from typing import Any, Literal`

### GeoJSON Point structure (RFC 7946)

```json
{
  "type": "Point",
  "coordinates": [151.2093, -33.8688]
}
```

- `coordinates[0]` = longitude (east-west, range -180 to 180)
- `coordinates[1]` = latitude (north-south, range -90 to 90)
- Longitude-first order per GeoJSON specification

## API Response Models (`apps/api/app/models/geojson.py`)

### GeoJSON Point

```python
class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]  # [longitude, latitude]
```

### GeoJSON Feature (one incident)

```python
class IncidentFeatureProperties(BaseModel):
    incident_id: str
    title: str
    incident_type: str
    status: str
    severity: str
    severity_tier: str          # Mapped AWS tier: "advice" | "watch" | "emergency"
    affected_jurisdiction_ids: list[str]
    participating_organisation_ids: list[str]
    started_at: str             # ISO 8601 datetime string
    pprr_phase: str | None
    incident_level: int

class IncidentFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str                     # incident_id
    geometry: GeoJSONPoint
    properties: IncidentFeatureProperties
```

### GeoJSON FeatureCollection (response envelope)

```python
class IncidentFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[IncidentFeature]
    metadata: IncidentMapMetadata

class IncidentMapMetadata(BaseModel):
    total: int                  # Total matching incidents (with location)
    unmapped_count: int         # Incidents matching filters but missing location
    page: int                   # Current page number (1-based)
    page_size: int              # Items per page
    fetched_at: str             # ISO 8601 timestamp of data retrieval
```

## Severity Domain Value → AWS Tier Mapping

| Domain Value | AWS Tier | Marker Colour | Marker Shape | CSS Token |
|---|---|---|---|---|
| `"advisory"` | Advice | Yellow #FFC107 | Circle | `--ama-aws-advice` |
| `"watch"` | Watch and Act | Orange #FF8C00 | Triangle | `--ama-aws-watch` |
| `"warning"` | Emergency Warning | Red #D32F2F | Diamond | `--ama-aws-emergency` |
| `"emergency"` | Emergency Warning | Red #D32F2F | Diamond | `--ama-aws-emergency` |

**Mapping logic** (applied in API response and frontend):

```python
SEVERITY_TO_AWS_TIER = {
    "advisory": "advice",
    "watch": "watch",
    "warning": "emergency",
    "emergency": "emergency",
}
```

## Filter Status Values

The `/disasters` page displays only operational statuses. The `rehearsal` status is excluded server-side:

| Status Value | Displayed on Map | Note |
|---|---|---|
| `monitoring` | ✅ Yes | Operational |
| `active` | ✅ Yes | Operational |
| `stabilising` | ✅ Yes | Operational |
| `recovery` | ✅ Yes | Operational |
| `closed` | ✅ Yes | Operational |
| `rehearsal` | ❌ No | Excluded server-side per FR-029, Assumption §9 |

## Cosmos DB Query Shape

**Container**: `incidents` in `disaster-hub` database
**Partition key**: To be confirmed (likely `incident_id` or `incident_type`)

### Base query (always applied)

```sql
SELECT * FROM c
WHERE c.status != 'rehearsal'
  AND IS_DEFINED(c.location)
  AND c.location.type = 'Point'
```

### Dynamic filter clauses (applied when parameter provided)

| Filter | SQL Clause | Parameter |
|---|---|---|
| incident_type | `ARRAY_CONTAINS(@types, c.incident_type)` | `@types: str[]` |
| severity | `ARRAY_CONTAINS(@severities, c.severity)` | `@severities: str[]` |
| status | `ARRAY_CONTAINS(@statuses, c.status)` | `@statuses: str[]` |
| pprr_phase | `ARRAY_CONTAINS(@phases, c.pprr_phase)` | `@phases: str[]` |
| year_start | `DateTimePart("yyyy", c.started_at) >= @year_start` | `@year_start: int` |
| year_end | `DateTimePart("yyyy", c.started_at) <= @year_end` | `@year_end: int` |
| keyword | `CONTAINS(LOWER(c.title), LOWER(@keyword))` | `@keyword: str` |

### Pagination

```sql
ORDER BY c.started_at DESC
OFFSET @offset LIMIT @limit
```

### Unmapped count query

```sql
SELECT VALUE COUNT(1) FROM c
WHERE c.status != 'rehearsal'
  AND (NOT IS_DEFINED(c.location) OR c.location IS NULL)
  [+ same dynamic filter clauses]
```

## Indexing Recommendations

For efficient query performance on the incidents container:

```json
{
  "indexingPolicy": {
    "includedPaths": [
      { "path": "/incident_type/?" },
      { "path": "/status/?" },
      { "path": "/severity/?" },
      { "path": "/pprr_phase/?" },
      { "path": "/started_at/?" },
      { "path": "/location/type/?" },
      { "path": "/title/?" }
    ],
    "compositeIndexes": [
      [
        { "path": "/status", "order": "ascending" },
        { "path": "/started_at", "order": "descending" }
      ]
    ]
  }
}
```
