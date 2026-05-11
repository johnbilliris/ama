# Data Model: Measurable Success-Criteria Evidence Harness (spec 038)

**Branch**: `038-success-criteria` | **Date**: 2026-05-11
**Source spec**: `specs/038-success-criteria/spec.md`
**Source decisions**: `specs/038-success-criteria/research.md` D1–D14

This document maps the spec's nine Key Entities to concrete Cosmos DB
containers, partition keys, and Pydantic v2 models. All containers live
in the existing AU Cosmos DB account
(`australiaeast` primary, `australiasoutheast` paired DR — FR-029).

Pydantic v2 models go under `apps/api/app/services/evidence/models/`
and a Python twin is published from
`packages/domain/src/domain/models/evidence_*.py` for cross-service
reuse; the TypeScript twin under `packages/domain/src/evidence/*.ts`
mirrors the same schema for the Next.js frontend (FR-034 reuse).

All timestamps are UTC `datetime` (Pydantic `AwareDatetime`).
All IDs are ULIDs (string, 26 chars) generated server-side.

---

## Container summary

| Container             | Partition key      | Append-only | TTL / archive          | Spec entity (Key Entities §)        |
| --------------------- | ------------------ | ----------- | ---------------------- | ----------------------------------- |
| `kpi_ladder`          | `/kpi_id`          | versioned   | none                   | KPI Ladder + Indicator Definition   |
| `kpi_signals`         | `/scenario_id`     | yes         | 90d hot → cold-archive | Signal                              |
| `delta_scorecards`    | `/scenario_id`     | versioned   | none                   | Delta Scorecard                     |
| `causal_chains`       | `/capability_id`   | versioned   | none                   | Causal Chain                        |
| `benchmark_register`  | `/kpi_id`          | versioned   | none                   | Benchmark Register                  |
| `evidence_audit`      | `/audit_id`        | yes (locked) | 90d hot → 7y cold-lock | Audit Trail                         |
| `evidence_audit_dlq`  | `/audit_id`        | yes         | 30d                    | (operational dead-letter; not spec) |

