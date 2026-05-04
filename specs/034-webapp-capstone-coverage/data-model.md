# Phase 1 Data Model — 034 Web Application Capstone Coverage Validation

This file enumerates the entities the suite produces, asserts against, or
manages. Each entity is precisely typed (TypeScript / JSON Schema) and
linked to its source FR / clarification. The goal is to remove ambiguity
for `/speckit.tasks` decomposition and to allow CI to validate every
artefact via JSON Schema.

## Convention

- All identifiers are kebab-case strings.
- Timestamps are ISO-8601 UTC (`YYYY-MM-DDTHH:mm:ss.sssZ`).
- Booleans are explicit `true` / `false` (no truthy strings).
- `null` MUST be represented as JSON null (never omitted, never `"null"`).
- Audit identifiers (`audit_id`, `correlation_id`) are UUIDv4 strings.

## Entities

### 1. `CoverageTraceRow` — FR-004

Purpose: one row of the canonical
`specs/034-webapp-capstone-coverage/coverage-trace.{md,json}` artefact.

```typescript
type CoverageTraceRow = {
  /** Stable persona identifier from bootstrap_seed_data().identities */
  persona_id: string;                          // e.g., "ic-nsw-rfs"

  /** AIIMS function this persona occupies in the test scenario */
  aiims_function:                              // II-A function map
    | "control"
    | "operations"
    | "planning"
    | "logistics"
    | "public-information";

  /** Capstone outcome 1..5 */
  outcome: 1 | 2 | 3 | 4 | 5;

  /** Hazard pair string; pair MUST be sorted alphabetically */
  hazard: string;                              // e.g., "bushfire+extreme-heat"

  /** FR identifier (FR-001 through FR-027) the row asserts */
  fr_id: `FR-${string}`;                       // pattern: ^FR-\d{3}[a-z]?$

  /** Constitution clause(s) the test exercises (multiple allowed) */
  constitution_clauses: Array<
    | "I" | "II" | "II-A" | "III" | "IV"
    | "V" | "V-A" | "V-B" | "V-C"
    | "VI" | "VII" | "VIII"
    | "NN-1" | "NN-2" | "NN-3" | "NN-4" | "NN-5"
    | "QG-1" | "QG-2" | "QG-3"
  >;

  /** Playwright test ID (titlePath join). Multiple IDs joined with ";"
   *  in the markdown render; the JSON form uses an array. */
  test_ids: string[];                          // ≥ 1

  /** Browser route under test (path only; no host). */
  route: `/${string}`;

  /** Audit Evidence ID — id of the audit record observed within 2 s
   *  of the state-changing action. NULL only if the test is read-only. */
  audit_evidence_id: string | null;            // UUIDv4 or null

  /** Correlation id propagated through the request chain. */
  correlation_id: string;                      // UUIDv4

  /** Pass / fail signal for this assertion. */
  status: "passed" | "failing" | "flake-known" | "skipped";

  /** Wall-clock duration of the test that produced this row. */
  duration_ms: number;                         // integer ≥ 0

  /** ISO timestamp the row was emitted. */
  emitted_at: string;
};
```

JSON Schema canonicalised in
`contracts/coverage-trace-row.schema.json`.

### 2. `GapRegisterEntry` — FR-005, Q11

Purpose: one row of `specs/034-webapp-capstone-coverage/gap-register.md`
and one shadow JSONL line in
`audit/web-coverage-gaps/{date}/{hour}.jsonl`.

