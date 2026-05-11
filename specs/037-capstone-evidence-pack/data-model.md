# Data Model — Capstone Evidence Pack

**Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md) · **Date**: 2026-05-11

This document describes the entities, fields, validation rules, and state transitions for the five durable artefacts. It is the source of truth for the JSON Schemas under [`contracts/`](./contracts/) and the Pydantic v2 models under `packages/domain/src/domain/models/`.

All entities are **append-only at the row level** (FR-005): published rows are immutable; corrections happen via dated revision rows that preserve the prior value. This is enforced at three layers — git history, Cosmos audit-timeline, and Blob immutability policy (ADR PD-037-04).

---

## Common envelope — `EvidencePackArtefact`

Every artefact JSON sidecar conforms to this envelope. The envelope's `metadata` block is what the publication-gate reads (RES-04, RES-05).

| Field | Type | Required | Description |
|---|---|:---:|---|
| `artefact_id` | enum: `risk_register`, `adoption_roadmap`, `executive_kpi_surface`, `rai_register`, `feature_value_ledger` | ✓ | One of the five artefact identifiers |
| `schema_version` | semver string | ✓ | Schema version this artefact validates against (e.g., `1.0.0`) |
| `publication_id` | UUID v4 | ✓ | Unique per publish; used as Blob snapshot key and Cosmos audit-row partition value |
| `published_at_utc` | RFC 3339 datetime | ✓ | Server-issued at publish time |
| `published_by` | string (Entra `oid`) | ✓ | Identity that triggered publication; never includes display name (NN-2) |
| `metadata` | object | ✓ | See `PublicationGateMetadata` below |
| `rows` | array of row objects | ✓ | Per-artefact row type (RiskRow / AdoptionWave / KpiRow / RaiRow / FeatureValueRow + TradeoffRow) |
| `superseded_surfaces` | array of string (path) | optional | For artefacts that supersede pre-existing surfaces (FR-022); each path gains a deprecation banner |

**Validation rules**:

- `rows` MUST be non-empty for v1 (FR-001).
- `published_at_utc` MUST be ≤ "now"; future-dated publications are rejected by the gate.
- `publication_id` MUST be unique across all prior publishes (Cosmos audit-timeline lookup).

**State transitions**: `Draft` (in-repo, no `publication_id`) → `Published` (gate-passed, `publication_id` assigned, Blob snapshot written, Cosmos audit row appended). There is **no `Edited` state**; corrections create a new `Published` row tagged `revises: <prior_publication_id>`.

---

## `PublicationGateMetadata`

The metadata block embedded in every `EvidencePackArtefact.metadata` and validated by `contracts/publication-gate-metadata.schema.json`.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `manual_row_count` | integer ≥ 0 | ✓ | Server-recomputed at publish; equals `count(rows[*].provenance.tag == "manual")` |
| `total_row_count` | integer ≥ 1 | ✓ | Equals `len(rows)` |
| `manual_row_ratio` | number in `[0, 1]` | ✓ | Equals `manual_row_count / total_row_count`; gate fails if mismatched |
| `auditor_signoff` | `AuditorSignoff` object | conditional | REQUIRED if `manual_row_ratio > 0.5` (FR-038); otherwise MUST be omitted |
| `manual_row_ratio_threshold` | number, default `0.5` | optional | For future-proofing; default locked to FR-038 cap for v1 |
| `link_check_status` | enum: `passed`, `failed`, `pending` | ✓ | Set by the gate; `passed` is the only state in a published artefact |
| `last_gate_run_utc` | RFC 3339 datetime | ✓ | Set by the gate when it last validated this artefact |

### `AuditorSignoff` (sub-object)

| Field | Type | Required | Description |
|---|---|:---:|---|
| `name` | string | ✓ | Named auditor |
| `role` | string | ✓ | Role title (e.g., "Compliance Auditor", "Risk Manager") |
| `signoff_date_utc` | RFC 3339 datetime | ✓ | When the override was granted |
| `basis` | string | ✓ | The AIDR / ISO / NIST framework reference that authorises the override (FR-038) |

**Validation rules**:

- If `manual_row_ratio > 0.5` and `auditor_signoff` is missing or any field is empty, the publication gate fails (FR-009 + FR-038, SC-011).
- `auditor_signoff` MUST NOT be present when `manual_row_ratio ≤ 0.5` (prevents accidental override claims).

---

## Common sub-objects

### `Provenance`

