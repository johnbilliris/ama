# Phase 1 Data Model: LLM Evaluation Framework

**Feature**: 030-llm-eval-framework
**Source**: Spec § Key Entities, FRs, and research.md D4

## Storage placement summary

| Entity | Store | Container / Path | Partition key |
|---|---|---|---|
| EvaluationCase | Blob (immutable) | `datasets/{datasetId}/{version}/cases.jsonl` | n/a |
| EvaluationDatasetVersion | Cosmos | `eval_datasets` | `/datasetId` |
| MetricDefinitionVersion | Cosmos | `eval_metric_definitions` | `/metricId` |
| JudgeModelVersion | Cosmos | `eval_metric_definitions` (kind=judge) | `/metricId` (judge bound to metric) |
| ModelUnderTest | Cosmos | `eval_runs` (kind=model_registry) | `/runId` (or registry partition `model-registry`) |
| EvaluationRun | Cosmos | `eval_runs` | `/runId` |
| Scorecard | Cosmos (summary) + Blob (`runs/{runId}/report.json` and `report.html`) | as above | `/runId` |
| SampleTrace | Blob | `runs/{runId}/traces/{caseId}.json` | n/a |
| Baseline | Cosmos | `eval_runs` (kind=baseline) | `/runId` (the run nominated as baseline) |
| ProvisioningPolicy | Cosmos | `eval_runs` (kind=policy) | `/runId` (or `policy-current`) |
| InfrastructureLifecycleRecord | Cosmos (summary) + Blob (`runs/{runId}/infra.json`) | as above | `/runId` |
| AuditEvent | Cosmos (append-only) | `eval_audit` | `/runId` |

All Blob containers under the immutable storage account use a **time-based retention policy = 7 years** (FR-021). All Cosmos containers ship with **change feed enabled** so audit projection is automatic.

---

## Entities

### EvaluationCase

Per FR-008. Stored line-per-case in the dataset's immutable JSONL; never mutated post-publication.

| Field | Type | Notes |
|---|---|---|
| `caseId` | string (ULID) | Globally unique; immutable. |
| `datasetId` | string | Parent dataset id. |
| `version` | string (semver) | Parent dataset version (denormalised). |
| `inputs` | object | Model-facing inputs (single prompt, conversation, RAG context). Schema differs by case type. |
| `expectedBehaviour` | object | Rubric: `mustInclude[]`, `mustNotInclude[]`, `expectedAction` (answer/refuse/escalate/clarify/redirect), `escalationTriggers[]`, `referToAuthority` boolean, `tone` enum (`compassionate`/`directive`/`procedural`). |
| `sensitivityLabels` | string[] | e.g., `graphic-fatality`, `human-remains`, `minor-involved`, `mass-casualty`, `prompt-injection`. |
| `hazardTags` | string[] | At least one from: `structure-fire`, `bushfire`, `flood`, `storm`, `building-collapse`, `hazmat`, `mass-casualty`, `missing-person`, `fatality-report`, `remains-recovery`, `evacuation-order`, `public-info`, `crisis-distress`. |
| `jurisdictionTags` | string[] | ISO 3166-2 codes (e.g., `AU-NSW`, `AU-VIC`). Optional. |
| `severity` | enum | `low` \| `medium` \| `high` \| `critical`. |
| `language` | string | BCP-47; v1 published values restricted to `en` / `en-AU` (FR-008). |
| `provenance` | enum | `synthetic` \| `sanitised-real`. |
| `provenanceMeta` | object | `{author, reviewer, sourceRunId?, sanitisationLog?}`. Sanitisation log required when `sanitised-real`. |
| `approvalState` | enum | `draft` \| `in-review` \| `approved` \| `rejected`. Only `approved` is published. |
| `approvalChain` | object[] | Append-only `{role, principal, action, timestamp}`. |
| `metricApplicability` | string[] | Which metrics apply (some cases skip e.g., groundedness when no retrieval). |
| `retrievalScope` | bool | Optional, default `false`. When `true`, retrieval-quality metrics (FR-001(d)) apply and `retrievedContext` MUST be populated. |
| `retrievedContext` | object[] | Optional; required iff `retrievalScope == true`. Each entry: `{docId, content, rank, relevanceLabel?}` for recall@k / precision@k / nDCG@k computation. |

**Validation**:

- `language` MUST be a valid BCP-47 code; v1 publication MUST restrict to `en*`.
- `expectedBehaviour.expectedAction == "refuse"` ⇒ `expectedBehaviour.referToAuthority` MUST be set.
- `provenance == "sanitised-real"` ⇒ `provenanceMeta.sanitisationLog` and PII-scan-pass evidence MUST be present (FR-023).
- `sensitivityLabels` MUST include at least one of `graphic-fatality`, `human-remains`, `mass-casualty` if `hazardTags` includes `fatality-report` or `remains-recovery`.

### EvaluationDatasetVersion

Per FR-009.

