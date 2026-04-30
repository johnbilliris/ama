# Feature Specification: LLM Evaluation Framework for Disaster Response

**Feature Branch**: `030-llm-eval-framework`
**Created**: 2026-04-27
**Status**: Approved (promoted by spec 032 task T006 — all tasks under spec 030 are tracked separately; status promotion gates spec-032 FR-I01)
**Input**: User description: "Develop an LLM Evaluation framework based off Microsoft best practices (Microsoft Research metric framework; Azure Architecture RAG/LLM evaluation phase) suitable for a Disaster Response Coordination Hub. Implement evaluation criteria, produce an extraordinarily large set of inputs and responses typical of disaster scenarios (including language such as fire, death, burned bodies, human remains, etc.), and provision/deprovision infrastructure to execute these evaluations against multiple Microsoft Foundry models."

## Clarifications

### Session 2026-04-27

- Q: What is the target size of the initial published evaluation dataset (v1)? → A: ~5,000 approved cases at v1, designed to grow to 10k+
- Q: What judge-model strategy should the framework use for graded metrics? → A: Hybrid: rule-based where deterministic + primary Foundry judge + secondary judge sampled for disagreement detection
- Q: Which compliance/regulatory frameworks must the evaluation evidence align to? → A: ISO/IEC 42001 + NIST AI RMF + Australian Privacy Principles
- Q: What is the initial Foundry model set under evaluation for v1? → A: Frontier OpenAI + mid-tier OpenAI + Microsoft small model (Phi family)
- Q: Which surface(s) trigger and consume the release-gate scorecard? → A: GitHub Actions PR check (path-scoped) + AMA progressive-delivery promotion gate, sharing one scorecard
- Q: Maximum end-to-end runtime for a full multi-model evaluation run? → A: ≤ 8 hours (PR gate uses fast subset; full run fits within an overnight window)
- Q: How long must evaluation run artifacts and audit records be retained? → A: 7 years (aligned with ISO/IEC 42001, APP, and Australian public-sector record-keeping baselines)
- Q: What is the dataset's language scope at v1? → A: English-only at v1, with schema-ready support for additional languages in later versions
- Q: How are concurrent requests for the same model+dataset combination handled? → A: Run independently with distinct identifiers; each requester gets their own scorecard
- Q: Who can read scorecards and sample-level traces? → A: Two-tier internal — summary visible to all platform staff; sample-level traces gated to eval/safety/governance roles

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare candidate Foundry models against disaster-domain criteria (Priority: P1)

A platform owner responsible for the Disaster Response Coordination Hub needs evidence that any LLM powering operator-facing or public-facing assistants behaves correctly, safely, and consistently when handling distressing disaster content (fatalities, casualties, missing persons, fire spread, evacuation orders, hazardous materials). They launch an evaluation run that scores each candidate model on the same fixed dataset, using the same metrics, and produces a side-by-side report so leadership can choose a model with documented justification.

**Why this priority**: Without this, model selection for life-safety scenarios is unfounded. P1 because every other story (curated datasets, ephemeral infra, regression gating) only delivers value once a comparable scorecard exists.

**Independent Test**: Trigger an evaluation run with at least two registered Foundry models against the disaster evaluation set; confirm the system returns a single comparable report containing per-metric scores, pass/fail verdicts against thresholds, sample-level traces, and an overall recommendation.

**Acceptance Scenarios**:

1. **Given** two or more Foundry models are registered and a disaster-domain dataset is published, **When** an evaluator starts a comparison run, **Then** the system produces a report showing each model's score on every defined metric (quality, groundedness, safety, refusal correctness, tone appropriateness), the dataset version evaluated, and a clear winner per metric and overall.
2. **Given** an evaluation run is in progress, **When** the evaluator opens the run, **Then** they can see live progress (samples processed, samples remaining, failures so far) and cancel the run cleanly without leaving infrastructure orphaned.
3. **Given** an evaluation run completes, **When** the evaluator exports the report, **Then** the export includes the dataset hash, model identifiers and versions, metric definitions, raw model outputs, scoring rationales, and reproducibility metadata sufficient for an external reviewer to re-run the evaluation.

---

### User Story 2 - Curate and govern a disaster-scenario evaluation dataset (Priority: P1)

