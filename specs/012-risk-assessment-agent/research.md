# Research: Risk Assessment Agent — Hazard Prediction, Recommendation Generation, and Multi-Agent Escalation

**Feature**: 012-risk-assessment-agent  
**Date**: 2026-04-15  
**Status**: Complete

---

## Research Task 1 — Weighted Confidence Averaging Formula (CHK018, CHK019)

**Context**: FR-011 specifies weighted averaging with authoritative=2×, IoT=1×, social=0.5× but doesn't define the exact formula. CHK018 asks whether these are defaults or fixed constants. CHK019 asks for the specific aggregation formula. Freshness scores must also be incorporated per FR-015.

**Decision**: Apply freshness adjustment at the per-signal level *before* weighted averaging. The formula is:

```
weighted_confidence = Σ(signal_i.confidence * source_weight_i * signal_i.freshness)
                    / Σ(source_weight_i * signal_i.freshness)
```

Where `source_weight` is: authoritative=2.0, IoT=1.0, social=0.5 (defaults, configurable via environment variables `SOURCE_WEIGHT_AUTHORITATIVE`, `SOURCE_WEIGHT_IOT`, `SOURCE_WEIGHT_SOCIAL`). Unknown source types default to social weight (0.5).

**Rationale**: Applying freshness at the per-signal level prevents stale authoritative signals from dominating the fused score through their 2× weight. A stale BoM signal should contribute less than a fresh BoM signal regardless of its source authority. The weighted mean produces a normalised confidence score in [0.0, 1.0] that accounts for both source trust and data recency. Source weights are configurable to allow runtime tuning, matching the intent of CHK018.

**Alternatives considered**:
- **Freshness as a separate post-averaging penalty**: Simpler but masks per-signal freshness contributions — a single stale signal among many fresh ones would penalise the entire average unfairly.
- **Fixed weights only**: Simpler but doesn't allow operational tuning when source reliability changes during an event.
- **Unweighted mean**: Loses the authoritative-source preference mandated by Constitution Principle III.

---

## Research Task 2 — Contradiction Detection and 30% Confidence Reduction (CHK025, CHK026, CHK027)

**Context**: FR-013 requires a 30% confidence reduction for contradictory signals. CHK026 asks whether this is multiplicative or subtractive. CHK025 asks for an objective definition of "opposing risk trajectories". CHK027 asks how three-way+ contradictions are handled.

**Decision**: 
- **Reduction method**: Multiplicative — `adjusted_confidence = weighted_confidence * 0.7`. This keeps the result bounded in [0.0, 1.0] regardless of input values.
- **Contradiction definition**: Two signals are contradictory when they indicate opposing risk trends for the same incident and geographic area. Objective criteria: one signal's payload indicates risk increasing (e.g., temperature rising, wind speed increasing, water level rising) while another indicates risk decreasing (e.g., fire contained, storm weakening, water receding) for the same parameter type. This is determined by the signal category and a configurable `risk_direction` field in the signal payload (values: `increasing`, `decreasing`, `stable`).
- **Multi-way contradictions**: The 30% reduction is applied once per assessment regardless of the number of contradicting signal pairs. The rationale is that the reduction flags uncertainty — additional contradictions don't compound the mathematical adjustment but ARE individually logged in the audit trail and assessment summary.

**Rationale**: Multiplicative reduction is standard for composable confidence adjustments. It preserves the [0,1] range and doesn't produce negative values (subtractive could: 0.2 - 0.3 = -0.1). The single-application-per-assessment approach prevents extreme confidence collapse in noisy environments where multiple contradictions may reflect sensor noise rather than genuinely conflicting conditions.

**Alternatives considered**:
- **Subtractive (−0.30)**: Could produce negative values for low-confidence signals. Rejected.
- **Per-pair 30% compounding**: `confidence * 0.7^N` for N contradictory pairs. Rejected because three contradicting signals would reduce to `0.343×` which is overly aggressive and could suppress valid assessments.
- **Weighted by source authority**: Reduce less for authoritative-vs-social contradictions. Rejected as adding complexity without clear benefit; all contradictions should trigger human review.

---

## Research Task 3 — Optimistic Concurrency for Assessment Versioning (CHK032)

**Context**: FR-006 requires monotonically increasing version numbers per incident and assessment type. CHK032 asks how this is guaranteed under concurrent processing.