| Field | Type | Notes |
|---|---|---|
| `datasetId` | string | Stable per dataset family. |
| `version` | string | Semver. |
| `state` | enum | `draft` \| `published`. Once `published`, immutable. |
| `contentHash` | string | SHA-256 of the canonical JSONL bytes. |
| `caseCount` | int | ≥ 5,000 for v1 publication (FR-007). |
| `distribution` | object | Map hazard → count + percentage; validated against SC-005 minimum-share rule. |
| `languageScope` | string[] | Distinct BCP-47 codes present; v1 must equal `["en"]`/`["en-AU"]`. |
| `manifestBlobUri` | string | Pointer to `cases.jsonl` and the case-count/`distribution` manifest. |
| `publishedAt` | string (ISO-8601) | Set on transition to `published`. |
| `publishedBy` | string | Principal id. |
| `approvalChain` | object[] | Authoring + safety-reviewer approvals. |

**State transitions**:

- `draft` → `published` (one-way).
- A new dataset version (n+1) is the only way to "modify" a published dataset.

### MetricDefinitionVersion

Per FR-002, FR-003a, FR-003b.

| Field | Type | Notes |
|---|---|---|
| `metricId` | string | E.g., `groundedness`, `refusal-correctness`, `tone-appropriateness`. |
| `version` | string | Semver. |
| `family` | enum | `quality` \| `factuality` \| `groundedness` \| `retrieval` \| `safety` \| `refusal` \| `tone` \| `injection-resistance` \| `latency` \| `cost`. |
| `scoringTier` | enum | `rule-based` \| `primary-judge` \| `secondary-judge-sampled`. |
| `scale` | object | E.g., `{type:"likert", min:1, max:5}` or `{type:"binary"}`. |
| `passThreshold` | number | Pass criterion. |
| `regressionDelta` | number? | Allowed degradation vs baseline before failing the gate (quality metrics). |
| `evidenceRequired` | string[] | What must be captured to score (e.g., `model_output`, `retrieved_context`, `rationale`). |
| `applicabilityFilter` | object? | Conditions a case must satisfy for this metric to apply. |
| `judgeBinding` | object? | When `scoringTier != rule-based`: `{primaryJudgeId, primaryJudgeVersion, secondaryJudgeId?, secondaryJudgeVersion?, secondarySamplingRate}`. |
| `definitionMarkdown` | string | Human-readable definition. |
| `state` | enum | `draft` \| `active` \| `retired`. |

**Validation**:

- `scoringTier == "primary-judge"` or `"secondary-judge-sampled"` ⇒ `judgeBinding.primaryJudgeId/Version` required.
- `scoringTier == "secondary-judge-sampled"` ⇒ `judgeBinding.secondarySamplingRate` ∈ (0, 1].
- A metric in `state=active` MUST be paired with a published baseline before it is allowed in a release-gate run (FR-024).

### JudgeModelVersion

Logically distinct from MUTs (FR-003).

| Field | Type | Notes |
|---|---|---|
| `judgeId` | string | E.g., `foundry/gpt-frontier-judge`. |
| `version` | string | Foundry catalog version. |
| `deployment` | object | `{region, sku, params}`. |
| `boundMetrics` | string[] | Metric ids this judge is approved for. |
| `approvalChain` | object[] | Same shape as dataset approvals. |

### ModelUnderTest

Per FR-013, FR-014.

| Field | Type | Notes |
|---|---|---|
| `modelId` | string | Foundry catalog id. |
| `version` | string | |
| `tier` | enum | `frontier-openai` \| `mid-tier-openai` \| `phi-small` \| `other`. |
| `defaultDeploymentProfile` | object | `{region, sku, params, scaleSettings}`. |
| `policyConstraints` | object | Override hooks for `ProvisioningPolicy`. |
| `state` | enum | `registered` \| `deprecated`. |

### EvaluationRun

The central artefact (FR-014, FR-015, FR-018, FR-020, FR-026, FR-028, FR-029).

| Field | Type | Notes |
|---|---|---|
| `runId` | string (ULID) | Globally unique even for concurrent same-(model,dataset) runs (Edge Cases). |
| `mode` | enum | `ad-hoc` \| `pr-fast-subset` \| `progressive-delivery-full` \| `scheduled`. |
| `triggeredBy` | object | `{principal, source, changeRef?}` — `source` ∈ `user` / `github-actions` / `progressive-delivery` / `scheduler`. |
| `datasetRef` | object | `{datasetId, version, contentHash, subsetFilter?}`. |
| `modelRefs` | object[] | Each: `{modelId, version, deployment, params}`. |
| `metricRefs` | object[] | `{metricId, version}` snapshots. |
| `judgeRefs` | object[] | `{judgeId, version}` snapshots. |
| `provisioningPolicySnapshot` | object | The policy in force at run start (FR-018). |
| `infrastructureLifecycle` | object | Pointer to `runs/{runId}/infra.json` blob. |
| `status` | enum | `queued` \| `provisioning` \| `running` \| `succeeded` \| `failed` \| `cancelled` \| `partial`. |
| `progress` | object | `{samplesTotal, samplesDone, failuresSoFar}` — updated continuously (FR-028). |
| `startedAt` / `endedAt` | ISO-8601 | |
| `costAttribution` | object | `{currency, total, breakdown:{provision, foundryInference, judgeInference, storage}}` (FR-020). |
| `scorecardRef` | object | Pointer to scorecard blob + summary copy. |
| `baselineRef` | object? | The scorecard treated as baseline for regression analysis. |
| `evidenceBundleRef` | object? | Pointer to signed evidence zip when run completes. |

