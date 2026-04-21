# Data Model: Simulation Control & Chat Orchestration

**Phase**: 1 · **Feature**: 024 · **Date**: 2026-04-19

All entities are scoped by the existing `tenant_id` (`sim-{scenarioRunId}`), persisted in
Cosmos DB containers with `/tenant_id` partition key, and carry a 2-year TTL.

## SimChatTurn

| Field | Type | Notes |
|---|---|---|
| id | string (uuid) | PK |
| tenant_id | string | partition key |
| simulation_id | string | redundant for query convenience |
| sequence | int | monotonic per simulation |
| role | enum(`user`,`assistant`,`tool`,`system`) | |
| content | string | redacted if PII was stripped |
| tool_call_id | string? | correlates assistant → tool → result |
| model | string | e.g. `gpt-4o-2024-08-06` |
| prompt_hash | string | SHA-256 of controller_prompt.md at send-time |
| actor_oid | string? | Entra ID object id for `user` role |
| created_at | datetime (UTC) | |
| content_hash | string | SHA-256 of `content` for tamper-evidence |

## SimToolInvocation

| Field | Type | Notes |
|---|---|---|
| id | string (uuid) | PK |
| tenant_id | string | partition key |
| turn_id | string | FK to SimChatTurn (assistant turn) |
| tool_name | enum(`seed_scenario`,`query_sub_agent`,`draft_warning_sim`,`summarise_state`,`pause`,`resume`,`stop`,`list_participants`) | allow-list enforced server-side |
| arguments | object (JSON) | |
| result | object? | null on error |
| outcome | enum(`ok`,`refused`,`error`,`cancelled-by-stop`) | |
| sub_agent | enum(`monitoring`,`planning`,`resource_allocation`,`communication`,`evacuation`,`risk_assessment`) ? | set only for `query_sub_agent` |
| latency_ms | int | |
| created_at | datetime (UTC) | |

## SimScenarioCard

| Field | Type | Notes |
|---|---|---|
| id | string (uuid) | PK |
| tenant_id | string | partition key |
| simulation_id | string | |
| hazard | enum(`bushfire`,`flood`,`cyclone`,`storm`,`heat`,`earthquake`,`tsunami`,`pandemic`,`other`) | |
| location | object | `{name, geojson_point, resolver: "azure-maps" | "user-provided"}` |
| start_at | datetime (UTC) | |
| aws_default_level | enum(`advice`,`watch_and_act`,`emergency_warning`) | |
| parameters | object | free-form keyed (wind_kmh, temp_c, rh, fuel_load, tc_category, surge_m, magnitude, …) |
| confirmed | bool | `true` after coordinator taps *Confirm & Start* |
| confirmed_by_oid | string? | |
| created_at | datetime (UTC) | |

## SimSyntheticDelivery

| Field | Type | Notes |
|---|---|---|
| id | string (uuid) | PK |
| tenant_id | string | partition key |
| simulation_id | string | |
| channel | enum(`sms`,`email`,`broadcast`,`social`,`cap_push`,`http`) | |
| audience | string | |
| payload_hash | string | SHA-256 of outbound body |
| block_reason | enum(`sim-egress-blocked`,`publication-gate`,`http-wrapper-gate`) | |
| intended_url | string? | for `http` channel |
| created_at | datetime (UTC) | |

## Simulation state (extension of spec 007 SimulationTenant)

Adds a single field:

- `status` — existing enum is extended with `draft` (pre-confirmation) and `ended` (post-stop);
  transitions are `draft → active → paused ⇄ active → ended` (ended is terminal). Spec 007's
  `active|paused|archived` remains; `archived` is reachable only from `ended` via the
  existing archive flow.

## Relationships

```text
SimulationTenant (spec 007) 1 ─── * SimChatTurn
                             1 ─── 1 SimScenarioCard
SimChatTurn (assistant role) 1 ─── * SimToolInvocation
SimulationTenant              1 ─── * SimSyntheticDelivery
```