**Decision**: Use a separate version counter document in Cosmos DB per incident+assessment_type, protected by optimistic concurrency with `_etag`. Pattern:

1. **Counter document**: `{id: "{incident_id}_{assessment_type}_counter", current_version: N, _etag: "..."}` stored in the same Cosmos container.
2. **Version assignment**: Read counter → increment → conditional `replace_item` with `If-Match: {_etag}`.
3. **Conflict handling**: On `412 Precondition Failed`, re-read the counter, re-increment, and retry (max 3 retries with jitter). If all retries fail, log an error and generate an assessment with a UUID-based fallback version suffix.
4. **Assessment document**: Immutable once written. Uses `create_item` (not upsert), so duplicate IDs fail fast.

**Rationale**: Separating the counter from the assessment document avoids read-modify-write races on assessment records (which must be immutable). The `_etag`-guarded counter ensures that even with concurrent processing of handoffs for the same incident, version numbers never collide. Three retries with jitter handle typical contention scenarios (most disaster incidents have low concurrent assessment rates per type).

**Alternatives considered**:
- **Database-generated auto-increment**: Cosmos DB doesn't natively support auto-increment. Rejected.
- **Timestamp-based versioning**: Risk of collisions at millisecond granularity. Rejected because spec mandates `{incident_id}_v{N}` format with integer N.
- **Distributed lock (Azure Blob lease)**: Stronger guarantee but adds latency and another Azure dependency. Over-engineering for expected concurrency levels.

---

## Research Task 4 — Penalty Ordering and Stacking (CHK039)

**Context**: The confidence score undergoes multiple adjustments: freshness (per-signal), contradiction reduction, and LLM fallback penalty. CHK039 asks for the order of application.

**Decision**: Apply penalties in this order:
1. **Freshness adjustment** — incorporated during weighted averaging (per Research Task 1)
2. **Contradiction reduction** — multiplicative: `× 0.7` (per Research Task 2)
3. **Fallback penalty** — multiplicative: `× 0.8` when LLM is unavailable (FR-031)

The final formula for a worst-case scenario:
```
raw_weighted_confidence = weighted_average(signals, weights, freshness)
after_contradiction = raw_weighted_confidence * 0.7     # if contradictions detected
after_fallback = after_contradiction * 0.8              # if LLM unavailable
final_confidence = after_fallback
```

Example: base=0.8, with contradiction and fallback → `0.8 × 0.7 × 0.8 = 0.448` (medium confidence). This is sensible — high-quality source data that has contradictions and no LLM reasoning should still produce a usable assessment at medium confidence.

**Rationale**: Ordering freshness first ensures it's baked into the base score before downstream adjustments. Contradiction detection operates on the fused score (not raw signals), so it comes second. Fallback penalty is an infrastructure-level degradation applied last. Multiplicative stacking keeps all values in [0.0, 1.0] and composes cleanly.

**Alternatives considered**:
- **Additive penalties**: Could produce negative values. Rejected.
- **Single combined penalty**: Less transparent for audit trail. Rejected because each adjustment must be independently recorded per FR-029.
- **Reversed order (fallback first)**: Doesn't make sense because fallback status is independent of the data quality being measured.

---

## Research Task 5 — Audit Record Schema Consolidation (CHK048)

**Context**: CHK048 identifies inconsistency between FR-029's field list and the Key Entities section for `RiskAssessmentDecisionRecord`. The canonical fields must be established.

**Decision**: The canonical audit record fields are:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str (UUID) | Unique record identifier |
| `handoff_id` | str | Originating handoff ID |
| `input_signal_ids` | list[str] | Signal IDs used in this processing step |
| `assessment_id` | str \| None | Resulting assessment ID (when applicable) |
| `recommendation_id` | str \| None | Resulting recommendation ID (when applicable) |
| `hazard_type` | str \| None | Hazard type being assessed |
| `severity_level` | str \| None | Assessed severity |
| `confidence_raw` | float | Raw weighted confidence before adjustments |
| `confidence_adjusted` | float | Final confidence after all adjustments |
| `version` | int \| None | Assessment version number |
| `decision_type` | DecisionType enum | Type of processing step |
| `model_id` | str \| None | LLM deployment ID used |
| `prompt_template_version` | str | Version of prompt template |
| `processing_duration_ms` | float | Time spent on this step |
| `decision_rationale` | str | Human-readable explanation of decision logic |
| `generation_method` | str | llm \| template_fallback \| safety_fallback |
| `escalation_targets` | list[str] | Downstream agents targeted (if any) |
| `agent_version` | str | Semantic version of agent code |
| `configuration_version` | str | Hash of active config values |
| `incident_scope_key` | str | Partition key for Cosmos DB |
| `tenant_id` | str | live \| simulation |
| `timestamp` | datetime (UTC) | When the record was created |