A response operations subject-matter expert and a safety reviewer collaborate to curate evaluation cases that mirror real coordination work: triaging incoming reports about fires, building collapses, deceased persons, recovery of human remains, hazardous spills, missing children, evacuation refusals, and crisis hotline interactions. They author cases that include sensitive language (fire, death, burned bodies, human remains, mass casualty), expected behaviour (when to answer, when to refer to authorities, when to trigger escalation), and tags for jurisdiction, hazard type, and severity. The dataset grows to thousands of cases and is versioned so prior evaluations remain reproducible.

**Why this priority**: The framework is only as credible as its dataset. Without a large, curated, governed dataset, results from Story 1 are not defensible. P1 alongside Story 1.

**Independent Test**: An SME authors and publishes a labelled dataset; a safety reviewer approves it; the system produces a versioned, immutable dataset artifact that Story 1's evaluation runs can target by version.

**Acceptance Scenarios**:

1. **Given** a draft case containing graphic disaster language and an expected behaviour rubric, **When** the SME submits it for review, **Then** the case is flagged with appropriate sensitivity labels, routed to a safety reviewer, and only added to a publishable dataset version after approval.
2. **Given** a published dataset version, **When** anyone modifies its contents, **Then** the system requires creating a new version and preserves the prior version unchanged so historical evaluations remain reproducible.
3. **Given** the dataset, **When** an evaluator filters it (e.g., only fatality-related cases, only NSW jurisdiction, only severity ≥ high), **Then** an evaluation run can target that subset and the report records exactly which subset was used.

---

### User Story 3 - Provision and deprovision evaluation infrastructure on demand (Priority: P1)

An evaluation engineer triggers a run; the system provisions the Foundry model deployments and any supporting evaluation compute needed for that run, executes the evaluation, captures all results to durable storage, then deprovisions all transient infrastructure. Costs and quotas are bounded by policy. The platform owner receives a per-run cost summary.

**Why this priority**: Disaster-domain evaluations need many model variants but cannot afford to leave expensive Foundry deployments running between runs. Ephemeral provisioning is the primary cost and security control. P1 because without it, Story 1 either runs against shared production deployments (risk) or accumulates idle cost.

**Independent Test**: Trigger an evaluation against a model not currently deployed; observe that the model deployment is created, used, and removed; confirm post-run that no transient evaluation resources remain and a cost record has been written.

**Acceptance Scenarios**:

1. **Given** a model is registered but not currently deployed, **When** an evaluation run targets it, **Then** the system provisions the deployment within policy limits (region, SKU, quota), executes the evaluation, and tears the deployment down on success or failure.
2. **Given** an evaluation run fails midway, **When** the failure is detected, **Then** the system still deprovisions all transient infrastructure created for that run and records the failure with full context.
3. **Given** an evaluation run completes, **When** the evaluator views run details, **Then** they see the resources that were created, when they were torn down, and the estimated cost attributed to the run.

---

### User Story 4 - Gate releases with regression evaluation (Priority: P2)

When a developer changes a prompt template, retrieval pipeline, or model selection in the Disaster Response Hub, an automated evaluation run executes against the canonical dataset. The change is blocked from merging if any safety metric regresses below threshold or if quality regresses by more than an allowed delta versus the current production baseline.

**Why this priority**: Critical for ongoing safety, but depends on Stories 1-3 being usable. P2.

**Independent Test**: Submit a change that intentionally degrades a safety-relevant prompt; confirm the gate fails with a clear, sample-level diagnostic and the change cannot be merged until either rolled back or explicitly overridden by an authorised approver.

**Acceptance Scenarios**:

1. **Given** a baseline scorecard exists for the current production configuration, **When** a proposed change is evaluated, **Then** the system reports each metric's delta versus baseline and marks regressions exceeding policy thresholds.
2. **Given** a regression is detected on a safety metric, **When** an approver attempts to override the gate, **Then** the override requires a documented justification, is logged immutably, and notifies the safety reviewer.

---

### User Story 5 - Audit and explain a past evaluation (Priority: P2)

A governance reviewer investigates an incident or a leadership question ("why did we choose model X six months ago?"). They open the historical evaluation run and see the exact dataset version, the model identifiers and versions, the metric definitions in force at that time, every input/output pair with its score and rationale, and the approval chain.

**Why this priority**: Necessary for governance and post-incident review, but only useful once runs and datasets exist. P2.

