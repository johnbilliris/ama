# Contract: Telemetry-Injection LLM (Azure OpenAI `json_schema` Strict Mode)

**Feature**: 036 — Real Sub-Agent Invocation & Telemetry-Injection Agent
**Spec FRs**: FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-018
**Owning agent**: `apps/agents/simulation_telemetry_injection/` (NEW Python sibling module — bundled in existing `apps/agents` Container App per 3-project cap)
**LLM**: Azure OpenAI `gpt-4o-mini`, AU East preferred → eastus2 fallback (Foundry carve-out registered)

This contract pins the request shape, the strict `response_format` schema, the degraded fallback path, and the Pydantic v2 validator the agent uses to convert free-text coordinator chat input into typed synthetic signals.

---

## 1. Agent Surface (HTTP)

```text
POST {AGENTS_BASE_URL}/simulation-telemetry-injection/invoke
Authorization: Bearer <managed-identity-jwt>
Content-Type: application/json
traceparent: 00-<trace-id>-<span-id>-01

{
  "tenant_id": "sim-tenant-uuid",
  "chat_text": "Wind has just shifted to NW at 80 km/h",
  "viewport_hint": { "centroid_lat": -33.86, "centroid_lng": 151.21, "client_jurisdiction": "NSW" },
  "active_threads": [
    { "thread_id": "...", "hazard_class": "fire", "jurisdiction": "NSW", "thread_color_index": 0 },
    { "thread_id": "...", "hazard_class": "weather", "jurisdiction": "NSW", "thread_color_index": 1 }
  ],
  "current_sim_clock": "2026-11-08T03:14:00Z",
  "correlation_id": "uuid-from-controller"
}

→ 200 OK
{
  "injection_correlation_id": "...",
  "signals": [
    {
      "signal_id": "...",
      "category": "weather",
      "confidence": "high",
      "parameters": { "wind_speed_kmh": 80, "wind_direction_deg": 315, "gust_speed_kmh": null },
      "gps": null,
      "contradicts": null,
      "model_deployment": "gpt-4o-mini-australiaeast",
      "prompt_hash": "abc123…"
    }
  ],
  "refusals": [],
  "unparseable_text": null,
  "degraded_path": false
}
```

Refusals come back inline:

```json
{
  "injection_correlation_id": "...",
  "signals": [],
  "refusals": [
    {
      "reason": "life_safety_low_confidence",
      "parsed_category": "fire-behaviour",
      "inferred_confidence": "low",
      "clarification_question": "I couldn't confidently parse fire-behaviour spotting from that input. Could you rephrase with explicit distance and bearing? (e.g. 'spotting 2 km NE at 1430')"
    }
  ],
  "unparseable_text": "the embers are jumping the road",
  "degraded_path": false
}
```

---

## 2. Pre-LLM Pipeline (server-side, BEFORE the LLM call)

The agent runs these steps in order; if any rejects, the LLM is **not** invoked:

1. **Length & rate gate**: input ≤ 4000 chars; per-user attempt-rate < 60/min (FR-009 circuit-breaker).
2. **Azure AI Content Safety**: Prompt Shield (jailbreak detection) + PII detector. Any HIGH-severity hit → return refusal with `reason: pii_detected` or `reason: malformed_input`.
3. **Rule-based PII scrubber** (defence-in-depth): regex over `\b\d{9,}\b` (Medicare-like), `\b04\d{8}\b` (AU mobile), `[\w\.-]+@[\w\.-]+` (email). Any hit → refusal.
4. **Real-world action detector**: regex over verbs like `dispatch`, `notify next of kin`, `call 000`, `text the public`, `publish` etc. that indicate a request for live-tenant action. Any hit → refusal `reason: real_world_action_request`.

Only after all 4 pass does the agent invoke the LLM.

---

## 3. LLM `response_format` (Strict JSON Schema)