```typescript
type GapRegisterEntry = {
  /** Globally unique gap id, pattern: GAP-{kebab}, e.g. GAP-FR-009-IC-NSW */
  gap_id: `GAP-${string}`;

  /** Persona(s) whose tests are blocked by this gap */
  affected_personas: string[];                 // ≥ 1

  /** Route(s) implicated */
  affected_routes: Array<`/${string}`>;        // ≥ 1

  /** FR + constitution clauses involved */
  fr_ids: Array<`FR-${string}`>;
  constitution_clauses: CoverageTraceRow["constitution_clauses"];

  /** Suggested or assigned owner (GitHub team handle or "unassigned") */
  owner: string;                               // e.g., "@ama/web-team"

  /** State machine status */
  status:
    | "Open"
    | "In-Progress"
    | "Closed"
    | "Reopened"
    | "Escalated";

  /** Closure metadata; required for Closed; null otherwise */
  closing_pr_url: string | null;
  merge_sha: string | null;

  /** FR-024 cycle counter; resets to 0 on regression after Closed */
  iteration_count: number;                     // integer ≥ 0

  /** FR-027 regression metadata; non-null only on Reopened state */
  regression_evidence: null | {
    failing_test_id: string;
    reverted_commit_sha: string;
    restored_revision_sha: string;
    detected_at: string;                       // ISO-8601
  };

  /** Tribunal narrative. Free text from review-log; bounded to 2000 chars */
  tribunal_notes: string;

  /** Last transition timestamp */
  updated_at: string;

  /** Optional reference to the suite-run cycle in which this gap first opened.
   *  Sourced from CycleMetadata.cycle_id (see entity 10). Added in cycle-1
   *  amendment per spec.md Pass 5 Q26 — additive, NOT mandatory; pre-cycle-1
   *  entries set this to null. Consumers MUST handle missing/null gracefully. */
  cycle_id: string | null;
};
```

State machine invariants:

| From → To | Required fields | Side effects |
|-----------|----------------|--------------|
| (none) → Open | `gap_id`, `affected_personas`, `affected_routes`, `fr_ids`, `constitution_clauses` | append `gap.opened` audit |
| Open → In-Progress | `closing_pr_url` non-empty | append `gap.in-progress` audit |
| In-Progress → Closed | `merge_sha` non-empty AND post-merge suite run hash-passes | append `gap.closed` audit; do not increment counter |
| Closed → Reopened | full `regression_evidence` block | append `gap.regressed` audit; do **not** increment counter (regression resets the cycle) |
| Reopened → In-Progress | `closing_pr_url` non-empty | increment `iteration_count` |
| any → Escalated | `iteration_count >= 4` OR explicit `escalate` | append `gap.escalated` audit; freeze counter |

JSON Schema in `contracts/gap-register-entry.schema.json`.

### 3. `ReviewVote` — ASM-006, Q13

Purpose: one agent's contribution to one tribunal cycle.

```typescript
type ReviewVote = {
  /** Stable agent identifier (filename basename of the .agent.md file) */
  agent_id: string;                            // e.g., "qa-test-engineer"

  /** Agent panel */
  panel: "operational" | "sector" | "technical";

  /** Cycle counter (corresponds to gap iteration_count) */
  cycle: number;                               // integer ≥ 0

  /** Gap this vote applies to */
  gap_id: GapRegisterEntry["gap_id"];

  /** Personas / FRs / clauses the agent claims standing on */
  touched_personas: string[];                  // ≥ 1
  touched_frs: Array<`FR-${string}`>;
  touched_clauses: CoverageTraceRow["constitution_clauses"];

  /** The vote */
  vote: "approve" | "object" | "abstain";

  /** Required when vote != "approve" — bounded length 4000 chars */
  rationale: string;

  /** Output disposition (filled by review-log.py during panel resolution) */
  disposition:
    | "meritorious"           // ≥2/3 of relevant panel
    | "rejected"              // < 2/3 of relevant panel
    | "veto"                  // operational-panel veto on safety-critical
    | "override"              // ≥ 50% of all 85 agents override
    | "pending";              // not yet resolved

  /** ISO timestamp */
  recorded_at: string;
};
```

JSON Schema in `contracts/review-vote.schema.json`.

### 4. `KnownGoodManifest` — FR-027

Purpose: pinned restoration target for the auto-rollback path.

```typescript
type KnownGoodManifest = {
  /** Schema version — bump on incompatible changes */
  version: 1;

  /** SHA the manifest was generated against */
  commit_sha: string;

  /** SHA-256 of coverage-trace.json content (asserts trace-deterministic) */
  trace_hash: string;

  /** ISO timestamp */
  generated_at: string;

  /** Per-environment Container App revisions (from cd.yml record-revisions) */
  revisions: {
    dev: { web: string; api: string };
    staging: { web: string; api: string };
    production: { web: string; api: string };
  };

  /** Last successful run id (for cross-link to artefact storage) */
  run_id: string;

  /** Last regression event observed; null if none in this cycle */
  last_regression: null | {
    failing_test_id: string;
    reverted_commit_sha: string;
    restored_revision_sha: string;
    detected_at: string;
  };
};
```