**Acceptance Scenarios**:

1. **Given** an evaluation run from an arbitrary prior date, **When** the reviewer opens it, **Then** every artifact (dataset version, model versions, metric definitions, scoring outputs, approval chain) is retrievable without external reconstruction.
2. **Given** a sample within a past run, **When** the reviewer requests the rationale, **Then** the system returns the original scoring rationale (rule-based or judge-model-based) recorded at run time, not a re-computed one.

---

### User Story 6 - Continuously expand the dataset from real (sanitised) operations (Priority: P3)

Operations leads identify representative real interactions (with PII removed and consent/policy clearance) and propose them as new evaluation cases, with an expected-behaviour rubric. The dataset grows steadily from synthetic seed cases toward operationally grounded cases.

**Why this priority**: Important for long-term credibility, but synthetic seed cases are sufficient for the framework's initial usefulness. P3.

**Acceptance Scenarios**:

1. **Given** a candidate real interaction, **When** an operations lead proposes it, **Then** the system enforces PII removal and reviewer approval before publication.

---

### Edge Cases

- A case contains content so graphic it triggers Foundry safety filters: the system MUST distinguish "model correctly refused dangerous request" from "model failed to answer a legitimate request" and score accordingly.
- A dataset case asks a question that has no single correct answer (e.g., "Is it safe to re-enter the building?"): the rubric must allow scoring on the *form* of the answer (uncertainty acknowledgement, referral to authority) rather than a specific factual match.
- Foundry quota is exhausted mid-run: the run pauses, partial results are preserved, and provisioned infrastructure is torn down within policy timeout regardless.
- Two evaluators trigger the same model+dataset combination concurrently: the system MUST run them independently with distinct run identifiers; results are never silently merged or overwritten. Cost remains bounded by the per-run cost cap (FR-018).
- A model returns an empty or malformed response: it is recorded as such, scored against the rubric (typically failing), and does not crash the run.
- A judge model used for grading is itself updated: the change creates a new metric definition version; prior runs retain their original judge version for reproducibility.
- A dataset case contains language that could be interpreted as instructions to the model rather than data about an event (prompt-injection-like): the framework MUST detect and report such cases as a separate metric class rather than silently letting them influence behaviour.
- A run is cancelled or the orchestrator process dies: a reconciliation process detects orphaned infrastructure within a bounded time window and tears it down.

## Requirements *(mandatory)*

### Functional Requirements

**Evaluation criteria and metrics**

- **FR-001**: The framework MUST support, at minimum, the following evaluation metric families derived from Microsoft's published guidance: (a) response quality (relevance, completeness, fluency, coherence), (b) factual correctness against ground truth where ground truth exists, (c) groundedness/faithfulness against retrieved context for retrieval-augmented use, (d) retrieval quality (recall and precision of retrieved context where retrieval is in scope), (e) safety and harm avoidance (including handling of graphic disaster content), (f) refusal correctness (refuse when appropriate, answer when appropriate), (g) tone and operational appropriateness (compassion, clarity, directive accuracy for emergency contexts), (h) prompt-injection resistance, and (i) latency and cost as operational metrics.
- **FR-002**: Each metric MUST have a versioned, written definition including its scoring scale, the evidence required to score it, whether it is rule-based or judge-model-based, and the pass threshold for disaster-response use.
- **FR-003**: Where a judge model is used, the judge model identifier and version MUST be recorded with every score it produces.
- **FR-003a**: The framework MUST score graded metrics using a hybrid strategy: (i) rule-based scoring wherever a deterministic check is sufficient (e.g., refusal-keyword presence, exact-match factuality, structured-output shape, escalation-trigger detection); (ii) a designated primary Foundry judge model for remaining metrics requiring semantic judgment (e.g., groundedness, tone appropriateness, refusal correctness, prompt-injection resistance); (iii) a designated secondary independent Foundry judge model invoked on a configurable sampled subset of cases per run to detect primary-judge bias or drift. Disagreements between primary and secondary judges on sampled cases MUST be surfaced in the run report.
- **FR-003b**: For every metric, the metric definition MUST declare its scoring tier (rule-based, primary-judge, secondary-judge-sampled) and the percentage of run cases scored by each tier. The sampling rate for the secondary judge MUST be a configurable property of the metric definition and is recorded with every run.
- **FR-004**: The framework MUST produce per-sample scores AND aggregated metrics (mean, distribution, pass rate, regression delta) per model per dataset version per run.
- **FR-005**: The framework MUST produce a single human-readable scorecard and a machine-readable export of every run.