**Rationale**: This consolidates both FR-029 and the Key Entities definition into a single authoritative schema. It preserves both raw and adjusted confidence for traceability (supporting CHK048's request for clarity), includes escalation_targets for multi-agent audit (supporting User Story 6), and aligns with the monitoring agent's audit record pattern for consistency.

---

## Research Task 6 — Azure Regions and Data Sovereignty (CHK063, CHK066)

**Context**: CHK063 asks for specific Azure region designations. CHK066 asks about Azure OpenAI availability in Australian regions.

**Decision**: All resources deployed in `australiaeast` (primary) and `australiasoutheast` (DR), consistent with the monitoring agent's deployment. Azure OpenAI is available in `australiaeast` with GPT-4o deployments. For `australiasoutheast` DR, LLM unavailability triggers the existing rule-based fallback with 20% confidence reduction.

**Rationale**: Same as monitoring agent — Australian data sovereignty is maintained. The rule-based fallback ensures the agent functions in DR without LLM dependency.

---

## Research Task 7 — AIDR Severity Framework Reference (CHK056)

**Context**: CHK056 asks whether AIDR severity levels are mapped to specific framework references or stated without citation.

**Decision**: The 4-level severity enum (`low`, `moderate`, `high`, `critical`) is based on AIDR Handbook Collection severity concepts (Australian Institute for Disaster Resilience — "Australian Emergency Management Handbook Series"). Formal version citation is documentation-only (README, spec clarification), not a runtime dependency. The severity definitions are:
- `low`: Minimal impact expected, routine monitoring continues
- `moderate`: Potential threat, increased monitoring and preparation recommended
- `high`: Significant threat expected within hours, protective action recommended
- `critical`: Immediate life threat, emergency protective action required

**Rationale**: AIDR provides the conceptual framework, but the system's severity computation is internally defined using signal category, confidence, and population estimates. No runtime dependency on AIDR data is introduced.

---

## Research Task 8 — Cosmos DB Unavailability for Audit (CHK047)

**Context**: CHK047 identifies a conflict between FR-034 (agent must not halt for any single dependency) and FR-028/FR-029 (audit records mandatory for every step).

**Decision**: Replicate the monitoring agent's three-tier degradation strategy:
1. **Tier 1 — Cosmos DB**: Primary append-only write path
2. **Tier 2 — Memory buffer**: Bounded in-memory ring buffer (default 10K records) when Cosmos is unavailable
3. **Tier 3 — File spill**: Local JSONL file when memory buffer is full
4. **Recovery**: Flush memory → file → Cosmos in chronological order when Cosmos recovers, annotating each record with `buffered_at` and `flush_source`

This resolves the conflict: audit records are always captured (meeting FR-028/FR-029) even when Cosmos DB is unavailable (meeting FR-034).

**Rationale**: The monitoring agent has validated this pattern in production. Replicating it ensures consistency across agents and leverages proven resilience mechanisms.

---

## Research Task 9 — Reproducibility with LLM Temperature=0 (CHK013)

**Context**: CHK013 asks whether `temperature=0` is sufficient for deterministic LLM outputs.

**Decision**: LLM `temperature=0` is necessary but not sufficient for bitwise-identical outputs across model updates or infrastructure changes. Reproducibility is defined as **semantic equivalence**: same hazard category, same severity level, same recommendation types, and same confidence level (within tolerance) — not bitwise-identical text. Each assessment stores the complete input snapshot (signal data, model deployment ID, prompt template version, configuration hash) to enable reproducibility verification and attribution of output differences to specific changes.

**Rationale**: Azure OpenAI does not guarantee bitwise-identical outputs even at temperature=0 across infrastructure updates. The spec's reproducibility requirement (FR-026, SC-004) specifies "identical hazard category, severity, and recommendation types" which is semantic equivalence, not textual identity. Storing the complete input snapshot enables post-hoc verification.