Carried on every row of every artefact (FR-037).

| Field | Type | Required | Description |
|---|---|:---:|---|
| `tag` | enum: `automated`, `manual` | ✓ | Source class |
| `source` | string (path or telemetry sink id) | ✓ | E.g., `apps/api/.../audit_writer.py` or `appinsights://customMetrics/evidence_pack.publication.duration_seconds` |
| `owner` | string (named role) | ✓ if `tag == "manual"` | Named role responsible (FR-037) |
| `review_cadence` | enum: `quarterly`, `monthly`, `post-incident` | ✓ if `tag == "manual"` | Review cadence (FR-037) |
| `automation_target` | string (spec/task ref or `"none"`) | ✓ if `tag == "manual"` | Future automation reference (FR-037) |
| `evidence_status` | enum: `Validated`, `Deferred`, `Unresolved` | ✓ | Mirrors `specs/shared/capstone-metric-trace.md` precedent |

### `BackCitation`

| Field | Type | Required | Description |
|---|---|:---:|---|
| `kind` | enum: `spec`, `adr`, `governance_hub`, `telemetry_sink`, `agent_md` | ✓ | Citation type |
| `ref` | string (path or sink id) | ✓ | E.g., `specs/030-llm-eval-framework/spec.md` |
| `section` | string | optional | Section heading or anchor |

---

## Per-artefact entities

### `RiskRow` (Artefact 1 — Systematic Risk Register)

Validated by `contracts/risk-register.schema.json`. Honours FR-010..FR-014.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `id` | string `RISK-<DOMAIN>-NNN` | ✓ | E.g., `RISK-AOAI-001` (must remain valid, FR-012) |
| `title` | string | ✓ | Short risk title |
| `category` | enum: `Platform`, `AI`, `Operational`, `Jurisdictional`, `Data`, `Supply-chain` | ✓ | FR-010: ≥ 1 row per category |
| `description` | string | ✓ | Full risk description |
| `likelihood` | integer 1..5 | ✓ | Inherent likelihood |
| `consequence` | integer 1..5 | ✓ | Inherent consequence |
| `inherent_score` | integer 1..25 | ✓ | `likelihood × consequence` (validated) |
| `treatment` | string | ✓ | Treatment summary |
| `owner` | string (named role) | ✓ | Named role |
| `residual_likelihood` | integer 1..5 | ✓ | Residual likelihood |
| `residual_consequence` | integer 1..5 | ✓ | Residual consequence |
| `residual_score` | integer 1..25 | ✓ | `residual_likelihood × residual_consequence` (validated) |
| `next_review_date` | ISO 8601 date | ✓ | Used by index `review overdue` flag (FR-013) |
| `back_citations` | array of `BackCitation` | ✓ | ≥ 1 spec or ADR (FR-011) |
| `provenance` | `Provenance` | ✓ | See above |

**Validation**: `inherent_score == likelihood * consequence`; `residual_score == residual_likelihood * residual_consequence`; `id` matches `^RISK-[A-Z0-9]+-\d{3}$`.

**Roll-up index** (`docs/risk-register/index.md`): rendered from the JSON sidecars sorted by `residual_score DESC`; rows with `next_review_date < today()` are flagged `review overdue` (FR-013).

---

### `AdoptionWave` (Artefact 2 — Adoption Roadmap)

Validated by `contracts/adoption-roadmap.schema.json`. Honours FR-015..FR-018.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `wave_id` | string `WAVE-NN` | ✓ | Sequential wave identifier |
| `cohort` | enum: `state-lead`, `local-government`, `utilities`, `transport`, `volunteer-ngo`, `commonwealth` | ✓ | Honours FR-015 cohort sequencing |
| `jurisdictions` | array of enum: `NSW`, `VIC`, `QLD`, `WA`, `SA`, `TAS`, `ACT`, `NT`, `Commonwealth` | ✓ | FR-018: every jurisdiction in ≥ 1 wave |
| `lead_agency` | string | ✓ | Named lead agency per jurisdiction (object map) |
| `readiness_gates` | array of string | ✓ | ≥ 1 gate per wave (US-2 acceptance) |
| `training_exercise_cadence` | object | ✓ | Cites specs 007/024/026 (FR-016, FR-017) |
| `training_exercise_cadence.cite` | array of `BackCitation` | ✓ | Specs 007/024/026 explicitly required |
| `change_management_artefacts` | array of string | ✓ | E.g., comms plan, training pack |
| `decommission_rollback_criteria` | array of string | ✓ | MUST preserve life-safety defaults + degrade to manual (FR-017) |
| `back_citations` | array of `BackCitation` | ✓ | |
| `provenance` | `Provenance` | ✓ | |