**Disaster-domain dataset**

- **FR-006**: The framework MUST ship with an initial curated evaluation dataset of disaster-coordination cases covering at least: structure fires, bushfires, floods, severe storms, building collapses, hazardous material incidents, mass casualty events, missing persons (including minors), fatality reporting, recovery of human remains, evacuation orders and refusals, public information requests, and crisis-distress interactions.
- **FR-007**: The initial published dataset (v1) MUST contain approximately 5,000 approved cases distributed across the hazard categories in FR-006, and the system MUST NOT prevent the dataset from growing to 10,000+ cases over subsequent versions.
- **FR-008**: Each case MUST contain: a unique identifier, the input(s) the model receives, the expected behaviour rubric (what a correct response looks like, including when to refuse or escalate), sensitivity labels, jurisdiction and hazard tags, severity, language code (BCP-47), and provenance (synthetic vs sanitised real, author, reviewer, approval state). The v1 published dataset MUST contain English-language cases only (`en`/`en-AU`); the case schema and dataset model MUST accommodate additional languages in subsequent versions without a breaking schema change.
- **FR-009**: The dataset MUST be immutably versioned: a published version cannot be altered; modifications produce a new version; every evaluation run records the exact version it used.
- **FR-010**: The dataset MUST support filtering and stratified subsetting (by hazard, jurisdiction, severity, sensitivity, provenance) such that runs can target a defined subset and the run record specifies the subset.
- **FR-011**: Authoring and publication MUST require a safety-reviewer approval step before a draft case is included in a publishable dataset version.
- **FR-012**: Cases that depict graphic content (fire fatalities, burned bodies, human remains, mass casualty) MUST be permitted in the dataset for evaluation purposes, MUST be sensitivity-labelled, MUST be access-controlled, and MUST be clearly marked in any export so downstream consumers handle them appropriately.

**Multi-model execution against Microsoft Foundry**

- **FR-013**: The framework MUST evaluate models hosted on Microsoft Foundry, supporting at minimum a configurable list of frontier and small-language Foundry-catalog models so that new models can be added without code changes. The v1 evaluable set MUST include at minimum three models spanning capability/cost tiers: (i) a frontier OpenAI-family model on Foundry, (ii) a mid-tier/cost-efficient OpenAI-family model on Foundry, and (iii) a Microsoft small-language model from the Phi family on Foundry. The exact catalog identifiers and versions are recorded per FR-014 and are configurable.
- **FR-014**: For every run, the framework MUST record the exact model identifier, version, deployment configuration (region, SKU, parameters such as temperature and max tokens), and the date/time window of execution.
- **FR-015**: The framework MUST execute the same dataset version against multiple models in a single comparison run and report results comparably.

**Ephemeral provisioning and deprovisioning**

- **FR-016**: The framework MUST be able to provision the infrastructure required to execute a run (Foundry model deployments and any supporting evaluation compute or storage) on demand, scoped to the run's lifetime.
- **FR-017**: The framework MUST deprovision all transient infrastructure when a run ends, regardless of whether the run succeeded, failed, or was cancelled.
- **FR-018**: The framework MUST enforce policy-based limits on provisioning: allowed regions, allowed SKUs, maximum concurrent deployments, maximum estimated run cost, and maximum run duration; runs exceeding limits MUST be rejected before infrastructure is created. The maximum end-to-end duration of a full multi-model run (full v1 dataset × the v1 model set × the metric suite, including secondary-judge sampling) MUST NOT exceed 8 hours; the PR-gate trigger MUST run against a stratified fast subset bounded to ≤ 30 minutes.
- **FR-019**: The framework MUST run a reconciliation process that detects and removes orphaned transient infrastructure (e.g., from a crashed orchestrator) within ≤ 60 minutes after the policy's `maxRunDurationMinutes` elapses.
- **FR-020**: The framework MUST record per-run cost attribution and surface it in the run report.

**Governance, safety, and audit**

