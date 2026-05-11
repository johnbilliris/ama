# Contract: SSE Map Overlay Event Types

**Feature**: 036 — Real Sub-Agent Invocation & Telemetry-Injection Agent
**Spec FRs**: FR-027, FR-028, FR-029, FR-030, FR-032, FR-033, FR-034
**Endpoint**: `GET /api/simulations/{simId}/events` (SSE; existing spec 024 stream extended)

This contract defines the **closed set** of SSE event types emitted by the simulation event stream for map-overlay deltas. Any event type NOT in this list MUST NOT be emitted by the API; the web client MUST ignore unknown event types defensively.

---

## 1. Event Type Taxonomy

```text
SSE event types (this feature only — chat-turn deltas inherit from spec 024)
├── map.overlay.created     ← new overlay layer written to sim tenant
├── map.overlay.updated     ← overlay mutated (geometry, properties, capacity)
├── map.overlay.stale       ← overlay crossed its category freshness window (FR-030)
├── map.overlay.cluster     ← overlay clustered or down-sampled for render (FR-034)
├── map.overlay.removed     ← overlay no longer applicable (e.g. sim ended, signal expired beyond 2× freshness)
└── map.overlay.batch       ← initial-load envelope (page reload / SSE reconnect) — array of `created` events
```

## 2. Layer Type Closed Set (FR-027)

Every emitted event carries `layer_type` from this enum (16 values):

```text
wind-arrow                       weather-derived
hazard-perimeter                 fire-behaviour-derived
evacuation-route                 evacuation-derived
resource-pin                     resource-derived
evac-centre-pin                  evacuation-derived
utility-outage-zone              utility-derived
tc-track-and-cone                weather (TC) derived
road-closure-and-alt-route       transport-derived
vessel-or-aircraft-position      resource-derived (marine / air)
airspace-restriction             transport-derived
maritime-exclusion               transport-derived
hospital-surge                   resource-derived (cascade)
remote-community-access          transport-derived
volunteer-staging                resource-derived
geohazard-zone                   geohazard-derived
flood-polygon                    hydrology-derived
```

## 3. Common Event Envelope

Every map-overlay SSE event uses this envelope:

```text
event: <event_type>
id: <monotonic_event_id>
data: <json_payload>

```

