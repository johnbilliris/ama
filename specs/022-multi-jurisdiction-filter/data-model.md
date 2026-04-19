# Data Model: Multi-Jurisdiction Filter for Preparedness Page

**Feature**: 022-multi-jurisdiction-filter | **Date**: 2025-07-20

## Existing Entities (No Changes)

### Jurisdiction

**Source**: `packages/domain/src/domain/models/jurisdiction.py`
**Seed**: `packages/domain/src/domain/seed/jurisdictions_australia.json`

| Field | Type | Description |
|-------|------|-------------|
| `jurisdiction_id` | `str` (PK) | Unique identifier (e.g., "nsw", "vic", "commonwealth") |
| `name` | `str` | Human-readable name (e.g., "New South Wales") |
| `level` | `Literal["commonwealth", "state", "territory", "regional", "local"]` | Administrative level |
| `parent_jurisdiction_id` | `str \| None` | Parent jurisdiction (states/territories → "commonwealth") |
| `policy_set_id` | `str` | Associated policy set identifier |
| `geospatial_boundary` | `dict[str, Any]` | GeoJSON polygon boundary |
| `status` | `Literal["active", "inactive"]` | Active/inactive flag |

**Filtering role**: The jurisdiction selector displays jurisdictions where `status == "active"`. The nine Australian jurisdictions (1 commonwealth, 6 states, 2 territories) form the selectable set.

**Validation rules**:
- `jurisdiction_id` is unique across the dataset
- `name` is non-empty
- `level` determines grouping in the selector (commonwealth displayed first, then states, then territories)

### Organisation

**Source**: `packages/domain/src/domain/models/organisation.py`
**Seed**: `packages/domain/src/domain/seed/organisations_australia.json`

| Field | Type | Description |
|-------|------|-------------|
| `organisation_id` | `str` (PK) | Unique identifier (e.g., "ses-nsw", "nema") |
| `name` | `str` | Organisation name |
| `category` | `Literal[...]` | Category (commonwealth, state, emergency_service, etc.) |
| `jurisdiction_ids` | `list[str]` | Jurisdictions this organisation belongs to |
| `operating_role` | `str` | Operational role description |
| `authority_level` | `str` | Authority level |
| `contact_channels` | `list[dict[str, str]]` | Contact methods |
| `participation_conditions` | `list[str]` | Conditions for participation |
| `status` | `Literal["active", "inactive", "planned"]` | Status |

**Filtering logic**: An organisation matches a jurisdiction selection if **any** of its `jurisdiction_ids` overlaps with the selected set (OR logic, per spec assumptions). Deduplication is inherent — each organisation appears once regardless of how many selected jurisdictions it matches.

**Validation rules**:
- `jurisdiction_ids` must contain at least one valid jurisdiction_id
- Filter: `any(jid in selected_ids for jid in org.jurisdiction_ids)`

### OperatingFramework

**Source**: `packages/domain/src/domain/models/operating_framework.py`
**Seed**: `packages/domain/src/domain/seed/frameworks_australia.json`

| Field | Type | Description |
|-------|------|-------------|
| `framework_id` | `str` (PK) | Unique identifier (e.g., "aiims-national") |
| `name` | `str` | Framework name |
| `framework_type` | `Literal[...]` | Type (aiims, agency_specific, etc.) |
| `principles` | `list[str]` | Guiding principles |
| `control_model` | `str` | Control model description |
| `approval_rules` | `list[dict[str, Any]]` | Approval rule definitions |
| `escalation_rules` | `list[dict[str, Any]]` | Escalation rule definitions |
| `span_of_control_guidance` | `str` | Span of control guidance text |
| `status` | `Literal["active", "retired", "draft"]` | Status |

**Filtering logic**: OperatingFramework has **no direct jurisdiction field**. Jurisdiction applicability is determined via FrameworkAssignment junction records (per spec 018). A framework matches a jurisdiction selection if **any** FrameworkAssignment links it to one of the selected jurisdictions.

### FrameworkAssignment (Junction Entity)

**Source**: `packages/domain/src/domain/models/framework_assignment.py`

| Field | Type | Description |
|-------|------|-------------|
| `assignment_id` | `str` (PK) | Unique identifier |
| `framework_id` | `str` (FK → OperatingFramework) | Referenced framework |
| `jurisdiction_id` | `str \| None` (FK → Jurisdiction) | Referenced jurisdiction |
| `organisation_id` | `str \| None` (FK → Organisation) | Referenced organisation (optional) |
| `effective_from` | `datetime` | Assignment start date |
| `effective_to` | `datetime \| None` | Assignment end date (None = current) |
| `overrides` | `dict[str, Any]` | Override parameters |

**Filtering logic**: For jurisdiction-based framework filtering:
```
SELECT DISTINCT framework
FROM FrameworkAssignment fa
JOIN OperatingFramework fw ON fa.framework_id = fw.framework_id
WHERE fa.jurisdiction_id IN (selected_jurisdiction_ids)
  AND fa.effective_to IS NULL  -- current assignments only
```

## New Seed Data

### FrameworkAssignment Seed File (NEW)

**Path**: `packages/domain/src/domain/seed/framework_assignments_australia.json`

This seed file provides the junction records linking frameworks to jurisdictions. Per research R-006, the current codebase synthesises these assignments on-the-fly but has no actual seed data, making framework filtering impossible.