**State transitions** (status):

```text
queued ──► provisioning ──► running ──► succeeded
                  │             │
                  │             ├──► failed
                  │             ├──► cancelled
                  │             └──► partial    (per FR-029 when teardown completes but eval did not)
                  └────────────► failed (provisioning rejected by policy or by What-If)
```

Every transition MUST emit an `AuditEvent`. `partial` requires a non-empty `progress.samplesDone > 0` and a `failureReason`.

### Scorecard

Per FR-004, FR-005, FR-022.

Two views:

- **Summary** (returned by `/api/eval/scorecards/{runId}`): per-metric mean, distribution buckets, pass/fail, overall verdict, regression deltas vs baseline, model identifiers, dataset version, run metadata. Universally readable by authenticated platform staff.
- **Detail** (returned by `/api/eval/scorecards/{runId}/traces/...`): per-sample inputs, outputs, scores, judge rationales, sensitivity labels of the source case. Restricted to `eval-author`/`safety-reviewer`/`governance-reviewer` (FR-022 two-tier).

### SampleTrace

One per `(runId, modelId, caseId)`. Fields: `caseId`, `modelId`, `inputs`, `output`, `latencyMs`, `tokenUsage`, `metricScores[] = {metricId, version, tier, value, rationale, judgeId?, judgeVersion?}`, `safetyFilterTriggered`, `disambiguator` (`refused` / `failed-to-answer` / `answered`).

### Baseline

A pointer record: `{baselineId, scorecardRunId, designatedBy, designatedAt, scope: {datasetId, modelTier?, environment?}, supersededBy?}`.

### ProvisioningPolicy

Per FR-018.

| Field | Type | Notes |
|---|---|---|
| `policyId` | string | |
| `version` | string | |
| `allowedRegions` | string[] | AU regions for data services; per constitution carve-out, model-hosting endpoint regions listed separately as `allowedModelHostRegions`. |
| `allowedSkus` | string[] | |
| `maxConcurrentDeployments` | int | |
| `maxRunCostAud` | number | |
| `maxRunDurationMinutes` | int | ≤ 480 (FR-018: 8 h ceiling). |
| `prFastSubsetMaxMinutes` | int | ≤ 30 (FR-018). |
| `secondaryJudgeSamplingRate` | number | Default for metrics that don't override. |
| `evaluatorRoles` | object | `{eval, safetyReviewer, governanceReviewer}` → Entra ID app role names. |

### InfrastructureLifecycleRecord

Per FR-019.

`{runId, events[] = {timestamp, action: "provision-start"/"provision-complete"/"lease-acquired"/"deprovision-start"/"deprovision-complete"/"orphan-detected"/"orphan-cleaned", resourceType, resourceId, region, sku, costEstimateAud}, terminalState: "clean"|"orphans-cleaned"|"orphans-pending"}`.

### AuditEvent

Per FR-021.

`{eventId, runId?, datasetId?, metricId?, principal, action, before?, after?, timestamp, evidenceRefs[]}` — append-only; sealed in Cosmos with TTL=null and projected daily into the immutable Blob audit archive for the 7-year retention guarantee.

Action vocabulary (non-exhaustive): `dataset.case.draft`, `dataset.case.approved`, `dataset.version.published`, `metric.version.activated`, `judge.version.approved`, `run.queued`, `run.provisioned`, `run.started`, `run.completed`, `run.failed`, `run.partial`, `run.cancelled`, `gate.failed`, `gate.override.requested`, `gate.override.applied`, `scorecard.summary.read`, `scorecard.trace.read`, `infra.orphan.cleaned`.

---

## Cross-cutting invariants

1. Every `EvaluationRun` MUST reference a `published` `EvaluationDatasetVersion` (FR-009) — `draft` versions cannot be evaluated.
2. Every score in a `SampleTrace` MUST resolve to an `(metricId, metricVersion)` and, where applicable, a `(judgeId, judgeVersion)` that existed and was active at run start (FR-006 reproducibility, SC-006).
3. `EvaluationRun.modelRefs[].deployment` MUST be a subset of the snapshotted `provisioningPolicySnapshot.allowedRegions × allowedSkus` (FR-018).
4. An `EvaluationCase` with sensitivity label `graphic-*` MUST never appear in a Scorecard summary export — only in the gated detail tier (FR-022, SC-009).
5. No `AuditEvent` may be deleted; corrections are emitted as new compensating events.