The single live copy lives at
`specs/034-webapp-capstone-coverage/known-good.json`. Updates are
committed by the `update-known-good` step in `cd.yml` after each
successful deploy.

### 5. `PersonaFixture` — ASM-011

Purpose: typed view of a seeded identity surfaced via
`/api/test-support/personas/{id}`.

```typescript
type PersonaFixture = {
  persona_id: string;
  display_name: string;
  organisation_id: string;
  jurisdiction_id:                                            // 8 + cross + Cwlth
    | "nsw" | "vic" | "qld" | "sa" | "wa" | "tas" | "act"
    | "nt" | "commonwealth" | "cross-sector";
  role: string;                                                // Persona's organisational role title.
                                                                // Free-form (e.g. "Incident Commander",
                                                                // "Logistics Officer", "Field Coordinator",
                                                                // "Risk Manager", "BoM Forecaster",
                                                                // "NSW RFS Captain"). Constrained by the
                                                                // 68-persona inventory in spec.md §Cited
                                                                // inputs; not limited to AIIMS-5 because
                                                                // 63 of the 68 personas (sector combat
                                                                // agencies + non-AIIMS-5 operational
                                                                // roles) have organisational titles that
                                                                // do not match AIIMS function names.
                                                                // RBAC checks use `aiims_function` below,
                                                                // not this string.
  permissions: string[];                                       // RBAC verbs
  aiims_function: CoverageTraceRow["aiims_function"];          // AIIMS-5 function the persona enacts in
                                                                // the test scenario (closed enum:
                                                                // control / operations / planning /
                                                                // logistics / public-information).
                                                                // This is the field RBAC asserts against.
  direct_reports: string[];                                    // span-of-control
};
```

Markdown contract in `contracts/persona-fixture.contract.md`.

### 6. `HazardScenarioFixture` — FR-016

```typescript
type HazardScenarioFixture = {
  fixture_id: string;                          // e.g., "outcome-1-bushfire-extreme-heat"
  outcome: CoverageTraceRow["outcome"];
  hazards: [string, string];                   // alphabetically sorted pair

  /** Baseline metrics for SC-005 outcome-proxy assertions */
  baseline: {
    lives_at_risk: number | null;              // SC-001 / outcome 1
    signal_to_action_ms: number | null;        // outcome 2
    evac_lead_hours: number | null;            // outcome 3
    logistics_clicks: number | null;           // outcome 4
    economic_loss_aud: number | null;          // outcome 5
  };

  /** Seeded incident chain root */
  disaster_id: string;
  primary_incident_id: string;

  /** Affected personas (the test will stripe per persona) */
  affected_persona_ids: string[];

  /** Multilingual coverage to assert on warnings */
  warning_languages: Array<"en" | "zh-Hans" | "aus-x-atsi-placeholder">;
};
```

### 7. `EvacuationStageState` — FR-012

```typescript
type EvacuationStageState = {
  stage:
    | "shelter-in-place"
    | "advice"
    | "watch-and-act"
    | "evacuate"
    | "all-clear";
  vulnerable_populations: Array<{
    cohort: "elderly" | "disability" | "indigenous" | "pre-school" | "non-english-primary";
    count: number;
    transport_required: boolean;
  }>;
  decision_audit_id: string;                   // UUIDv4
};
```

### 8. `RecoveryEnvironmentState` — FR-013

```typescript
type RecoveryEnvironmentState = {
  environment: "built" | "economic" | "natural" | "social";
  baseline_metric: number;
  current_metric: number;
  improvement_percent: number;                 // computed; SC-005 input
  measurement_window:
    | "first-72-hours"
    | "first-week"
    | "first-30-days"
    | "first-90-days";
  data_sources: string[];                      // ≥ 3 per FR-018(a)
};
```

### 9. `AgentObjection` — Q13 + R-019

Purpose: one structured objection emitted by an agent during the
nightly tribunal. Loaded from `.github/agents/{panel}/{agent_id}.agent.md`
front-matter or a sibling `.objection.json`.