**Structure**:
```json
[
  {
    "assignment_id": "assign-aiims-national-commonwealth",
    "framework_id": "aiims-national",
    "jurisdiction_id": "commonwealth",
    "organisation_id": null,
    "effective_from": "2024-01-01T00:00:00Z",
    "effective_to": null,
    "overrides": {}
  },
  {
    "assignment_id": "assign-aiims-national-nsw",
    "framework_id": "aiims-national",
    "jurisdiction_id": "nsw",
    "organisation_id": null,
    "effective_from": "2024-01-01T00:00:00Z",
    "effective_to": null,
    "overrides": {}
  }
]
```

**Population rules**:
- National frameworks (e.g., "aiims-national") should be assigned to ALL nine jurisdictions
- State-specific frameworks (e.g., "nsw-flood-communications") should be assigned to their respective jurisdiction only
- The `assignment_id` follows the pattern: `assign-{framework_id}-{jurisdiction_id}`

**Bootstrap update**: `bootstrap_seed_data()` in `packages/domain/src/domain/seed/bootstrap.py` must be updated to load this new file:
```python
"framework_assignments": load_seed_file(seed_root / "framework_assignments_australia.json"),
```

## Entity Relationships

```
┌──────────────┐         ┌───────────────────────┐         ┌──────────────────────┐
│ Jurisdiction  │◄────────│  FrameworkAssignment   │────────►│  OperatingFramework  │
│              │  1:N     │  (junction)            │  N:1    │                      │
│ jurisdiction_│         │ jurisdiction_id (FK)   │         │ framework_id (PK)    │
│ _id (PK)     │         │ framework_id (FK)      │         │ name                 │
│ name         │         │ assignment_id (PK)     │         │ framework_type       │
│ level        │         └───────────────────────┘         │ status               │
└──────┬───────┘                                           └──────────────────────┘
       │
       │ 1:N (via jurisdiction_ids list)
       │
┌──────┴───────┐
│ Organisation │
│              │
│ organisation_│
│ _id (PK)     │
│ name         │
│ jurisdiction_│
│ _ids (list)  │
│ status       │
└──────────────┘
```

**Relationship summary**:
- **Jurisdiction → Organisation**: One-to-many via Organisation.jurisdiction_ids list (an organisation can belong to multiple jurisdictions)
- **Jurisdiction → OperatingFramework**: Many-to-many via FrameworkAssignment junction table
- **FrameworkAssignment → Jurisdiction**: Many-to-one (each assignment links to exactly one jurisdiction)
- **FrameworkAssignment → OperatingFramework**: Many-to-one (each assignment links to exactly one framework)

## State Transitions

### Jurisdiction Selection State Machine

```
┌──────────────────┐
│  EMPTY           │  Initial state: no jurisdictions selected
│  (no params URL) │  Display: empty state prompt
│  Replay: disabled│
└────────┬─────────┘
         │ User selects jurisdiction(s)
         ▼
┌──────────────────┐
│  SELECTED        │  One or more jurisdictions selected
│  (?jurisdictions=│  Display: loading → catalogs
│   nsw,vic)       │  Replay: enabled
│  Replay: enabled │
└────────┬─────────┘
         │ User changes selection
         ▼
┌──────────────────┐
│  LOADING         │  API calls in flight (300ms debounce)
│  Display: loading│  Display: inline loading per catalog
│  indicators      │  Previous results cleared (FR-013)
└────────┬─────────┘
         │ API responds
         ▼
┌──────────────────┐       ┌──────────────────┐
│  LOADED          │       │  ERROR           │
│  Catalogs display│       │  Inline error per│
│  filtered data   │       │  catalog + retry │
└──────────────────┘       └──────────────────┘
```

### Replay Staleness State

```
┌──────────────────┐
│  NO REPLAY       │  Initial: no replay run yet
└────────┬─────────┘
         │ User clicks "Run rehearsal replay"
         ▼
┌──────────────────┐
│  REPLAY CURRENT  │  Replay results match current jurisdictions
│  replayJurisdic- │  Display: findings + gaps normally
│  tions == current│
└────────┬─────────┘
         │ User changes jurisdiction selection
         ▼
┌──────────────────┐
│  REPLAY STALE    │  Replay results for different jurisdictions
│  replayJurisdic- │  Display: notice + cleared results
│  tions != current│  Action: user must re-run replay
└──────────────────┘
```

## TypeScript Interfaces (Frontend)

### JurisdictionSummary (NEW)

Used by the jurisdiction selector and API client:

```typescript
export interface JurisdictionSummary {
  jurisdiction_id: string;
  name: string;
  level: "commonwealth" | "state" | "territory";
}
```

This is a projection of the full Jurisdiction model — only the fields needed for the selector UI.

### PreparednessOrganisation (EXISTING — no changes)

```typescript
export interface PreparednessOrganisation {
  organisation_id: string;
  name: string;
  category: string;
  jurisdiction_ids: string[];
  operating_role: string;
  authority_level: string;
  status: string;
}
```

### PreparednessFramework (EXISTING — no changes)

```typescript
export interface PreparednessFramework {
  framework_id: string;
  name: string;
  framework_type: string;
  span_of_control_guidance: string;
  status: string;
}
```
