# Research: Disaster Mapper UI

**Feature**: 020-disaster-mapper-ui
**Date**: 2025-07-17
**Status**: Complete — all unknowns resolved

---

## R-001: Azure Maps npm Integration with React 19 / Next.js 15

**Decision**: Use `azure-maps-control` v3.x as a client-side-only component via Next.js `dynamic()` with `{ ssr: false }`.

**Rationale**: The `azure-maps-control` package is a DOM-dependent imperative library that cannot render server-side. React integration requires `useRef` for the map container + `useEffect` for map initialisation/disposal. Next.js 15 App Router supports this via `"use client"` directive combined with dynamic import to skip SSR. This is the standard pattern recommended by Azure Maps documentation and matches how the project handles other client-only components.

**Key findings**:

- **Package**: `azure-maps-control` (npm) — includes TypeScript typings in-package (no separate `@types/` needed)
- **CSS import**: `azure-maps-control/dist/atlas.min.css` must be imported in the client component
- **Map initialisation**: `new atlas.Map(containerRef, { center: [lon, lat], zoom, authOptions })` inside `useEffect`
- **Cleanup**: `map.dispose()` in the effect cleanup function to prevent memory leaks
- **SSR guard**: Use `dynamic(() => import('./disaster-map'), { ssr: false })` in the page component
- **Authentication**: Subscription key via `NEXT_PUBLIC_AZURE_MAPS_KEY` env var for initial dev; Azure AD auth for production (via `authType: "aad"`)

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| `react-azure-maps` wrapper | Unmaintained, lags behind azure-maps-control releases, adds unnecessary abstraction |
| Mapbox GL JS | Not Azure-native (constitution §VIII); data sovereignty concerns for tile serving |
| Google Maps | Not Azure-native; tile data served from Google CDN outside Australia |
| Leaflet + Azure Maps tiles | Extra abstraction layer; loses Azure Maps' built-in clustering and layer management |

---

## R-002: Azure Maps Marker Customisation for AWS Severity Tiers

**Decision**: Use Azure Maps `SymbolLayer` with custom HTML markers or `HtmlMarker` for severity-coded shapes (circle/triangle/diamond). Alternatively, use SVG icon expressions on the `SymbolLayer` with `image` property pointing to custom icons added via `map.imageSprite.add()`.

**Rationale**: The spec requires three distinct shapes (circle, triangle, diamond) with three distinct colours (yellow, orange, red) per WCAG 2.1 AA accessibility requirements. Azure Maps' built-in pin icons only offer colour variation, not shape variation. Custom SVG markers provide both shape and colour differentiation. Using `map.imageSprite.add()` with named SVG data URIs keeps rendering within the SymbolLayer pipeline (better performance with clustering than HtmlMarker).

**Key findings**:

- **Approach**: Register three custom SVG icons via `map.imageSprite.add('marker-advice', svgDataUri)`, etc.
- **Layer expression**: Use a data-driven `image` expression: `['match', ['get', 'severityTier'], 'advice', 'marker-advice', 'watch', 'marker-watch', 'emergency', 'marker-emergency', 'marker-default']`
- **Colour tokens**: `--ama-aws-advice: #FFC107`, `--ama-aws-watch: #FF8C00`, `--ama-aws-emergency: #D32F2F`
- **Contrast**: All three colours meet 3:1 minimum contrast against Azure Maps' default road tile background (#E8E0D8 light grey)

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| BubbleLayer with colour only | Fails WCAG — must have shape differentiation beyond colour |
| HtmlMarker per incident | Performance degrades beyond ~200 markers; not compatible with clustering |
| Image sprite from PNG files | SVG data URIs are resolution-independent and smaller; better for HiDPI |

---

## R-003: Azure Maps Clustering Configuration

**Decision**: Use `atlas.source.DataSource` with `cluster: true` and `clusterRadius: 60` (per FR-005).

**Rationale**: Azure Maps' built-in clustering operates at the DataSource level — no separate `ClusteredDataSource` class exists. The `DataSource` constructor accepts clustering options directly. Cluster features automatically gain `point_count`, `cluster_id` properties. Clicking a cluster uses `getClusterExpansionZoom()` to determine the appropriate zoom level.

**Key findings**:

- **Configuration**: `new atlas.source.DataSource(undefined, { cluster: true, clusterRadius: 60, clusterMaxZoom: 14 })`
- **Cluster layer**: `BubbleLayer` with filter `["has", "point_count"]` for cluster circles showing count
- **Symbol layer**: `SymbolLayer` with filter `["!", ["has", "point_count"]]` for individual markers
- **Cluster count labels**: Separate `SymbolLayer` with `textOptions: { textField: ["get", "point_count_abbreviated"] }` rendered on top of cluster bubbles
- **Click-to-expand**: `map.events.add("click", clusterLayer, ...)` → `ds.getClusterExpansionZoom(clusterId)` → `map.setCamera({ center, zoom })`
- **Performance**: Built-in clustering handles 10,000+ features efficiently on the client side

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| Supercluster.js (separate library) | Redundant — Azure Maps has built-in clustering with identical algorithm |
| Server-side clustering | Adds latency per zoom/pan interaction; built-in client clustering is sufficient for <10K points |
| No clustering (just hide at zoom levels) | Poor UX with 500+ overlapping markers; spec explicitly requires clustering (FR-005) |

---

## R-004: Azure Maps Bicep Resource Provisioning

**Decision**: New module `infra/modules/azure-maps.bicep` deploying `Microsoft.Maps/accounts` with Gen2 SKU, locked to `australiaeast`, with `disableLocalAuth: true` for Entra-only auth.

**Rationale**: Azure Maps Gen2 is the current-generation SKU replacing Gen1 S0/S1. Disabling local auth enforces Azure AD-based data access, aligning with security best practices. The module follows the existing pattern from `monitoring.bicep` (params: `location`, `envPrefix`, `tags`; outputs: name and ID). CORS is configured to allow the web frontend origin.

**Key findings**:

- **Resource type**: `Microsoft.Maps/accounts@2024-07-01-preview` (stable preview)
- **SKU**: `{ name: 'G2' }` with `kind: 'Gen2'`
- **Data sovereignty**: `@allowed(['australiaeast'])` on location parameter enforces Australia East deployment
- **Auth**: `disableLocalAuth: true` — use RBAC with `Azure Maps Data Reader` role for data plane access
- **Integration**: Module wired into `infra/main.bicep` alongside existing monitoring module; subscription key passed as Container App env var or use managed identity + RBAC
- **CORS**: Configure `properties.cors.corsRules` with the web app origin

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| Gen1 S0 | Deprecated tier; Gen2 is recommended for new deployments |
| Subscription key auth (local auth enabled) | Less secure; constitution requires auditability which Entra auth provides per-user |
| Terraform module | Project uses Bicep (constitution §VIII: "Bicep preferred") |

---

## R-005: FastAPI GeoJSON Endpoint Design

**Decision**: New endpoint `GET /api/v1/incidents/map` in `apps/api/app/api/routes/incidents_map.py` returning a GeoJSON FeatureCollection. Uses new repository class `IncidentMapRepository` for Cosmos DB queries with dynamic filter composition.

**Rationale**: Creating a separate router file (not extending existing `incidents.py`) follows the project's single-responsibility pattern. The existing incidents router handles dashboard, declare, and resolve operations — the map endpoint has a fundamentally different query shape (geospatial, multi-filter, paginated, GeoJSON response). A dedicated repository class follows the existing `SignalRepository` pattern.

**Key findings**:

- **Router pattern**: New `incidents_map.py` with `router = APIRouter(prefix="/incidents", tags=["incidents"])` — same prefix as existing incidents router, merged via `api_router.include_router()`
- **Query parameters**: `type`, `severity`, `status`, `pprr_phase`, `keyword`, `year_start`, `year_end`, `page` (default 1), `page_size` (default 200)
- **Exclusion**: `c.status != 'rehearsal'` always applied server-side (FR-029, Assumption §9)
- **Location filter**: `IS_DEFINED(c.location) AND c.location.type = 'Point'` — only return mappable incidents
- **Cosmos query**: Dynamic WHERE clause composition with `@param` parameters (matches `signal_repository.py` pattern)
- **Response**: Pydantic model `GeoJSONFeatureCollection` with `features`, `total`, `page`, `page_size` fields
- **Unmapped count**: Separate count query without the location filter, minus total with filter = unmapped count (returned in response metadata)

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| Extend existing `/incidents/{id}/dashboard` | Different query shape; violates single-responsibility |
| Client-side filtering only | Spec mandates server-side filtering (FR-029); poor performance with large datasets |
| GraphQL endpoint | Project uses REST/FastAPI exclusively; GraphQL adds unnecessary complexity |
| Return raw JSON, convert to GeoJSON client-side | Constitution §IV requires GeoJSON standard; server-side conversion is cleaner |

