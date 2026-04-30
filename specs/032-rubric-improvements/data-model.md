# Phase 1 — Data Model: AMA Rubric Improvements

Entities introduced or extended by this feature. Existing entities (Signal, Incident, Alert, etc.) are unchanged unless noted.

## E-01 — Recommendation (extended)

Existing entity. Adds the following provenance + governance fields.

| Field | Type | Required | Notes |
|---|---|---|---|
| `prompt_sha` | string (hex 64) | yes (when LLM-backed) | SHA-256 of the prompt template + variables snapshot |
| `prompt_version` | string (semver) | yes (when LLM-backed) | from `packages/prompts/` registry |
| `model_id` | string | yes (when LLM-backed) | e.g. `gpt-4o`, `phi-3.5-mini` |
| `model_version` | string | yes (when LLM-backed) | Foundry deployment version label |
| `deployment_alias` | string | yes (when LLM-backed) | `aoai-reasoning-prod` etc. |
| `rag_sources[]` | array of `RagCitation` | optional | populated when prompt is grounded |
| `consensus_id` | UUID | optional | links to a `ConsensusEvent` when peer agents agreed |
| `autonomy_level_at_decision` | enum `low\|standard\|high` | yes | snapshot of jurisdiction-policy autonomy at decision time |
| `kill_switch_state` | enum `off\|engaged\|partial` | yes | snapshot |
| `shadow` | bool (default false) | yes | true → recommendation is from a shadow model path; never surfaced in UI |
| `parent_recommendation_id` | UUID | optional | for shadow recs, links to the prod recommendation it shadows |
| `audit_segment_id` | UUID | yes | links to AuditSegment containing this recommendation |

**State transitions**: unchanged (`proposed → under_review → approved/rejected/escalated → executed`); Saga doc in `docs/agents/decision-rights.md`.

## E-02 — RagCitation (NEW)

Embedded value type used in `Recommendation.rag_sources`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `handbook_id` | string | yes | e.g. `aidr-incident-management-2023` |
| `chapter` | string | optional | |
| `page` | int | optional | |
| `chunk_id` | string | yes | AI Search index document key |
| `score` | float | yes | retrieval score (0..1) |
| `quote` | string (≤ 500 chars) | yes | exact quoted snippet shown in the recommendation card |

## E-03 — AuditSegment (NEW)

Append-only ledger record. One row per timeline event burst (default: 100 events or 60 s window).

| Field | Type | Required | Notes |
|---|---|---|---|
| `segment_id` | UUID | yes | partition key |
| `incident_id` | UUID | yes | secondary index |
| `tenant_id` | string | yes | secondary index |
| `created_at` | datetime | yes | UTC, ISO 8601 |
| `event_count` | int | yes | |
| `events[]` | array of `TimelineEvent` | yes | append-only within the segment until sealed |
| `prev_segment_hash` | string (hex 64) | yes | SHA-256 of previous segment's `segment_hash` (or zero hash for first) |
| `segment_hash` | string (hex 64) | yes (after sealing) | SHA-256 of (`prev_segment_hash` ‖ canonical JSON of events ‖ created_at) |
| `sealed_at` | datetime | yes (after sealing) | sealed when full or window elapses |

**Integrity check job**: walks segments in `created_at` order verifying `prev_segment_hash` chain and `segment_hash` recomputation. Failure → publish-block + Observer-Auditor page.

## E-04 — JurisdictionPolicy (NEW)

Declarative document keyed by jurisdiction code. Stored in Cosmos container `jurisdiction_policies` (PK `/jurisdiction_code`).

| Field | Type | Required | Notes |
|---|---|---|---|
| `jurisdiction_code` | string | yes | `nsw`, `vic`, `qld`, ..., `commonwealth`, `act` |
| `autonomy_level` | enum `low\|standard\|high` | yes | overrides env default per FR-AG02 |
| `kill_switch_overrides` | map<agent_id, bool> | optional | per-agent off/on |
| `language_priorities[]` | array of BCP-47 tags | yes | first match wins for outbound public messaging |
| `aiims_role_overrides` | map<aiims_function, agent_id> | optional | per-jurisdiction role-to-agent mapping |
| `version` | int | yes | monotonically increasing |
| `effective_from` | datetime | yes | activation timestamp |
| `approved_by` | string (operator id) | yes | audit |

## E-05 — ConsensusEvent (NEW)