```typescript
type AgentObjection = {
  agent_id: string;
  panel: ReviewVote["panel"];
  cycle: number;
  gap_id?: GapRegisterEntry["gap_id"];          // optional: blanket objections
  touched_personas: string[];
  touched_frs: Array<`FR-${string}`>;
  touched_clauses: CoverageTraceRow["constitution_clauses"];
  rationale: string;                            // ≤ 4000 chars
  evidence: Array<{
    type: "test-failure" | "trace-row" | "audit-event" | "spec-ref";
    pointer: string;                            // e.g., "tests/e2e/web-coverage/operational/01-incident-controller.spec.ts:45"
  }>;
  proposed_remediation: string;                 // ≤ 2000 chars; required when vote=="object"
};
```

JSON Schema in `contracts/agent-objection.schema.json`.

## Cycle-1 amendment entities

> Added at plan re-run per spec.md passes 4 + 5 (Q20, Q21, Q24, Q26, Q27,
> Q28, Q29). These entities back FR-028 (outcome evaluator + audit-list
> endpoints), FR-029 (per-persona depth contract), FR-030 (net-new
> persona scenarios), and SC-012 (review-cycle outcome closure). They
> compose with — they do not replace — the cycle-0 entities above.

### 10. `CycleMetadata` — Q26 (suite-run-global metadata)

Purpose: deterministic per-run metadata emitted by the custom Playwright
Reporter at `onBegin` and persisted to
`tests/e2e/web-coverage/_artifacts/cycle-metadata.json` (gitignored).
Hosts the `cycle_start_ts` value Pass 4 Q22 originally placed on a
per-gap `GapRegisterEntry` cell — the correct home is per-run, not
per-gap. The audit-list endpoint reads `cycle_start_ts` directly from
`bootstrap_seed_data().current_cycle_start` server-side; this artefact
is the symmetric suite-side surface.

```typescript
type CycleMetadata = {
  /** ISO-8601 UTC timestamp from bootstrap_seed_data().current_cycle_start.
   *  MUST be byte-equal across re-runs on the same seed (SC-010). */
  cycle_start_ts: string;

  /** UUID v4 generated once per suite invocation. Referenced by
   *  GapRegisterEntry.cycle_id (additive, optional). */
  cycle_id: string;

  /** Full or short SHA of HEAD when the suite ran. */
  commit_sha: string;

  /** SHA-256 (lowercase hex) of the seed JSON used by
   *  bootstrap_seed_data(). Confirms the suite ran against the seed
   *  the trace assertions assume. */
  seed_hash: string;
};
```

JSON Schema in `contracts/cycle-metadata.schema.json`.

### 11. `DepthProfile` — Q20 + Q24 + Q28 (FR-029 per-persona contract)

Purpose: the per-persona scenario depth contract that the persona
spec generator under `scripts/web-coverage/_lib/persona_spec_generator.py`
consumes when emitting Playwright specs. One YAML per persona at
`tests/e2e/web-coverage/_lib/depth-profiles/{persona-id}.depth.yaml`;
68 total. A missing or invalid profile opens
`GAP-DEPTH-PROFILE-MISSING-{persona-id}` per FR-005 and blocks
`Capstone Ready` per FR-023.