The agent invokes Azure OpenAI Chat Completions (`gpt-4o-mini`, deployment name `gpt-4o-mini-au-east` or `gpt-4o-mini-eastus2-carve-out`) with:

```python
response = await aoai.chat.completions.create(
    model="gpt-4o-mini-au-east",  # or carve-out fallback
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # see §6
        {"role": "user", "content": rendered_user_payload},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "synthetic_signal_batch",
            "strict": True,                              # MANDATORY — refuses non-conforming output
            "schema": SIGNAL_BATCH_SCHEMA,               # see §4
        }
    },
    temperature=0,
    seed=42,                                             # determinism for SC-011
)
```

`strict: True` is **mandatory** — Azure OpenAI guarantees the returned text parses as the schema; any non-conforming output is refused at the API layer rather than reaching the agent.

---

## 4. JSON Schema (signal-batch — `SIGNAL_BATCH_SCHEMA`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://platform/schemas/synthetic-signal-batch.schema.json",
  "title": "Synthetic Signal Batch",
  "type": "object",
  "additionalProperties": false,
  "required": ["signals", "refusals", "unparseable_text"],
  "properties": {
    "signals": {
      "type": "array",
      "items": { "$ref": "#/$defs/signal" }
    },
    "refusals": {
      "type": "array",
      "items": { "$ref": "#/$defs/refusal" }
    },
    "unparseable_text": {
      "type": ["string", "null"],
      "description": "The leftover free-text the LLM could not classify"
    }
  },
  "$defs": {
    "signal": {
      "type": "object",
      "additionalProperties": false,
      "required": ["category", "confidence", "parameters", "gps", "contradicts"],
      "properties": {
        "category": {
          "type": "string",
          "enum": [
            "weather",
            "fire-behaviour",
            "hydrology",
            "geohazard",
            "utility",
            "transport",
            "evacuation",
            "resource",
            "comms-channel-state"
          ]
        },
        "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
        "parameters": { "$ref": "#/$defs/parameters" },
        "gps": {
          "type": ["object", "null"],
          "additionalProperties": false,
          "required": ["lat", "lng"],
          "properties": {
            "lat": { "type": "number", "minimum": -90, "maximum": 90 },
            "lng": { "type": "number", "minimum": -180, "maximum": 180 }
          }
        },
        "contradicts": {
          "type": ["string", "null"],
          "description": "signal_id of an existing sim-tenant signal that this one contradicts (FR-014)"
        }
      }
    },
    "parameters": {
      "description": "Typed parameters; oneOf per category. Fields not in the chosen variant are absent.",
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "wind_speed_kmh": { "type": ["number", "null"], "minimum": 0, "maximum": 400 },
        "wind_direction_deg": { "type": ["number", "null"], "minimum": 0, "maximum": 360 },
        "gust_speed_kmh": { "type": ["number", "null"], "minimum": 0, "maximum": 500 },
        "rainfall_mm_hr": { "type": ["number", "null"], "minimum": 0, "maximum": 1000 },
        "tc_category": { "type": ["integer", "null"], "minimum": 1, "maximum": 5 },
        "fire_intensity_kw_m": { "type": ["number", "null"], "minimum": 0 },
        "fire_perimeter_geojson": { "type": ["object", "null"], "description": "GeoJSON Polygon" },
        "spotting_distance_km": { "type": ["number", "null"], "minimum": 0, "maximum": 50 },
        "spotting_bearing_deg": { "type": ["number", "null"], "minimum": 0, "maximum": 360 },
        "river_height_m": { "type": ["number", "null"] },
        "flood_polygon_geojson": { "type": ["object", "null"] },
        "geohazard_type": { "type": ["string", "null"], "enum": [null, "earthquake", "tsunami_inundation", "landslide", "volcanic_ashfall"] },
        "shake_mmi": { "type": ["integer", "null"], "minimum": 1, "maximum": 12 },
        "outage_polygon_geojson": { "type": ["object", "null"] },
        "outage_kind": { "type": ["string", "null"], "enum": [null, "power", "water", "telco_voice", "telco_data", "fuel"] },
        "transport_kind": { "type": ["string", "null"], "enum": [null, "road_closure", "airspace_restriction", "maritime_exclusion"] },
        "transport_geometry_geojson": { "type": ["object", "null"] },
        "evacuation_kind": { "type": ["string", "null"], "enum": [null, "route_closed", "centre_capacity_change", "centre_amenity"] },
        "centre_capacity_pct": { "type": ["number", "null"], "minimum": 0, "maximum": 100 },
        "resource_kind": { "type": ["string", "null"], "enum": [null, "asset_status", "personnel_count", "fuel_status", "medical_pack", "hospital_bed_capacity"] },
        "resource_count": { "type": ["integer", "null"] },
        "comms_channel": { "type": ["string", "null"], "enum": [null, "radio_VHF", "radio_HF", "telco_voice", "telco_data", "satellite", "messaging_app"] },
        "comms_state": { "type": ["string", "null"], "enum": [null, "operational", "degraded", "offline"] }
      }
    },
    "refusal": {
      "type": "object",
      "additionalProperties": false,
      "required": ["reason"],
      "properties": {
        "reason": {
          "type": "string",
          "enum": [
            "life_safety_low_confidence",
            "missing_provenance",
            "unknown_category",
            "malformed_input"
          ]
        },
        "parsed_category": { "type": ["string", "null"] },
        "inferred_confidence": { "type": ["string", "null"], "enum": [null, "high", "medium", "low"] },
        "clarification_question": { "type": "string" }
      }
    }
  }
}
```

**Strict-mode constraints** (Azure OpenAI requirements for `strict: true`):

- All `properties` are listed in `required` (use nullable types instead of optional fields).
- `additionalProperties: false` everywhere.
- `enum` types are closed.

---

## 5. Pydantic v2 validator (post-LLM)

The agent re-validates the LLM output via Pydantic v2 (defence-in-depth — `strict: true` is rare but not infallible across Azure OpenAI versions):

```python
# apps/agents/simulation_telemetry_injection/schemas.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal

Category = Literal[
    "weather", "fire-behaviour", "hydrology", "geohazard", "utility",
    "transport", "evacuation", "resource", "comms-channel-state",
]
Confidence = Literal["high", "medium", "low"]

class GpsPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

class SignalParameters(BaseModel):
    wind_speed_kmh: float | None = Field(default=None, ge=0, le=400)
    wind_direction_deg: float | None = Field(default=None, ge=0, le=360)
    gust_speed_kmh: float | None = Field(default=None, ge=0, le=500)
    rainfall_mm_hr: float | None = Field(default=None, ge=0, le=1000)
    tc_category: int | None = Field(default=None, ge=1, le=5)
    fire_intensity_kw_m: float | None = Field(default=None, ge=0)
    fire_perimeter_geojson: dict | None = None
    spotting_distance_km: float | None = Field(default=None, ge=0, le=50)
    spotting_bearing_deg: float | None = Field(default=None, ge=0, le=360)
    river_height_m: float | None = None
    flood_polygon_geojson: dict | None = None
    geohazard_type: Literal["earthquake","tsunami_inundation","landslide","volcanic_ashfall"] | None = None
    shake_mmi: int | None = Field(default=None, ge=1, le=12)
    outage_polygon_geojson: dict | None = None
    outage_kind: Literal["power","water","telco_voice","telco_data","fuel"] | None = None
    transport_kind: Literal["road_closure","airspace_restriction","maritime_exclusion"] | None = None
    transport_geometry_geojson: dict | None = None
    evacuation_kind: Literal["route_closed","centre_capacity_change","centre_amenity"] | None = None
    centre_capacity_pct: float | None = Field(default=None, ge=0, le=100)
    resource_kind: Literal["asset_status","personnel_count","fuel_status","medical_pack","hospital_bed_capacity"] | None = None
    resource_count: int | None = None
    comms_channel: Literal["radio_VHF","radio_HF","telco_voice","telco_data","satellite","messaging_app"] | None = None
    comms_state: Literal["operational","degraded","offline"] | None = None