- **FR-021**: All evaluation runs, dataset versions, metric-definition versions, judge-model versions, approval decisions, and gate overrides MUST be recorded in an immutable audit log retrievable per run, retained for at least 7 years from the run's completion date. The audit-event schema and retention MUST be sufficient to produce evidence packages mapped to ISO/IEC 42001 (AI Management System) controls and NIST AI RMF functions (Govern, Map, Measure, Manage).
- **FR-022**: Access to evaluation datasets containing graphic content MUST be role-controlled and access events MUST be logged. Access controls and logging MUST satisfy the Australian Privacy Principles (APPs) for any case derived from real interactions. Scorecard access MUST be two-tiered: (i) summary scorecards (per-metric scores, deltas, pass/fail, model identifiers, dataset version, run metadata) are readable by all authenticated platform staff to support transparent model-selection decisions; (ii) sample-level traces (raw inputs, raw model outputs, judge rationales, full audit detail) are restricted to evaluation, safety-reviewer, and governance roles, with every access event logged. Scorecards and traces are not redistributed outside the organisation.
- **FR-022a (development environment exception)**: In the **development environment only**, the evaluation API MAY accept anonymous, public-facing requests so an operator can exercise the full pipeline against synthetic data without standing up an Entra ID app registration or issuing tokens. When anonymous access is enabled, the API MUST (a) tag every audit event with `principal=anonymous` and `environment=dev`, (b) reject any access to real-interaction-derived cases or cases carrying sensitivity labels other than the synthetic dev dataset, and (c) refuse to start if `ENVIRONMENT != "dev"`. Staging and production deployments MUST continue to enforce the full Tier-1/Tier-2 role model from FR-022 with no anonymous access permitted.
- **FR-023**: The framework MUST never store unredacted personally identifiable information from real operational interactions; cases derived from real interactions MUST pass a documented PII-removal step before publication, and the de-identification approach MUST align with the Australian Privacy Principles (APP 11 Security and APP 6 Use/Disclosure).
- **FR-024**: The framework MUST provide a release-gate mode in which a proposed change is evaluated against a baseline and rejected if any safety metric falls below threshold or any quality metric regresses beyond an allowed delta; gate overrides MUST require justification and approver identity, both logged. The release gate MUST be invokable from two surfaces sharing a single scorecard per change: (i) a GitHub Actions required check on pull requests whose changed paths include prompt templates, retrieval configuration, model selection, or metric/dataset versions; and (ii) the AMA progressive-delivery promotion pipeline (feature 029) at promotion time between environments.
- **FR-025**: The framework MUST clearly distinguish, in scoring, between "model correctly refused" and "model failed to answer" so that safety filters do not mask quality problems and vice versa.

**Reproducibility and operations**

- **FR-026**: Any past run MUST be reproducible end-to-end from its recorded artifacts: same dataset version, same model version, same metric and judge versions, same parameters.
- **FR-027**: The framework MUST allow runs to be triggered ad-hoc by an authorised user, on a schedule, or by an automated pipeline. Automated triggers behave as defined in FR-024 (one scorecard per change powering both the path-scoped GitHub Actions PR check and the AMA progressive-delivery promotion pipeline).
- **FR-028**: The framework MUST surface live progress and allow clean cancellation of in-flight runs.
- **FR-029**: The framework MUST support partial-result preservation when a run cannot complete (quota exhaustion, infrastructure failure, cancellation).

### Key Entities