---

### `KpiRow` (Artefact 3 — Executive KPI Surface)

Validated by `contracts/executive-kpi-surface.schema.json`. Honours FR-019..FR-023.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `kpi_id` | string `KPI-CAP-NNN` | ✓ | Sequential KPI identifier |
| `capstone_criterion` | enum: `lives-saved`, `response-time`, `evacuation-lead-time`, `logistics-efficiency`, `economic-loss-reduction` | ✓ | One of the 5 capstone success criteria |
| `kind` | enum: `leading`, `lagging` | ✓ | FR-019: ≥ 1 leading + ≥ 1 lagging per criterion |
| `name` | string | ✓ | Human-readable KPI name |
| `owner` | string (named role) | ✓ | FR-020 |
| `refresh_cadence` | enum: `realtime`, `hourly`, `daily`, `weekly`, `monthly`, `quarterly` | ✓ | FR-020 |
| `target_value` | number | ✓ | FR-020 |
| `target_unit` | string | ✓ | E.g., "lives/year", "%", "minutes" |
| `threshold_band` | object `{green, amber, red}` | ✓ | FR-020 alert band |
| `source_of_truth` | `BackCitation` | ✓ | E.g., App Insights metric / Cosmos query / governance-hub markdown |
| `consolidates` | array of string (path) | ✓ | The scattered surfaces this KPI consolidates (FR-020 enumeration) |
| `current_value` | number | optional | Latest sampled value; absent if telemetry stale |
| `last_observed_utc` | RFC 3339 datetime | optional | If absent or > refresh_cadence, page renders "stale as of <timestamp>" (FR-023) |
| `back_citations` | array of `BackCitation` | ✓ | |
| `provenance` | `Provenance` | ✓ | |

**Page-level invariant** (FR-021): the executive page surfaces the per-artefact `manual_row_ratio` for each of the five artefacts at the top of the surface, in a `aria-live="polite"` region (NN-3).

---

### `RaiRow` (Artefact 4 — Responsible AI Register)

Validated by `contracts/responsible-ai-register.schema.json`. Honours FR-024..FR-029.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `component_id` | string | ✓ | E.g., `agent.communication`, `agent.evacuation`, `sim.telemetry-injection`, `eval.llm-framework`, `client.foundry-rag` |
| `component_kind` | enum: `sub-agent`, `simulation-agent`, `evaluation-framework`, `rag-client` | ✓ | |
| `spec_refs` | array of `BackCitation` | ✓ | Specs 008–012, 030, 036-sim-agent-extend, 036-foundry-rag-grounding (FR-024) |
| `frameworks` | object | ✓ | Four columns, each REQUIRED |
| `frameworks.au_ai_ethics_8_principles` | `RaiCell` | ✓ | |
| `frameworks.iso_42001` | `RaiCell` | ✓ | |
| `frameworks.iso_23894` | `RaiCell` | ✓ | |
| `frameworks.nist_ai_rmf` | `RaiCell` | ✓ | Sub-fields for Govern / Map / Measure / Manage |
| `principles` | object | ✓ | Eight dimensions, each REQUIRED |
| `principles.human_oversight` | `RaiCell` | ✓ | |
| `principles.fairness` | `RaiCell` | ✓ | |
| `principles.accountability` | `RaiCell` | ✓ | |
| `principles.transparency` | `RaiCell` | ✓ | |
| `principles.privacy` | `RaiCell` | ✓ | |
| `principles.safety` | `RaiCell` | ✓ | |
| `principles.contestability` | `RaiCell` | ✓ | |
| `principles.reliability` | `RaiCell` | ✓ | |
| `eval_evidence_refs` | array of `BackCitation` | ✓ | Cites spec 030 evaluation outputs (FR-028); MUST NOT trigger evaluation |
| `provenance` | `Provenance` | ✓ | |

#### `RaiCell` (sub-object)

| Field | Type | Required | Description |
|---|---|:---:|---|
| `posture` | enum: `compliant`, `partial`, `not-applicable` | ✓ | Blanks forbidden (FR-027) |
| `summary` | string | ✓ | One-paragraph summary |
| `na_justification` | string | ✓ if `posture == "not-applicable"` | Required when `not-applicable` |
| `evidence` | array of `BackCitation` | ✓ | ≥ 1 citation |