---

## R-006: Incident Domain Model Extension

**Decision**: Add `location: dict[str, Any] | None = None` field to the `Incident` Pydantic model in `packages/domain/src/domain/models/incident.py`. The field stores a GeoJSON Point geometry object.

**Rationale**: Using `dict[str, Any]` matches the existing pattern in the domain package (e.g., `Jurisdiction.geospatial_boundary` is `dict[str, Any]`). The field is optional (`None` default) since not all existing incidents have location data (Assumption §1). GeoJSON Point format (`{"type": "Point", "coordinates": [lon, lat]}`) per RFC 7946, as mandated by constitution §IV.

**Key findings**:

- **Field definition**: `location: dict[str, Any] | None = None`
- **Validation**: GeoJSON structure validated at the API response layer (Pydantic models in `geojson.py`), not at the domain model layer — keeps the domain model lean
- **Migration**: No database migration needed — Cosmos DB is schema-less; field is optional and new documents include it
- **Existing data**: Incidents without location remain valid; FR-030 handles disclosure of unmapped count

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| Separate `IncidentLocation` model/entity | Over-engineering for a single optional field; existing `Jurisdiction` uses inline dict |
| Flat `latitude`/`longitude` fields | Not GeoJSON compliant; constitution §IV mandates GeoJSON standard |
| Strict `GeoJSONPoint` Pydantic submodel at domain level | Domain models in this project use `dict[str, Any]` for geo data (see `Jurisdiction.geospatial_boundary`) |

---

## R-007: Frontend State Management for Filters

**Decision**: URL query parameters for filter state persistence, managed via a custom `useDisasterMapFilters` React hook that syncs with `next/navigation` `useSearchParams`.

**Rationale**: Spec explicitly requires URL-based filter persistence for shareability and bookmarkability (Clarification session 2026-04-13, FR edge case §7). Using `useSearchParams` from Next.js 15 App Router is the idiomatic approach. The hook encapsulates parsing, validation, default values, and URL update logic.

**Key findings**:

- **URL format**: `/disasters?type=bushfire,flood&severity=advisory&status=active&pprr_phase=response&keyword=nsw&year_start=2020&year_end=2024`
- **Multi-value encoding**: Comma-separated within a single parameter (e.g., `type=bushfire,flood`)
- **Defaults**: All filters unset = show all incidents (no server-side filter applied)
- **Debouncing**: 300ms debounce on keyword search input before triggering API call; immediate trigger for checkbox/dropdown filter changes
- **Browser navigation**: `useSearchParams` integrates with browser back/forward history automatically

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| React state only (no URL sync) | Not bookmarkable/shareable — spec explicitly requires URL persistence |
| localStorage/sessionStorage | Not shareable via link; breaks the spec requirement |
| Zustand/Redux global store | Over-engineering; URL params + a hook is sufficient for this scope |

---

## R-008: Telemetry Integration

**Decision**: Use the existing `@azure/monitor-opentelemetry` package already in `apps/web/package.json` for frontend metrics. Use FastAPI middleware and structured logging for backend metrics to Application Insights.

**Rationale**: The web app already depends on `@azure/monitor-opentelemetry` (version ^1.7.0). Adding custom metrics via `meter.createHistogram()` and `meter.createCounter()` follows OpenTelemetry conventions. Backend telemetry uses the existing Application Insights integration from the monitoring Bicep module.

**Key findings**:

- **Frontend metrics** (via OpenTelemetry meter):
  - `disaster_mapper.page_load_ms` — `performance.now()` delta from page mount to map `ready` event
  - `disaster_mapper.filter_apply_ms` — delta from filter change to map re-render completion
  - `disaster_mapper.map_render_ms` — delta from data receipt to marker render completion
  - `disaster_mapper.incidents_displayed` — gauge updated on each render
- **Backend metrics** (via FastAPI middleware / structured logging):
  - `disaster_mapper.api_error_rate` — tracked via response status code (5xx count / total count)
- **Existing infra**: Application Insights connection string from `monitoring.bicep` module output

**Alternatives considered**:

| Alternative | Rejected Because |
|---|---|
| Custom Application Insights SDK (non-OTel) | Project already uses OpenTelemetry; mixing SDKs adds confusion |
| Console.log + Log Analytics agent | Not structured; doesn't produce named metrics queryable in Log Analytics |
| Third-party analytics (Datadog, etc.) | Not Azure-native; constitution §VIII |