```typescript
type DepthProfile = {
  /** Kebab-case persona id; MUST resolve in bootstrap_seed_data().identities (ASM-011) */
  persona_id: string;

  /** Primary workspace route the persona enters at scenario start (drawn from ASM-003) */
  workspace_route: `/${string}`;

  /** Closed enum of 12 values — first 9 cover write personas (Q20),
   *  last 3 cover read-only personas (Pass 4 Q24). Generators MUST NOT
   *  silently downgrade a read-only persona to a route-only stub. */
  safety_critical_workflow:
    | "approval"
    | "publish"
    | "allocate"
    | "decline"
    | "queue-sync"
    | "escalate"
    | "handover"
    | "declare"
    | "reopen"
    | "observe-tamper-resist"     // Q24 (a) — tamper-attempt + read-back
    | "report-generate"            // Q24 (b) — audit-derivative report
    | "export-evidence";           // Q24 (c) — briefing-acknowledgement

  /** Ordered list of UI / API actions; each step ends in a status assertion */
  workflow_steps: Array<{
    action: string;
    target_selector: string;       // role/label/test-id locator OR HTTP route — never raw CSS
    expected_response_status: number;  // 100..599
  }>;

  /** Where the post-transition state is asserted. AT LEAST ONE of
   *  evaluator_endpoint or ui_selector MUST be present (oneOf rule in schema). */
  assertion_targets: {
    /** Bound to FR-028 routable range per Pass 5 Q29 — sc-001..sc-005 only.
     *  SC-006..SC-011 are CI-artefact-derived; using them here fails validation. */
    evaluator_endpoint?: "sc-001" | "sc-002" | "sc-003" | "sc-004" | "sc-005" | null;

    /** Playwright locator on which persisted state is asserted */
    ui_selector?: string;

    /** Where the spec retrieves X-Correlation-Id for the audit-list read-back */
    audit_correlation_id_source: "header" | "response_body";
  };

  /** Capstone outcome 1..5 per FR-016; drives @outcome:N tag emission */
  capstone_outcome: 1 | 2 | 3 | 4 | 5;

  /** Constitution §III hazard catalogue (single primary hazard) */
  hazard:
    | "bushfire"
    | "tropical-cyclone"
    | "riverine-flood"
    | "severe-storm"
    | "extreme-heat"
    | "earthquake"
    | "tsunami"
    | "pandemic";

  /** Optional BCP-47 tag per FR-014 / Clarif Q2; canonical ATSI selection
   *  deferred per research.md R-008 */
  multilingual_variant?: string;

  /** Optional cross-jurisdiction reach tags per Pass 4 Q23 — folder
   *  placement pivots on owning persona; this field records reach
   *  without breaking the FR-001 naming convention */
  coverage_tags?: Array<
    | "state-government" | "territory-government" | "local-government"
    | "commonwealth" | "cross-sector" | "abc-sbs"
    | "aboriginal-torres-strait-islander" | "remote-community"
    | "critical-infrastructure" | "mutual-aid" | "dacc" | "jatwc"
  >;
};
```

JSON Schema (JSON-Schema **draft-07** — deliberately distinct from the
2020-12 schemas under `contracts/`; the spec generator's `ajv` instance
selects the meta-schema per file) at
`tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` (Phase-1
contract peer of `coverage-trace-row.schema.json` per Q28).

### 12. `EvaluatorRequest` — Q21 + Q27 (FR-028 evaluator request)

Purpose: typed request body sent by the suite to
`POST /api/outcomes/sc-{001..005}/evaluate`. Idempotency keying tuple
is `(sc_id, scenario_id, persona_id, correlation_id)`.

```typescript
type EvaluatorRequest = {
  /** Kebab-case scenario id; MUST resolve in bootstrap_seed_data() scenarios.
   *  Unknown values trigger HTTP 404 → GAP-EVALUATOR-SCENARIO-MISSING (FR-005). */
  scenario_id: string;

  /** Kebab-case persona id; MUST resolve in bootstrap_seed_data().identities
   *  per ASM-011. Fixture-only identities are forbidden. */
  persona_id: string;

  /** UUID v4 propagated via X-Correlation-Id. Idempotency tuple member. */
  correlation_id: string;

  /** Sc_id-specific shape; sourced from HazardScenarioFixture.baseline §6.
   *  Per Pass 5 Q29 the routable range is sc-001..sc-005 only. */
  metric_inputs:
    | { lives_at_risk: number }                  // sc-001
    | { signal_to_action_ms: number }            // sc-002
    | { evac_lead_hours: number }                // sc-003
    | { logistics_clicks: number }               // sc-004
    | { economic_loss_aud: number };             // sc-005
};
```

Embedded JSON Schema in `contracts/outcome-evaluator.contract.md`
(under §"Request JSON Schema"). The same contract documents the per-
`sc_id` `metric_inputs` sub-schemas.

### 13. `EvaluatorResponse` — Q21 + Q27 (FR-028 evaluator response)

Purpose: typed 200 response from
`POST /api/outcomes/sc-{001..005}/evaluate`.