- **Evaluation Case**: A single input or conversation given to a model under test, with an expected-behaviour rubric, sensitivity labels, hazard/jurisdiction/severity tags, provenance, and approval state.
- **Evaluation Dataset (Version)**: An immutable, versioned collection of approved cases with a content hash, an authoring history, and an approval chain.
- **Metric Definition (Version)**: A versioned specification of one metric: scale, scoring method (rule-based or judge-model-based), required evidence, pass threshold, and applicability conditions.
- **Judge Model (Version)**: A model used to score outputs against rubrics; recorded separately from the model under test, with its own identifier and version.
- **Model Under Test**: A registered Foundry model with identifier, version, deployment configuration profile, and policy constraints.
- **Evaluation Run**: A single execution that pairs a dataset version with one or more models under test and one set of metric-definition versions; records inputs, outputs, scores, rationales, infrastructure lifecycle, cost, and outcome.
- **Scorecard**: The per-run, per-model summary produced from a run, including pass/fail per metric and overall verdict.
- **Baseline**: A designated scorecard treated as the comparison point for regression gating.
- **Provisioning Policy**: The set of allowed regions, SKUs, concurrency limits, cost caps, and duration caps that bound any provisioning action.
- **Infrastructure Lifecycle Record**: A per-run record of resources created, their lifetimes, the deprovisioning event, and any orphan-cleanup events.
- **Audit Event**: An immutable record of an authoring, approval, run, override, or access action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Platform leadership can answer "which Foundry model should we use for the Disaster Response Hub, and why?" by pointing at a single current scorecard, without further analyst work.
- **SC-002**: An evaluation run targeting at least three Foundry models against the full disaster dataset completes end-to-end (provision → evaluate → deprovision → report) within 8 hours and without manual infrastructure intervention in 100% of runs in a representative validation week.
- **SC-003**: After any successful or failed run, zero transient evaluation resources remain provisioned beyond the policy timeout, verified by automated reconciliation.
- **SC-004**: 100% of evaluation runs are reproducible from their recorded artifacts by a reviewer who was not involved in the original run.
- **SC-005**: The initial published disaster dataset contains enough approved cases across all required hazard types that no single hazard type contributes less than a defined minimum share of the run, ensuring no metric is dominated by a single scenario. The minimum-share floor is owned by the safety-reviewer role and codified in `packages/eval-dataset/generation/distribution-v1.json`.
- **SC-006**: For every run, every score is traceable to the exact case, model output, metric definition version, and (where applicable) judge model version that produced it.
- **SC-007**: A change that demonstrably degrades safety behaviour (verified by an authored regression case) is blocked by the release gate on first attempt, with a sample-level diagnostic identifying the regression.
- **SC-008**: Cost per evaluation run is reported with each run and stays within the provisioning-policy cap in 100% of runs; runs that would exceed the cap are rejected before provisioning.
- **SC-009**: Safety-sensitive content (graphic disaster language including fatalities, burned bodies, human remains, mass casualty) is handled correctly by the framework: it is preserved in the dataset for evaluation, access is logged, and it is never leaked into channels (logs, exports, dashboards) lacking appropriate sensitivity controls.
- **SC-010**: A new Foundry model can be added to the evaluable set without code changes and produce a comparable scorecard on the existing dataset within a single run.
- **SC-011**: When a run is cancelled or fails, partial results are preserved and visible, and the run record clearly indicates the run's incomplete status.
- **SC-012**: A governance reviewer can retrieve any past run's full evidence chain (dataset version, model versions, metric/judge versions, scores, rationales, approvals, overrides) without contacting the original team.

## Assumptions

- The Disaster Response Hub already has a model-using component (assistant, summariser, triage helper, or RAG flow) whose behaviour this framework evaluates; this spec does not redefine that component's purpose.
- "Microsoft Foundry" refers to the Azure-hosted model catalogue and deployment surface; models will be addressable by catalog identifier and version.
- Curated synthetic cases are an acceptable initial source for the dataset; sanitised real operational cases are an additive source over time, not a precondition.
- Sensitive but non-illegal graphic language describing real disaster phenomena (fire, death, burned bodies, human remains, mass casualty, missing persons including minors) is in scope for evaluation purposes; content that would itself be illegal to store is out of scope and does not need to be represented.
- Existing organisational governance (audit, RBAC, retention) for the broader platform will be reused; this framework adds run-level and case-level audit on top, not a parallel system. Compliance alignment targets are ISO/IEC 42001 (AI Management), NIST AI RMF, and the Australian Privacy Principles; sector-specific certifications (e.g., emergency-services regulator schemes, ISO 27001) are not in scope for this feature.
- Cost and quota policies will be defined and owned by the platform owner; this spec requires the framework to enforce such policies but does not set their numeric values.
- Standard industry defaults apply to non-functional concerns not specified here (authentication, retention, error UX) and will be reconciled to the AMA platform's existing standards during planning.

## Out of Scope

- Building or fine-tuning the Foundry models themselves.
- Replacing the production assistant or RAG pipeline; this framework evaluates them.
- Real-time live monitoring of production traffic (this is a candidate follow-on, not part of this feature).
- Human red-teaming workflows beyond the safety-reviewer approval and dataset authoring described here.
- Open-ended dataset distribution outside the platform; sensitive cases are not redistributed.