| Field | Type | Required |
|---|---|---|
| `consensus_id` | UUID | yes |
| `incident_id` | UUID | yes |
| `agent_ids[]` | array of strings | yes (≥ 2) |
| `recommendation_summary` | string | yes |
| `agreement_score` | float (0..1) | yes |
| `time_window_seconds` | int | yes |
| `created_at` | datetime | yes |

## E-06 — EvalCase / EvalScorecard (extended)

Spec 030 entities. This feature commits to v1 = 5,000 cases. Scorecards drive CI gates: a PR that lowers any of {accuracy, hallucination_rate, safety_pass_rate, refusal_correctness, tone_appropriateness} below the published baseline fails CI.

## E-07 — MetricDefinition (NEW)

Catalogue entry for `docs/observability/metrics-catalogue.md` and used at runtime to register App Insights customMetrics.

| Field | Type | Required |
|---|---|---|
| `name` | string | yes |
| `kind` | enum `counter\|gauge\|histogram` | yes |
| `unit` | string (UCUM) | yes |
| `dimensions[]` | array of strings | yes |
| `source_module` | string | yes |
| `slo_link` | string (anchor in slo.md) | optional |
| `retention_days` | int | yes |

Initial catalogue entries:
- `signal.ingestion.lag_seconds` (histogram, dims: source, jurisdiction)
- `agent.handoff.success_total` (counter, dims: source_agent, target_agent)
- `agent.handoff.dead_letter_depth` (gauge, dims: queue)
- `alert.publish.lag_seconds` (histogram, dims: jurisdiction, language)
- `llm.tokens.total` (counter, dims: model, deployment, operation)
- `llm.cost.aud_micros` (counter, dims: model, deployment, operation)
- `llm.budget.warning` (counter, dims: scope)
- `agent.killswitch.lag_seconds` (histogram, dims: agent_id)
- `rag.retrieval.lag_milliseconds` (histogram, dims: index)
- `audit.integrity_check.failures_total` (counter)
- `dora.deployment_frequency_per_day` (gauge)
- `dora.lead_time_hours` (histogram)
- `dora.change_failure_rate` (gauge)
- `dora.mttr_minutes` (histogram)

## E-08 — SLO (NEW)

| Field | Type |
|---|---|
| `id` | string |
| `description` | string |
| `sli_metric_name` | string (FK to MetricDefinition.name) |
| `objective` | string (e.g., `P95 ≤ 60s over 30d`) |
| `error_budget_minutes_per_month` | float |
| `paging_severity` | enum `P1\|P2\|P3\|P4\|P5` |

## E-09 — PromptArtifact (NEW)

| Field | Type | Required |
|---|---|---|
| `id` | string | yes |
| `version` | semver | yes |
| `sha` | string (hex 64) | yes |
| `owner` | string (GitHub team) | yes |
| `cosign_signature_url` | string | yes |
| `fulcio_identity` | string | yes |
| `review_due` | date | yes |
| `templates[]` | array of `{name, content_hash}` | yes |

## E-10 — AutonomyDial (NEW)

In-memory snapshot served from JurisdictionPolicy + environment defaults; consumed by every agent's decision gate.

```python
class AutonomyDial(BaseModel):
    environment: Literal["dev", "staging", "production", "rehearsal"]
    jurisdiction_code: str
    level: Literal["low", "standard", "high"]
    rationale: str
    snapshot_at: datetime
```

Defaults: `dev=high`, `staging=standard`, `production=standard`, `rehearsal=high`. Jurisdiction policy may override; `low` is reserved for life-safety windows declared by IC/Executive.

## E-11 — KillSwitch (NEW)

Cosmos document `agent_killswitches/<agent_id>`; watched by each agent process. Toggle propagation P99 ≤ 30 s; heartbeat metric `agent.killswitch.lag_seconds`.

| Field | Type |
|---|---|
| `agent_id` | string |
| `engaged` | bool |
| `engaged_at` | datetime |
| `engaged_by` | operator id |
| `reason` | string |
| `expires_at` | datetime (optional) |

---

**Relationships overview**

```
Recommendation ── 1..* ──> RagCitation
Recommendation ── 1 ──> AuditSegment
Recommendation ── 0..1 ──> ConsensusEvent
JurisdictionPolicy ── 1..* ──> AutonomyDial (snapshots)
PromptArtifact ── 1..* ──> Recommendation (via prompt_sha + prompt_version)
EvalCase ── 1..* ──> EvalScorecard
MetricDefinition ── 1..* ──> SLO
KillSwitch ── 1 ──> Agent
```