Measurement Method (Key Entity #3) is **not** a Cosmos entity — it is
deterministic content generated from `kpi_ladder` + a templated markdown
renderer. The published artefact is materialised on demand by
`GET /api/v1/evidence/measurement-method` (no separate container).

---

## 1. KPI Ladder + Indicator Definition

**Container**: `kpi_ladder`  **Partition key**: `/kpi_id`

Each ladder version is a single document keyed by `kpi_id` (one
indicator) plus a `version` integer. The "ladder" view is materialised
by joining all latest-version documents grouped by `capstone_sc_id`
(see `KpiLadderView` projection).

```python
# apps/api/app/services/evidence/models/kpi.py
from typing import Annotated, Literal
from pydantic import BaseModel, Field, AwareDatetime, condecimal

AiimsFunction = Literal[
    "Control", "Intelligence", "Planning",
    "Operations", "Logistics", "PublicInformation",
]
IncidentLevel = Literal[1, 2, 3]
Provenance = Literal["auto", "manual"]
IndicatorKind = Literal["leading", "lagging"]
LifeSafetyTier = Literal["life_safety", "efficiency"]  # FR-006 ranking


class ConfidenceBandRule(BaseModel):
    """FR-002 attribute #9 + FR-009/FR-010 default."""
    method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"] = "bootstrap_p2_5_p97_5"
    min_resamples: int = Field(default=1000, ge=1)
    fallback_label: Literal["small-sample"] = "small-sample"


class RiskAdjustment(BaseModel):
    """FR-004 — 5x5 likelihood × consequence matrix (AS/NZS ISO 31000)."""
    likelihood: Annotated[int, Field(ge=1, le=5)]
    consequence: Annotated[int, Field(ge=1, le=5)]

    @property
    def weight(self) -> float:
        return (self.likelihood * self.consequence) / 25.0


class IndicatorDefinition(BaseModel):
    """One row in the ladder. FR-002 nine attributes."""
    id: str  # ULID, document id
    kpi_id: str  # partition key — stable across versions
    version: int = Field(ge=1)
    capstone_sc_id: Literal[
        "SC-CAP-015-001",  # ≥1,000 lives saved/yr
        "SC-CAP-015-002",  # ≥50 % response-time reduction
        "SC-CAP-015-003",  # ≥24 h earlier evac lead-time
        "SC-CAP-015-004",  # ≥30 % logistics efficiency uplift
        "SC-CAP-015-005",  # ≥30 % economic-loss reduction
    ]
    name: str
    kind: IndicatorKind  # leading | lagging — FR-001 (≥1 of each per SC)
    aiims_function: AiimsFunction  # FR-003
    incident_level: IncidentLevel  # FR-003
    life_safety_tier: LifeSafetyTier  # FR-006 ranking input

    # FR-002 nine attributes:
    formula: str
    unit: str
    owner_role: str
    refresh_cadence: str  # ISO-8601 duration, e.g. "PT15M"
    target_value: condecimal(max_digits=18, decimal_places=4)
    alert_threshold: condecimal(max_digits=18, decimal_places=4)
    baseline_source: str  # citation back to spec 015 / prototype baseline
    provenance: Provenance
    confidence_band_rule: ConfidenceBandRule

    # FR-004 — risk-adjusted twin (optional only if matrix not yet supplied;
    # render-time refusal handled per spec Edge Case #5).
    risk_adjustment: RiskAdjustment | None = None

    created_at: AwareDatetime
    created_by: str  # actor sub / role
    superseded_by: str | None = None  # ULID of next-version document
```

**Validation rules**

- `version` is monotonically increasing per `kpi_id`. Updates create a
  new document; the prior document's `superseded_by` is set in a
  transactional batch (FR-005).
- For each `capstone_sc_id`, the projected ladder view MUST contain
  ≥1 `leading` AND ≥1 `lagging` document (SC-001 verified at write
  time + at API read time).
- `provenance == "manual"` rows are counted per artefact; service
  refuses publication when manual share > 50 % unless a named-auditor
  sign-off entry exists in `evidence_audit` (FR-028 / SC-010).
- `risk_adjustment is None` → `GET ?include_risk_adjusted=true` returns
  HTTP 409 with the Edge Case #5 message.

**State transitions**: `draft → published → superseded`. Only `published`
documents appear in the ladder view; `superseded` remain retrievable
by ID for audit (FR-005).

---

## 2. Signal

**Container**: `kpi_signals`  **Partition key**: `/scenario_id`

```python
class ConfidenceScore(BaseModel):
    """FR-024 — float [0.00, 1.00], two-decimal precision."""
    value: condecimal(ge=0, le=1, decimal_places=2)

    @property
    def band(self) -> Literal["high", "medium", "low"]:
        if self.value >= 0.80: return "high"
        if self.value >= 0.50: return "medium"
        return "low"


class CanonicalEventChain(BaseModel):
    """FR-008 — call→dispatch→arrival→control→clear timestamps."""
    call_received_at: AwareDatetime | None = None
    dispatched_at: AwareDatetime | None = None
    arrived_at: AwareDatetime | None = None
    controlled_at: AwareDatetime | None = None
    cleared_at: AwareDatetime | None = None
    imputed_fields: list[str] = Field(default_factory=list)  # FR-008 forward-impute tag


class Signal(BaseModel):
    id: str  # ULID
    scenario_id: str  # partition key
    seed: str  # FR-014 deterministic seed
    mode: Literal["baseline", "ama_assisted"]  # FR-012
    kpi_id: str  # foreign key → kpi_ladder
    capability_id: str  # spec 008–012 / 036 / 036-sim-agent-extend agent id
    capability_version: str  # FR-024 provenance
    actor: str  # human or agent identity
    source: str  # FR-024 provenance
    occurred_at: AwareDatetime
    region: Literal["australiaeast", "australiasoutheast"]  # FR-029 — non-AU rejected at write
    chain: CanonicalEventChain
    confidence: ConfidenceScore
    reduced_fidelity: bool = False  # FR-027 / FR-032
    advisory_only: bool = False  # FR-024 + FR-030 gate when band == "low"
    payload: dict  # KPI-specific numeric payload (validated per kpi_id)
    correlation_id: str  # propagated to App Insights
```

**Validation rules**

- `region` MUST be one of the two AU regions; non-AU writes are
  rejected at the FastAPI layer and the refusal is recorded in
  `evidence_audit` with `kind="non_au_signal_refused"` (FR-029, SC-009).
- `confidence.band == "low"` → `advisory_only` MUST be `True` and
  `reduced_fidelity` MUST be `True` (FR-024).
- `imputed_fields` non-empty → row is excluded from the bootstrap CI
  computation (FR-008 / D5).

---

## 3. Delta Scorecard

**Container**: `delta_scorecards`  **Partition key**: `/scenario_id`

```python
class KpiDelta(BaseModel):
    kpi_id: str
    baseline_value: condecimal(max_digits=18, decimal_places=4)
    ama_assisted_value: condecimal(max_digits=18, decimal_places=4)
    absolute_delta: condecimal(max_digits=18, decimal_places=4)
    percent_delta: condecimal(max_digits=8, decimal_places=4)
    confidence_band_low: condecimal(max_digits=18, decimal_places=4)
    confidence_band_high: condecimal(max_digits=18, decimal_places=4)
    confidence_method: Literal["bootstrap_p2_5_p97_5", "stddev_pm1"]
    meets_target: bool
    small_sample: bool = False  # FR-008/FR-010 label
    reduced_fidelity: bool = False  # FR-027


class DeterminismCheck(BaseModel):
    """FR-016 — ±2 % relative OR ±1 absolute unit, whichever is greater."""
    repetition_count: int = Field(ge=1)
    within_tolerance_count: int
    diverged: bool  # surfaced (not hidden) per FR-016 + Edge Case #4

    @property
    def reproduction_rate(self) -> float:
        return self.within_tolerance_count / self.repetition_count


class DeltaScorecard(BaseModel):
    id: str  # ULID
    scenario_id: str  # partition key — one of the 7 canonical scenarios
    seed: str
    run_pair_id: str  # ties baseline + ama-assisted Signal sets
    kpi_deltas: list[KpiDelta]  # MUST cover all 5 capstone KPIs (SC-003)
    determinism: DeterminismCheck | None = None  # populated after ≥2 repeats
    created_at: AwareDatetime
    created_by: str
    correlation_id: str
```

**Validation rules**

- `kpi_deltas` MUST contain exactly the five capstone KPIs (SC-003).
- `determinism.reproduction_rate >= 0.95` is the SC-004 pass bar; lower
  values do NOT block publication but MUST set `diverged = True` and
  surface in the UI (FR-016).

---

## 4. Causal Chain

**Container**: `causal_chains`  **Partition key**: `/capability_id`

```python
class Assumption(BaseModel):
    text: str
    resolved: bool = False  # FR-019 — unresolved flagged in UI


class ThreatToValidity(BaseModel):
    text: str
    severity: Literal["low", "medium", "high"]


class CausalChain(BaseModel):
    id: str
    capability_id: str  # partition key — agent id from specs 008–012/036/036-sim-agent-extend
    capability_name: str
    version: int = Field(ge=1)
    kpis_moved: list[str]  # ≥1 — kpi_id list
    expected_magnitude_value: condecimal(max_digits=18, decimal_places=4)
    expected_magnitude_unit: str
    assumptions: list[Assumption]  # ≥1
    threats_to_validity: list[ThreatToValidity]  # ≥1
    originating_spec_path: str  # FR-018 back-citation, e.g. "specs/011-resource-allocation-agent/spec.md"
    created_at: AwareDatetime
    superseded_by: str | None = None
```

**Validation rules** (SC-006): every published agent (specs 008, 009,
010, 011, 012, 036, 036-sim-agent-extend) MUST have ≥1 `published`
chain document. `originating_spec_path` MUST start with `specs/` and
point to an existing file.

---

## 5. Benchmark Register

**Container**: `benchmark_register`  **Partition key**: `/kpi_id`

```python
class BenchmarkEntry(BaseModel):
    id: str
    kpi_id: str  # partition key
    jurisdiction: str  # e.g. "NSW Ambulance", "VIC FRV", "AU"
    kind: Literal["external_benchmark", "prototype_baseline"]  # FR-021
    source_name: str  # e.g. "AFAC FDI/FFDI", "BoM hazard warning lead-time"
    source_citation: str  # URL or doc ref
    target_value: condecimal(max_digits=18, decimal_places=4) | None  # nullable for "not available"
    target_unit: str
    not_available: bool = False  # FR-022
    created_at: AwareDatetime
```

**Validation rules** (SC-007): for every `kpi_id` in `kpi_ladder`, the
register MUST contain ≥1 entry. If no recognised external benchmark
exists for a jurisdiction, the entry MUST have `not_available = True`
and a sibling `prototype_baseline` entry MUST be present.

---

## 6. Audit Trail

**Container**: `evidence_audit`  **Partition key**: `/audit_id`
**Cold archive**: Blob container `evidence-audit-cold/` (Cool tier, 7-y
immutability lock — D3).

```python
AuditKind = Literal[
    "signal_ingested",
    "scorecard_published",
    "ladder_version_published",
    "non_au_signal_refused",       # FR-029, SC-009
    "manual_share_blocked",        # FR-028, SC-010
    "auditor_signoff_recorded",    # FR-028 / spec 037 FR-037 reuse
    "kpi_amendment_recorded",      # FR-025 — original preserved, new entry appended
    "degraded_mode_entered",       # FR-027, FR-032
    "small_sample_labelled",       # FR-008 / FR-010
    "divergence_flagged",          # FR-016, Edge Case #4
]


class AuditEntry(BaseModel):
    """FR-025 — append-only. Service rejects PATCH/DELETE."""
    id: str  # ULID
    audit_id: str  # partition key — typically equals the value_id (KPI value being traced)
    value_id: str  # the kpi value / scorecard / signal id this entry pertains to
    kind: AuditKind
    actor: str  # human sub or agent capability_id
    occurred_at: AwareDatetime
    references: dict[str, str]  # {"signal_id": ..., "model_output_id": ..., "decision_id": ..., "outcome_id": ...}
    payload: dict  # kind-specific structured detail
    correlation_id: str
    region: Literal["australiaeast", "australiasoutheast"]  # FR-029
    archived_to_blob: bool = False  # set True after change-feed mirror at age 90d
```

**Validation rules**

- The service layer rejects any `PATCH`/`DELETE` against this container
  at the Manager tier (FR-025). Amendments are recorded as a NEW entry
  with `kind="kpi_amendment_recorded"` and `references["original_id"]`
  pointing at the prior entry.
- `references` MUST permit the SC-005 trace
  `signal → model → recommendation → human decision → outcome` to be
  walked in a single audit view. The service guarantees this by
  validating that for any `value_id`, the union of
  `references.keys()` across all entries covers the five-step chain
  (or explicitly records `degraded_mode_entered` for any missing step).

---

## Cross-entity invariants

- **AU sovereignty (FR-029, SC-009)**: every write to every container
  asserts `region in {"australiaeast", "australiasoutheast"}`. The
  Cosmos accounts themselves are pinned to those regions by Bicep
  (D10).
- **Life-safety primacy (FR-006)**: any rollup endpoint that ranks
  KPIs orders `IndicatorDefinition.life_safety_tier == "life_safety"`
  ahead of `"efficiency"` regardless of magnitude.
- **Advisory-only (FR-030)**: scorecards with any
  `KpiDelta.reduced_fidelity == True` carry an `advisory_only: true`
  banner in the API response and the UI.
- **Capstone exclusion (FR-033, SC-011)**: this spec is tagged
  non-capstone-critical-path in `specs/shared/capstone-metric-trace.md`
  (see `plan.md` §"Capstone-trace tagging step").
- **Append-only audit (FR-025)**: enforced at the Manager tier; Cosmos
  change-feed mirrors to immutable Blob (D3) for ≥7-year retention.