class SyntheticSignal(BaseModel):
    category: Category
    confidence: Confidence
    parameters: SignalParameters
    gps: GpsPoint | None = None
    contradicts: str | None = None

    @model_validator(mode="after")
    def _validate_per_category_required_fields(self):
        # FR-013: per-category required-field validation
        match self.category:
            case "weather":
                if self.parameters.wind_speed_kmh is None and self.parameters.rainfall_mm_hr is None and self.parameters.tc_category is None:
                    raise ValueError("weather signal must have at least one of wind_speed_kmh, rainfall_mm_hr, tc_category")
            case "fire-behaviour":
                if self.parameters.fire_intensity_kw_m is None and self.parameters.fire_perimeter_geojson is None and self.parameters.spotting_distance_km is None:
                    raise ValueError("fire-behaviour signal must have at least one of fire_intensity_kw_m, fire_perimeter_geojson, or spotting fields")
            # ... 7 more category cases
        return self

class Refusal(BaseModel):
    reason: Literal["life_safety_low_confidence", "missing_provenance", "unknown_category", "malformed_input"]
    parsed_category: str | None = None
    inferred_confidence: Confidence | None = None
    clarification_question: str

class SyntheticSignalBatch(BaseModel):
    signals: list[SyntheticSignal]
    refusals: list[Refusal]
    unparseable_text: str | None = None
```

If Pydantic raises `ValidationError`, the agent writes `injection.refused` audit with `reason: malformed_input` and returns the refusal envelope.

---

## 6. System Prompt

The system prompt is canonical, version-pinned, and hashed with the user payload to produce `prompt_hash` (FR-060). Pinned in `apps/agents/simulation_telemetry_injection/prompt.md`. Excerpt:

```text
You are the **simulation-telemetry-injection** agent. You convert free-text coordinator
chat input into typed synthetic signals for an emergency-management exercise. You NEVER
take real-world action. Your output ALWAYS conforms to the JSON schema named
`synthetic_signal_batch`.

Rules:
1. Pick the BEST-FIT category from {weather, fire-behaviour, hydrology, geohazard,
   utility, transport, evacuation, resource, comms-channel-state}. If you cannot match
   any category with at least medium confidence, emit a refusal with reason
   "unknown_category".
2. Confidence levels:
   - high: the input contains an explicit numeric or named parameter.
   - medium: the input describes a clear qualitative state.
   - low: hedged or descriptive. **For life-safety categories** (fire-behaviour,
     hydrology, geohazard with shake_mmi ≥ 5), `low` confidence MUST emit a refusal
     with reason "life_safety_low_confidence" and a clarification_question that asks
     for explicit numbers/bearings.
3. If the input names a real audience or commands a real-world action, refuse with
   reason "missing_provenance" — sub-agent invocations only.
4. If the input contradicts an active sim-tenant signal (provided to you in the user
   payload as `active_signals`), set `contradicts` to that signal_id; do NOT delete
   the prior signal — the platform handles supersession.
5. Use the `viewport_hint` only as a tie-breaker for jurisdiction; the platform
   re-runs the centroid → jurisdiction lookup server-side.