```typescript
type EvaluatorResponse = {
  /** Three-state verdict (FR-028 contract). "gap" surfaces when the metric
   *  is unknowable from the available baseline + actual readings. */
  status: "pass" | "fail" | "gap";

  /** Free-form pointers to evidence rows (e.g. "audit:{audit_id}",
   *  "trace:tests/e2e/web-coverage/.../*.spec.ts"). Suite uses these to
   *  enrich coverage-trace.md cells. */
  evidence_refs: string[];

  /** Numeric metric value computed by the evaluator; null when status=="gap" */
  metric_value: number | null;

  /** Threshold the evaluator compared against; null when status=="gap" */
  threshold: number | null;

  /** UUID v4 — resolves via /api/audit/list?correlation_id={id} to an
   *  append-only audit row carrying rationale, source_refs, confidence,
   *  operator_identity. The audit append SLO is ≤ 2 s (FR-004). */
  audit_id: string;
};
```

Embedded JSON Schema in `contracts/outcome-evaluator.contract.md`
(under §"Response 200 JSON Schema").

### Cycle-1 cross-entity invariants

- `CycleMetadata.cycle_start_ts` MUST byte-equal
  `bootstrap_seed_data().current_cycle_start` (the server-side source
  read by the audit-list endpoint when `cycle=current`). Asymmetry is
  detected by the merge job's determinism check (SC-010).
- `GapRegisterEntry.cycle_id`, when non-null, MUST equal an existing
  `CycleMetadata.cycle_id` from the run during which the gap first
  opened. The field remains optional for backward compatibility.
- `DepthProfile.persona_id` MUST be one of the 68 personas in the
  FR-002 inventory. The CI gate (T177) fails if any inventory persona
  lacks a valid profile.
- `DepthProfile.assertion_targets.evaluator_endpoint`, when non-null,
  MUST be in `{sc-001..sc-005}` (Pass 5 Q29). Setting it to
  `sc-006..sc-011` fails schema validation.
- For every `EvaluatorRequest`, the suite MUST observe an audit row
  via `/api/audit/list?correlation_id={request.correlation_id}` whose
  `operator_identity.persona_id == request.persona_id` and whose
  `audit_id` matches the corresponding `EvaluatorResponse.audit_id`.
- A repeated `EvaluatorRequest` with identical
  `(sc_id, scenario_id, persona_id, correlation_id)` MUST return the
  same `EvaluatorResponse.audit_id` and the same verdict (idempotency).

## Cross-entity invariants

- Every `CoverageTraceRow.audit_evidence_id` (when non-null) MUST resolve
  to an audit record in Blob Storage with matching `correlation_id`
  within the 2-second SLO.
- For every `GapRegisterEntry.status == "Closed"`, there MUST exist at
  least one `CoverageTraceRow` whose `test_ids` intersect the gap's
  closing-PR test ids and whose `status == "passed"`.
- Every `ReviewVote.cycle` MUST equal the `iteration_count` of the
  referenced `GapRegisterEntry` at the time of recording.
- `KnownGoodManifest.trace_hash` MUST equal SHA-256 of
  `coverage-trace.json` byte content (sorted, deterministic).
- `PersonaFixture.persona_id` MUST exist in
  `bootstrap_seed_data().identities` and be the only source of identities
  consumed by tests (ASM-011).
- `HazardScenarioFixture.affected_persona_ids` MUST be a subset of
  `bootstrap_seed_data().identities[*].persona_id`.

## Validation surfaces

- Every contract above has a JSON Schema in `contracts/`, except
  `DepthProfile` whose JSON Schema lives at
  `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` (it is a
  Phase-1 contract peer per Pass 5 Q28; co-located with the data files
  it validates so the spec generator can resolve it without a
  cross-package import).
- The merge job (`web-coverage-merge`) validates
  `coverage-trace.json`, the JSONL audit shadow, and
  `_artifacts/cycle-metadata.json` against their schemas via `ajv`.
- The `web-coverage-gate` job validates these cross-entity invariants
  before posting the GitHub status check, including (cycle-1):
  - every persona in the FR-002 inventory has a valid `*.depth.yaml` (T177);
  - every captured `EvaluatorRequest` / `EvaluatorResponse` payload
    matches its embedded schema (Q27);
  - any 400 response from the evaluator is tagged `@expect:400` in the
    originating spec, otherwise the gate fails on accidental
    `sc-006..sc-011` URL references (Q29).