Where `<json_payload>` conforms to:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://platform/schemas/sse-map-overlay-event.schema.json",
  "type": "object",
  "required": ["event_type", "sim_id", "overlay_id", "layer_type", "sim_badge", "visual_modifier", "timestamp"],
  "additionalProperties": false,
  "properties": {
    "event_type": {
      "type": "string",
      "enum": ["map.overlay.created", "map.overlay.updated", "map.overlay.stale", "map.overlay.cluster", "map.overlay.removed", "map.overlay.batch"]
    },
    "sim_id": { "type": "string", "format": "uuid" },
    "overlay_id": { "type": "string", "format": "uuid" },
    "signal_id": { "type": "string", "format": "uuid", "description": "Source synthetic signal" },
    "layer_type": {
      "type": "string",
      "enum": [
        "wind-arrow", "hazard-perimeter", "evacuation-route", "resource-pin", "evac-centre-pin",
        "utility-outage-zone", "tc-track-and-cone", "road-closure-and-alt-route",
        "vessel-or-aircraft-position", "airspace-restriction", "maritime-exclusion",
        "hospital-surge", "remote-community-access", "volunteer-staging",
        "geohazard-zone", "flood-polygon"
      ]
    },
    "geojson_feature": {
      "type": "object",
      "description": "Standard GeoJSON Feature; required for created/updated/batch events; absent on stale/cluster/removed.",
      "properties": {
        "type": { "const": "Feature" },
        "geometry": { "$ref": "https://geojson.org/schema/Geometry.json" },
        "properties": { "$ref": "#/$defs/featureProperties" }
      }
    },
    "sim_badge": { "const": true, "description": "Always true — this stream only emits sim-tenant overlays" },
    "visual_modifier": { "type": "string", "enum": ["striped", "dashed", "badged", "amber-tint"] },
    "thread_id": { "type": "string", "format": "uuid", "description": "Hazard thread the overlay belongs to (FR-052)" },
    "thread_color_index": { "type": "integer", "minimum": 0, "maximum": 4, "description": "0..4 colour-blind-safe palette index" },
    "stale": { "type": "boolean", "default": false },
    "stale_since": { "type": ["string", "null"], "format": "date-time" },
    "cluster_count": { "type": ["integer", "null"], "description": "When event_type=map.overlay.cluster, the number of underlying overlays merged" },
    "label": { "type": ["string", "null"], "description": "Human-readable label (e.g. '80 km/h gust 110')" },
    "timestamp": { "type": "string", "format": "date-time" },
    "trace_id": { "type": "string", "description": "OpenTelemetry trace_id for cross-cascade observability" }
  },
  "$defs": {
    "featureProperties": {
      "type": "object",
      "additionalProperties": true,
      "properties": {
        "signal_id": { "type": "string", "format": "uuid" },
        "layer_type": { "type": "string" },
        "sim_badge": { "const": true },
        "visual_modifier": { "type": "string" },
        "stale": { "type": "boolean" },
        "stale_since": { "type": ["string", "null"] },
        "thread_id": { "type": "string", "format": "uuid" },
        "thread_color_index": { "type": "integer" },
        "category": { "type": "string" },
        "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
        "label": { "type": "string" },
        "cluster_count": { "type": ["integer", "null"] }
      }
    }
  }
}
```

## 4. Event-Type Semantics

### 4.1 `map.overlay.created`

Emitted within ≤ 15 s (hazard / evacuation / resource per FR-028) or ≤ 10 s (weather / geohazard per FR-029) of the underlying signal write. Always carries `geojson_feature`. The web client MUST add the layer to the map.

### 4.2 `map.overlay.updated`

Emitted on every signal mutation (e.g. wind direction inverted, TC category changed, polygon redrawn). The web client MUST replace the existing layer for the same `overlay_id`. `geojson_feature` is the new geometry/properties.

### 4.3 `map.overlay.stale`

Emitted when `now() - signal.timestamp > FRESHNESS_WINDOWS[category]` (per `apps/api/app/config/signal_freshness.py`). The event sets `stale: true` and `stale_since`; `geojson_feature` is omitted (the existing geometry is unchanged). The web client MUST apply the stale visual: `opacity-40` plus a clock-icon `STALE` badge anchored to the overlay centroid (UX cohort §4).

### 4.4 `map.overlay.cluster`

Emitted when overlay capacity exceeds the render budget (FR-034 — currently 50 overlays per layer-type per viewport). `cluster_count` reports how many underlying overlays were merged. The web client renders a `+N more` cluster badge; tap/click expands to show the individual overlays.

### 4.5 `map.overlay.removed`

Emitted when an overlay no longer applies — e.g. simulation ended, signal exceeded 2× freshness window without replacement, or coordinator manually cleared the layer. The web client MUST remove the layer.

### 4.6 `map.overlay.batch`

Emitted on initial connection or SSE reconnect (browser-tab-closed-mid-conversation edge case). Payload contains an array of `map.overlay.created` records spanning the active overlays. The web client MUST replace its overlay state with the batch contents (server is authoritative).

```json
{
  "event_type": "map.overlay.batch",
  "sim_id": "...",
  "overlay_id": "00000000-0000-0000-0000-000000000000",
  "layer_type": "wind-arrow",
  "sim_badge": true,
  "visual_modifier": "striped",
  "timestamp": "...",
  "batch": [
    { "...individual created event payload..." },
    { "...etc..." }
  ]
}
```

The wrapper-level `overlay_id` and `layer_type` on a batch event are sentinel placeholders; only `batch[i]` payloads matter.

## 5. Latency targets

| Layer-type group | SLA (FR-028 / FR-029) | SLO target | Burn-rate alert |
|---|---|---|---|
| Hazard / evacuation / resource (most layer types) | ≤ 15 s p95 | 99 % | p95 > 20 s |
| Weather / geohazard | ≤ 10 s p95 | 99 % | p95 > 15 s |

Measured via Application Insights RUM (client-side: SSE event-received timestamp → DOM update timestamp). Server-side: signal-write timestamp → SSE event emit timestamp logged in Azure Monitor custom metric `simulation_overlay_emit_latency_ms`.

## 6. Order guarantees

- Per `overlay_id`: events are emitted in monotonic `id` order (SSE Last-Event-ID semantics for client reconnect).
- Across `overlay_id`s: ordering follows the underlying signal-pipeline ordering (Event Hubs partition by `simulation_id` guarantees per-sim ordering).
- `map.overlay.batch` is the **first** event after every (re)connect — clients MUST process the batch before any subsequent delta.

## 7. Tenant scoping

- Every emitted event MUST carry a `sim_id` matching the URL path. The API server-side filter rejects subscribers from receiving events for sims they do not have access to (per FR-051: `Simulation.Coordinator` and `Simulation.Observer` roles can read; observers see the same overlay stream as coordinators).
- `sim_badge: true` is invariant on every event — this stream NEVER emits live-tenant overlays. Live-tenant map updates flow on the existing live-tenant SSE stream (spec 020 unchanged).

## 8. Client behaviour notes (FR-030 stale rendering)

- The web client uses CSS filter `opacity-40` for stale overlays + a `StaleBadge` component anchored to the overlay centroid showing a clock icon and `STALE` text label (WCAG 2.1 AA contrast met).
- Tooltip on hover: `Last updated: <timestamp> — <X> minutes ago` derived from `stale_since`.

## 9. SSE event-id and reconnect

- `id:` field on every event is a monotonic per-sim counter. On reconnect, the client SHOULD send `Last-Event-ID: <last_seen_id>`; the server replays missed events from its event log (Cosmos `simulation_audit_entries` derived projection) plus a fresh `map.overlay.batch` to reconcile.

---

*Contract complete 2026-05-08. ≈81 valid tuples after applying §4.6 sentinel-placeholder rules; T-J02 enumerates the exact set.*