6. Output: SyntheticSignalBatch ONLY. No prose. No markdown.
```

---

## 7. Degraded fallback path

If the LLM call fails (Azure OpenAI 429 exhausted, network partition, deployment unavailable), the agent falls back to a rule-based regex extractor (`apps/agents/simulation_telemetry_injection/rule_based_extractor.py`):

- Match `wind\s*(speed)?\s*(\d+)\s*km/?h` → `weather` with `wind_speed_kmh = N`, confidence `medium`.
- Match `(magnitude|M)\s*(\d+\.?\d*)` → `geohazard` (earthquake), confidence `medium` (downgraded from high).
- ... 7 more category-specific patterns.

In degraded mode:

- `degraded_path: true` is set on the response.
- Confidence is downgraded by one rung (high→medium, medium→low).
- Life-safety low becomes `life_safety_low_confidence` refusal (FR-010 still enforced).
- An `injection.success` audit entry is still written but with `model_deployment: "rule-based-fallback"` and `prompt_hash: null`.

This satisfies FR-009 / FR-053 (graceful degradation under LLM unavailability) while preserving the FR-010 hybrid life-safety gate.

---

## 8. Cosmos write & session-token capture (FR-015)

Successfully validated signals are written to `simulation_synthetic_signals` (partition key `simulation_id`, Session consistency — see ADR-036-001):

```python
session_token: str | None = None
for signal in batch.signals:
    item, response = await container.create_item(
        body=signal.to_cosmos_doc(simulation_id=sim_id, ...),
        enable_response_payload=True,
    )
    if session_token is None:
        session_token = response.session_token  # capture for read-your-own-write barrier
```

The agent returns `session_token` in the HTTP response; the Controller passes it to subsequent sub-agent HTTP calls in the same turn (FR-008 single audit envelope). Sub-agents pass `session_token` to their Cosmos reads as `headers={"x-ms-session-token": session_token}`.

Event Hubs publish (in parallel with Cosmos write):

```python
async with producer:
    batch_event = await producer.create_batch(partition_key=str(sim_id))
    for signal in batch.signals:
        batch_event.add(EventData(json.dumps(signal.to_event_payload())))
    await producer.send_batch(batch_event)
```

Per-subscriber consumer groups (`sim-risk-assessment`, `sim-evacuation`, `sim-resource-allocation`, `sim-monitoring`) drive FR-026 fan-out.

---

## 9. Telemetry-Injection Audit (FR-009 success budget bookkeeping)

For each chat turn, the agent writes:

1. `injection.attempted` (every parse attempt, success or refused).
2. Either:
   - `injection.success` (one entry covering all signals in the turn — counts as 1 toward the 30/min FR-009 budget), or
   - `injection.refused` (one per refusal reason).
3. If any signal triggers FR-026 fan-out: `routing.fanout_dispatched` (existing spec-024 entry).

---

## 10. Contract test cases

Pinned in `tests/contract/test_telemetry_injection_llm.py`:

| Case | Input | Expected output |
|---|---|---|
| explicit-wind | `"Wind has shifted NW at 80 km/h"` | 1 weather signal, high confidence |
| life-safety-low | `"the embers are jumping the road"` | 0 signals; 1 refusal `life_safety_low_confidence` |
| pii-leak | `"call John on 0412345678"` | 0 signals; refusal `pii_detected` (caught pre-LLM) |
| real-world-action | `"dispatch a strike team"` | 0 signals; refusal `real_world_action_request` |
| multi-signal | `"Wind 80 NW; magnitude 5.2 quake near Sydney"` | 2 signals (weather + geohazard) |
| contradicts | `"actually wind is now from SE at 30"` (with prior NW 80 signal active) | 1 weather signal, `contradicts: <prior_signal_id>` |
| unparseable | `"the vibes are off"` | 0 signals; refusal `unknown_category`; `unparseable_text` populated |

Each test asserts the JSON schema validates the output, the Pydantic model parses it, the audit envelope is written, and the Cosmos session-token is captured.

---

*Telemetry-Injection LLM contract complete 2026-05-08. `gpt-4o-mini` with strict `json_schema`; Pydantic v2 validator; degraded rule-based fallback; FR-010 hybrid life-safety gate enforced both pre-LLM and post-LLM.*