---

### `FeatureValueRow` (Artefact 5a — Feature-to-Value Ledger)

Validated by `contracts/feature-value-ledger.schema.json`. Honours FR-030..FR-034.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `spec_id` | string `NNN-<slug>` | ✓ | E.g., `030-llm-eval-framework` |
| `spec_title` | string | ✓ | Spec title |
| `tag` | enum: `capstone-contributing`, `delivery-hygiene` | ✓ | FR-030: rows that don't contribute MUST be tagged `delivery-hygiene` |
| `capstone_metrics` | array of object | ✓ if `tag == "capstone-contributing"` | One entry per metric contributed to |
| `capstone_metrics[].metric_id` | enum (5 capstone metrics) | ✓ | |
| `capstone_metrics[].magnitude` | number | ✓ | Quantified contribution |
| `capstone_metrics[].direction` | enum: `+`, `-`, `±` | ✓ | |
| `capstone_metrics[].residual_gap_to_target` | number | ✓ | FR-031 |
| `open_followups` | array of `BackCitation` | ✓ if any `residual_gap_to_target != 0` | FR-033: ≥ 1 follow-up named (existing spec / issue / roadmap wave) |
| `cross_link_to_metric_trace` | `BackCitation` | ✓ | Inverse link to `specs/shared/capstone-metric-trace.md` (FR-034) |
| `provenance` | `Provenance` | ✓ | |

### `TradeoffRow` (Artefact 5b — Decision/Tradeoff Log)

Validated by `contracts/feature-value-ledger.schema.json` (sibling section `tradeoffs[]`). Honours FR-032 + FR-036.

| Field | Type | Required | Description |
|---|---|:---:|---|
| `adr_id` | string `ADR-NNN-...` | ✓ | E.g., `ADR-031-progressive-delivery-pipeline` |
| `adr_path` | string (path) | ✓ | E.g., `docs/aidr/decisions/adr-031-progressive-delivery-pipeline.md` |
| `bounding_features` | array of string (`spec_id`) | ✓ | FR-032 |
| `alternatives_considered` | array of string | ✓ | FR-032 |
| `rationale` | string | ✓ | FR-032 |
| `synthesised_tension` | enum: `speed-vs-legality`, `automation-vs-command`, `local-vs-cross-jurisdiction`, `visibility-vs-privacy`, `none` | ✓ | FR-036 |
| `provenance` | `Provenance` | ✓ | |

---

## Relationships

```text
EvidencePackArtefact (envelope)
├── metadata: PublicationGateMetadata
│   └── auditor_signoff?: AuditorSignoff
├── rows[]: <RowType>
│   ├── back_citations[]: BackCitation
│   └── provenance: Provenance
└── superseded_surfaces[]: string

FeatureValueRow ──cross-links──▶ specs/shared/capstone-metric-trace.md row(s)
RaiRow         ──cites──────────▶ spec 030 evaluation outputs
AdoptionWave   ──cites──────────▶ specs 007 / 024 / 026 capabilities
KpiRow         ──consolidates──▶ docs/governance-dashboard.md, governance-hub/observability/{slo,metrics-catalogue}.md, specs/{015,021,030}
RiskRow        ──extends───────▶ docs/risk-register/RISK-AOAI-001.md (preserved under new schema)
```

---

## State machine — publication

```text
[Draft (in-repo only)]
       │  developer commits .md + .json under PR
       ▼
[Pending] ── publication-gate runs ──▶ [Failed] ── fix + re-PR ──▶ [Pending]
       │ gate passes
       ▼
[Published]
       │  Blob snapshot written
       │  Cosmos audit row appended
       │  App Insights metrics emitted
       ▼
[Immutable] ── correction needed? ──▶ new PR creates revision row with `revises: <prior_publication_id>`
```

There is no `Unpublish` state; once published, an artefact's `publication_id` is permanent and traceable.

---

## Indices

- **Risk Register roll-up** (`docs/risk-register/index.md`): list of all `RiskRow` sorted by `residual_score DESC`, with overdue flag (FR-013).
- **Governance-hub index** (`docs/governance-hub/index.md`): five top-level links to the artefacts (FR-002).
- **Capstone-metric-trace cross-link** (`specs/shared/capstone-metric-trace.md`): adds spec-037 row tagged `non-capstone-critical-path / delivery-hygiene` (FR-007).
