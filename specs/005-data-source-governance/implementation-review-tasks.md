# Implementation Review: 005 Data Source Governance

**Review date:** 2026-09-11. **Baseline:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
HEAD matched the requested baseline; the inspected implementation/specification paths had no tracked differences from it.
**Method:** isolated, static source and test-assertion audit. No delegation, product execution, deployment, fixes, or approval activity.
**Coverage:** 57/57 original tasks, 38/38 FR/NFR/SC identifiers, 15/15 acceptance scenarios, six/six edge cases.
All 57 original task boxes are `[X]`; those historical marks are not verification results. There are **28 unchecked follow-ups** below.

## Findings First

P0 denotes a critical application-level safety/security gap; P1 denotes a substantial correctness or integrity gap;
P2 denotes an assurance, contract, or evidence gap. These priorities do not assert an observed production incident.

| Priority | Finding and controlling evidence | Follow-up |
| --- | --- | --- |
| P0 | Governance authorization is not attached to either router. Helpers trust a role header but have no route callers; production Entra/RBAC middleware protects different prefixes. Mutations also accept supplied assessor/assigner identities or use `api-user`. See [helpers and router](../../apps/api/app/api/governance.py#L42), [registration](../../apps/api/app/api/data_sources.py#L38), [Entra prefixes](../../apps/api/app/middleware/entra_auth.py#L38), and [RBAC prefixes](../../apps/api/app/middleware/rbac_check.py#L32). | AUD-001 |
| P0 | Non-compliance/deactivation does not gate active ingestion. The signal endpoint reaches a service that writes signals without a registry lookup; the polling base also processes payloads without governance eligibility. Blocking a new assignment is not blocking ingestion or an existing chain. See [signal entry](../../apps/api/app/api/routes/signals.py#L14), [signal write](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12), [polling base](../../apps/api/app/services/ingestion/pipeline_base.py#L192), and [assignment-only gate](../../apps/api/app/services/governance_registry.py#L263). | AUD-002 |
| P1 | Failed re-review immediately derives `non_compliant`; it never starts the required grace period. Grace start and expiry are callable helpers without operational callers in the searched application paths. Tests manually call them. See [derivation](../../apps/api/app/services/governance_registry.py#L157), [grace helpers](../../apps/api/app/services/governance_registry.py#L193), and [manual expiry test](../../tests/integration/test_governance_grace_period.py#L80). | AUD-003 |
| P1 | One compliant principle can approve the whole source, and one assessment suppresses the assessment-gap indicator. The purported all-compliant test assesses only two principles. See [derivation](../../apps/api/app/services/governance_registry.py#L157), [gap detection](../../apps/api/app/services/governance_registry.py#L363), and [two-principle assertion](../../tests/contract/test_constitutional_compliance.py#L98). | AUD-004 |
| P1 | Mutations, supersession/revocation, derived status, and audit writes are separate writes without conditional concurrency or a transaction. A later write failure can leave committed changes without their audit; concurrent replicas can create multiple current/active records. See [assessment sequence](../../apps/api/app/services/governance_registry.py#L110), [assignment sequence](../../apps/api/app/services/governance_registry.py#L263), and [unconditional upserts](../../apps/api/app/repositories/governance_repository.py#L270). | AUD-005 |
| P1 | The audit is neither storage-enforced append-only nor sufficient for replay. Cosmos uses upsert for audit IDs, models are mutable, and events omit complete registration/assessment/chain state and implicit primary revocations. See [audit model](../../packages/domain/src/domain/models/governance_audit.py#L36), [audit persistence](../../apps/api/app/repositories/governance_repository.py#L456), and [registration event](../../apps/api/app/services/governance_registry.py#L71). | AUD-006 |
| P1 | Request tenant context does not constrain governance source, assessment, assignment, precedence, or cache access. Storage partitions by source ID, not an authenticated scope; audit defaults to `live`. A globally shared public catalogue may be legitimate, but no policy separates it from sensitive tenant/agency decisions. See [tenant context](../../apps/api/app/middleware/tenant_middleware.py#L35), [source persistence](../../apps/api/app/repositories/governance_repository.py#L296), and [audit tenant default](../../packages/domain/src/domain/models/governance_audit.py#L45). | AUD-007 |
| P1 | Re-review only appends events. It does not flag assessments, record Constitution/source versions, track pending work, or expose amendment activation; dashboard `rereview_pending` is hardcoded to zero. See [triggers](../../apps/api/app/services/governance_registry.py#L172) and [zero counter](../../apps/api/app/services/governance_registry.py#L406). | AUD-008 |
| P1 | The assessor UI has six labels, not the required principle-specific criteria. The pinned six-principle/v1.0.1 model also lacks reconciliation with the current v1.2.0 Constitution and its changed structure. See [form](../../apps/web/src/components/governance/AssessmentForm.tsx#L5), [assessment enum](../../packages/domain/src/domain/models/constitutional_assessment.py#L6), and [current Constitution](../../.specify/memory/constitution.md#L315). | AUD-009 |
| P1 | CRUD and governance instantiate different repositories. Without `COSMOS_ENDPOINT`, their dictionaries diverge: registration/listing and compliance do not share a registry. Only the governance instance is seeded; a failed seed attempt is permanently marked attempted. Cosmos support is real, not absent. See [CRUD instance](../../apps/api/app/api/data_sources.py#L11), [governance bootstrap](../../apps/api/app/api/governance.py#L60), and [backend selection](../../apps/api/app/repositories/governance_repository.py#L37). | AUD-010 |
| P1 | Registration accepts empty mandatory metadata; PATCH accepts arbitrary status strings and uses unvalidated `setattr`. Blank explanations/identities and lists containing blank conditions also pass server-side checks. See [request models](../../apps/api/app/api/data_sources.py#L14), [update service](../../apps/api/app/services/governance_registry.py#L87), and [assessment validation](../../apps/api/app/services/governance_registry.py#L110). | AUD-011 |
| P1 | Trust/rank compatibility is broken for legacy rank-only records and updates. Construction overwrites an existing rank using default tier 7; PATCH changes tier without running that validator. No effective input-bound derived-trust calculation is represented in this model. See [defaults and validator](../../packages/domain/src/domain/models/data_source.py#L45) and [construction-only test](../../tests/contract/test_data_source_registry.py#L46). | AUD-012 |
| P1 | Deactivation lacks the active-incident/chain guard, and generic PATCH can resurrect a terminal deactivated source or bypass deactivation metadata. See [deactivation](../../apps/api/app/services/governance_registry.py#L98), [PATCH](../../apps/api/app/services/governance_registry.py#L87), and [required transitions](data-model.md#L34). | AUD-013 |
| P1 | Catalogue validation is a fixed five-name set. The referenced spec-004 catalogue instead explicitly lists development-time actor agents, so simply loading all its names would also be wrong. No rename/removal detection or mapping contract exists in this path. See [static set](../../apps/api/app/validators/governance_validators.py#L5), [literal model](../../packages/domain/src/domain/models/agent_governance.py#L6), and [catalogue purpose](../../.github/agents/AGENTS.md#L11). | AUD-014 |
| P1 | Chain validation checks names, continuity, and confidence, but not payload compatibility, positive/contiguous step numbering, or the existence of a primary assignment. `payload_contract_ref` is inert text. See [validator](../../apps/api/app/validators/governance_validators.py#L40), [chain service](../../apps/api/app/services/governance_registry.py#L288), and [step model](../../packages/domain/src/domain/models/handoff_chain.py#L22). | AUD-015 |
| P1 | Changing the primary assignment can leave an incompatible active chain. Compliance/grace/deactivation changes do not rederive governance status, so a rejected source can remain labelled `fully_governed`; assessment after assignment can leave the inverse stale state. See [assignment](../../apps/api/app/services/governance_registry.py#L263), [derivation](../../apps/api/app/services/governance_registry.py#L326), and [compliance derivation](../../apps/api/app/services/governance_registry.py#L157). | AUD-016 |
| P1 | Precedence accepts nonexistent/unapproved/deactivated source references and duplicate hazard/jurisdiction rules. Inheritance is implemented in repository helpers but not exposed as an effective-resolution operation; equal-tier human escalation is not implemented there. Generic contradiction detection elsewhere is not this resolver. See [set](../../apps/api/app/services/governance_registry.py#L344), [storage/resolution](../../apps/api/app/repositories/governance_repository.py#L393), and [contradiction detector](../../apps/agents/risk_assessment/correlation.py#L132). | AUD-017 |
| P1 | The governance cache is process-local, deletes expired entries, and has no registry-outage fallback or safe-default result. Only HTTP chain replacement invalidates it; other eligibility mutations and replicas do not. See [cache](../../apps/api/app/services/governance_cache.py#L9) and [lookup](../../apps/api/app/api/governance.py#L252). Agent-runtime consumption remains explicitly deferred. | AUD-018 |
| P1 | The default dashboard cannot reflect live governance changes: its data service is constructed without the repository. Seed availability is counted as compliance, matrix fallback invents current assessment dates with zero gaps, and detail returns empty history, even for unknown IDs. See [composition](../../apps/api/app/api/routes/governance_dashboard.py#L71), [statistics](../../apps/api/app/services/governance_data_service.py#L230), [matrix](../../apps/api/app/services/governance_data_service.py#L623), and [detail](../../apps/api/app/services/dashboard_aggregation_service.py#L185). | AUD-019 |
| P1 | The complete planner/architect workflow is not available in the UI. Source administration is a placeholder; there is no assignment creation control; legacy list/assignment/editor requests use the wrong default prefix; category filters are never editable and failed chain saves can look successful. The newer assessment form is real and is credited. See [placeholder](../../apps/web/src/app/governance/data-sources/page.tsx#L22), [assignment fetch](../../apps/web/src/app/governance/%5BdataSourceId%5D/assignments/page.tsx#L28), and [editor save](../../apps/web/src/components/governance/HandoffChainEditor.tsx#L49). | AUD-020 |
| P2 | Contract drift includes absent/ignored `agent_name`, `from_dt`/`to_dt` instead of `from`/`to`, cache status in JSON instead of its header, missing audit-source 404, and inconsistent error schemas/invalid-date handling. See [list signature](../../apps/api/app/api/data_sources.py#L49), [dashboard](../../apps/api/app/api/governance.py#L268), [audit](../../apps/api/app/api/governance.py#L298), and [OpenAPI](contracts/openapi-governance.yaml#L15). | AUD-021 |
| P2 | Gap detection, stored gap counts, and summary presentation disagree. Secondary-only assignments hide a missing primary; missing chains are not surfaced; current cards omit assigned and re-review counts. See [gap logic](../../apps/api/app/services/governance_registry.py#L363), [default gap field](../../packages/domain/src/domain/models/data_source.py#L55), and [cards](../../apps/web/src/components/governance/GovernanceSummary.tsx#L20). | AUD-022 |
| P2 | Observability is incomplete: lookup timing covers the service/miss path, cache counters remain local, gap logs occur on dashboard reads rather than mutations, and expiry warnings are read-driven. Audit failure logging exists. See [lookup log](../../apps/api/app/services/governance_registry.py#L422), [summary logs](../../apps/api/app/services/governance_registry.py#L378), and [cache counters](../../apps/api/app/services/governance_cache.py#L12). | AUD-023 |
| P2 | Named contract/integration tests largely call isolated services; cache tests never inject registry failure; Playwright filter/gap/drill-down tests can pass without performing their claimed action. Newer dashboard tests mostly assert shape/status, not governance read-after-write. See [fixtures](../../tests/contract/test_data_source_registry.py#L14), [cache cases](../../tests/integration/test_governance_cache.py#L21), [conditional E2E](../../tests/e2e/test_governance_dashboard.spec.ts#L10), and [new filter assertion](../../tests/integration/test_governance_dashboard_api.py#L86). | AUD-024 |
| P2 | AU privacy/classification and default-deny transfer obligations are not mapped to a governance-specific policy/control. The existing classifier covers other route families; non-AU country regimes are explicitly deferred, not missing active-country implementations. No actual transfer or legal approval is established by this audit. See [amendments](spec.md#L235), [classifier scope](../../apps/api/app/middleware/classifier_gateway.py#L36), and [bounded carve-out](../../.specify/memory/constitution.md#L245). | AUD-025 |
| P2 | Latency, availability, failover, and cache-outage outcomes remain UNVERIFIED. Synchronous Cosmos operations run inside async endpoints; dashboard gap calculation performs per-source queries. There is no inspected lookup p95 measurement or fault-run evidence. See [Cosmos client](../../apps/api/app/repositories/governance_repository.py#L252), [gap loop](../../apps/api/app/services/governance_registry.py#L363), and [cache tests](../../tests/integration/test_governance_cache.py#L21). | AUD-026 |
| P2 | T056/T057 are checked without a local rehearsal record, SME catalogue sign-off, readiness snapshot, timed workflow/usability study, or reconstructive audit replay. All six success outcomes stay UNVERIFIED. See [completion claims](tasks.md#L143) and [acceptance instructions](quickstart.md#L140). | AUD-027 |
| P2 | Associated checklist/plan PASS statements are authored claims. HYP-003 points to a missing, malformed hypothesis filename; portfolio structural rubric snapshots are not per-spec consultation or human validation evidence. See [hypothesis claim](spec.md#L224), [baseline methodology](../028-capstone-alignment/evidence/rubric-baseline.md#L3), and [decision record sign-off](../028-capstone-alignment/evidence/decision-record.md#L38). | AUD-028 |

## Scope, Inputs, and Limitations

The governing [Review Contract](../001-spec-implementation-audit/README.md#L14) requires source-level delivery proof,
individual task rows, explicit negative searches, and separation of execution from authorship. Only this report is written.
Other specifications' implementation-review reports were not used. Supporting files from other features were inspected only
where this specification references them or the current behavior routes through their implementation.

| Input | Review scope |
| --- | --- |
| [spec.md](spec.md#L1) | Entire file, seven clarification decisions, all requirements, user stories, edge cases, and feature-028 amendments. |
| [tasks.md](tasks.md#L1) | Entire file, every T001 through T057 checkbox, checkpoints, dependencies, and implementation strategy. |
| [plan.md](plan.md#L1) | Entire file, both constitutional gates, planned storage/performance, model/UI/test ownership. |
| [data-model.md](data-model.md#L1) | Entire file, all six entities, required fields, referential/temporal invariants, reconciliation table. |
| [research.md](research.md#L1) | All ten decisions, including rejection of in-memory-only storage and hardcoded agent validation. |
| [quickstart.md](quickstart.md#L1) | Prerequisites, setup, all eight test-first phases, eight rehearsals, and acceptance checks. |
| [OpenAPI](contracts/openapi-governance.yaml#L1) | All paths, request/response schemas, security, errors, header and query contracts. |
| [quality checklist](checklists/requirements.md#L1) | All 28 checked claims plus notes; assessed individually below. |
| [Constitution](../../.specify/memory/constitution.md#L1) | Current v1.2.0, principles, human authorization, AU sovereignty, bounded model-hosting exception, and amendment authority. |
| [actor catalogue](../../.github/agents/AGENTS.md#L11) | Development-time purpose and actual actor identifiers, not an inferred runtime-agent catalogue. |
| [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1) and [hypothesis contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L1) | Validation evidence and filename/status obligations referenced by amendments. |
| [feature-028 decision](../028-capstone-alignment/evidence/decision-record.md#L9), [baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L3), [postfeature](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) | Only claims relevant to this specification's appended scope, personas, and HYP-003. Documentation-only authoring does not prove runtime or approval. |
| [risk record](../../docs/risk-register/RISK-NEW-013.md#L1) | Claimed signal-envelope compatibility treatment referencing spec 005; no execution evidence attached. |
| [review instructions](../../.github/instructions/code-review.instructions.md#L1) and [detailed standards](../../.github/instructions/references/code-review-checklists.md#L1) | Security, controlling behavior, meaningful assertions, errors, concurrency, and evidence quality. Python fact-grounded-coding and Cosmos DB best-practices skills were consulted; no debugger, SDK, or cloud calls were made. |

Source was followed from [router registration](../../apps/api/app/api/router.py#L75) and
[application middleware](../../apps/api/app/main.py#L26) into both governance services, both repository backends,
validators, models, seed loader, API and polling ingestion, legacy and replacement UI, and the assertions cited below.
Positive source findings mean IMPLEMENTED only for their specified slice, never that tests ran successfully.

Negative searches covered tracked application code in `apps/api/app`, `apps/agents`, `apps/ingestion`, and
`apps/ingest-runner`; governance UI references throughout `apps/web/src`; tests under `tests`, `apps/api/tests`,
and `apps/web/tests`; the complete local specification folder; and relevant references in `docs`,
`specs/028-capstone-alignment`, `specs/shared`, and CI configuration. Searches included the lifecycle/authorization
helper names, repository imports, `/data-sources`, `handoff-lookup`, and the linked hypothesis ID/filename.
The only tracked HYP-003 file found belongs to spec 001 and is not evidence for this specification's hypothesis.
The retired RSS implementation was also checked: [its current source identity](../../apps/ingestion/pipelines/bom_rss.py#L40)
maps to `bom-warnings`; a different pipeline name is not grounds for claiming a missing catalogue source.

No product imports, tests, builds, browser executions, benchmarks, network-to-product calls, deployments, or cloud operations
were performed. Cosmos persistence, actual authentication at any external ingress, live tenant isolation, real notifications,
performance, disaster failover, SME sign-off, human approval, and readiness outcomes remain UNVERIFIED without checked-in proof.
Public FastAPI/Pydantic documentation was consulted only to confirm router-dependency and assignment-validation semantics;
it is not implementation evidence. No secrets or real user data are reproduced.

### Status Semantics

IMPLEMENTED = inspected source supports the scoped behavior/artifact; PARTIAL = specific obligations remain;
MISSING = required behavior/artifact absent after scoped search; CONFLICT = incompatible obligations or implementations;
UNVERIFIED = execution/outcome/approval not established; SUPERSEDED = explicit replacement/retirement evidence.
A test filename or mock is never promoted to delivery or execution proof.

### Supersession and Scope Decisions

| Decision | Status | Evidence and effect on this audit |
| --- | --- | --- |
| Operational consumption of thresholds in US3-AS3 | SUPERSEDED for this feature's execution obligation | [Clarification](spec.md#L90), [FR-009b](spec.md#L142), and [research](research.md#L77) explicitly defer agent runtime refactoring. Stored/queryable thresholds remain in scope; the absence of an agent consumer is not independently charged as missing delivery. |
| Original `/governance` landing presentation | SUPERSEDED as the entry point only | [Redirect](../../apps/web/src/app/governance/page.tsx#L29) and [replacement navigation test](../../tests/e2e/governance-dashboard.spec.ts#L11) establish replacement. They do not retire source CRUD, live compliance, filters, assignment, or gap visibility. AUD-019/AUD-020/AUD-022 assess the replacement against those retained obligations. |
| Non-AU country implementation | Explicitly deferred; not an absence finding | [SCP-009](spec.md#L230), [capstone requirements](spec.md#L235), and [D-009 reaffirmation](../028-capstone-alignment/evidence/decision-record.md#L13) retain AU-v1. No non-AU MoU, DPIA, sovereign-region authorization, or country promotion is inferred. |
| Constitution/reference-model evolution | CONFLICT, not an automatic waiver | [v1.0.1 assumption](spec.md#L176) versus [v1.2.0](../../.specify/memory/constitution.md#L315). FR-012a requires re-evaluation; the new Constitution does not authorize silent continued approval under an obsolete rubric. |
| Agent-side cache/fallback wording | CONFLICT requiring ownership clarification | [NFR-002/NFR-003](spec.md#L156) speak about agents, while FR-009b defers runtime refactoring. API-side T040/T041 remain concrete deliverables. AUD-018 requires an explicit compatibility/downstream contract, not unapproved agent-business-logic work. |

## Remediation Tasks

Every task below is future work and remains unchecked. Commands are instructions for later authorized execution only.

### Validation Prerequisites Used Below

- **V-PY:** repository-compatible Python 3.12+, API/domain dependencies and pytest extras already installed; run from the
  repository root. Use [test import setup](../../tests/conftest.py#L10). Clear production Cosmos/identity settings before
  application imports; use explicit injected fake repositories/containers and synthetic authenticated principals. Fixtures
  must not accidentally select live Cosmos via `COSMOS_ENDPOINT`. No real secrets in fixtures or reports.
- **V-WEB:** V-PY plus Node.js 22, pinned pnpm 10.6.3, installed web dependencies and Playwright Chromium. Use
  [Playwright configuration](../../apps/web/playwright.config.cts#L3); reserve 3000/8000 for an isolated test instance and do
  not reuse another operator's service. This config starts servers; its commands were not run here.
- **V-STORE:** explicitly configured isolated SDK-compatible test storage, separate from operational resources. Ordinary
  suites must exercise deterministic fakes without network; actual durability/ETag/transaction evidence requires a separately
  authorized emulator or test-environment run. Repository mock assertions alone do not close a durability claim.
- **V-MEASURE:** explicit approval for a dedicated AU test environment and fault/load exercise, recorded topology/versions,
  representative seeded data, identity policy, workload, time window, and retained raw measurements. No production fault injection.
- **V-DOC:** text/JSON/Markdown inspection only; validate IDs, evidence ownership, file existence, line anchors, and newline.
  Human review evidence must name reviewer role/date/scope/revision and must not be inferred from an author name.

### Safety and Integrity

- [ ] **AUD-001 (P0): Enforce authenticated governance access and actor attribution.**

  **Original obligations:** T017, T020, T021, T026, T031, T037, T038, T039, T049, T055; FR-005, FR-013, FR-015, FR-016.
  **Expected vs actual/impact:** only permitted authenticated roles may change governance; broader authorized readers may view it.
  [Unattached header helpers](../../apps/api/app/api/governance.py#L42) and [unprotected production prefixes](../../apps/api/app/middleware/rbac_check.py#L32)
  leave the ASGI governance paths unrestricted; body-supplied actor IDs undermine accountability.
  **Developer instructions:** attach real authenticated dependencies to every governance/source read and mutation, including
  replacement-dashboard and runtime lookup routes. Define the role-name mapping to existing auth claims; derive actor/assessor/
  assigner identity from the verified principal, not headers or editable form fields. Preserve deliberate broader read access.
  **Tester instructions:** extend [registry contract tests](../../tests/contract/test_data_source_registry.py#L14) and
  [dashboard API client fixture](../../tests/integration/test_governance_dashboard_api.py#L10). Positive: each allowed writer and
  permitted reader. Negative: missing/invalid bearer, unrelated role, forged `X-User-Role`, forged assessor/assigner. Edge:
  multi-role identities and denied requests must cause zero state/audit mutations except the appropriate denial event.
  **Ownership/dependencies:** Security Engineer and API owner; establish the principal contract before AUD-007/AUD-025.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_governance_assignment.py tests/integration/test_governance_dashboard_api.py -q`.
  Complete only when real-router assertions prove 401/403 versus allowed success and stored actor IDs equal verified subjects.

- [ ] **AUD-002 (P0): Enforce source eligibility at ingestion and existing-chain lookup.**

  **Original obligations:** T021, T027, T030, T034, T035, T040; FR-006, FR-012b; US1-AS3, US2-AS4.
  **Expected vs actual/impact:** rejected/deactivated/expired sources must not supply operational signals; valid lapsed sources
  may continue within grace. [API ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) and
  [poll processing](../../apps/api/app/services/ingestion/pipeline_base.py#L192) do not consult governance, and
  [lookup](../../apps/api/app/services/governance_registry.py#L422) checks only chain status.
  **Developer instructions:** introduce one authoritative eligibility decision reused before source polling/payload acceptance,
  signal persistence, and eligible-chain publication. Resolve envelope identities to registered sources; never trust a caller's
  kind/status as authorization. Define unknown/unassessed behavior explicitly, and preserve FR-012b's approved grace exception.
  This is ingestion policy enforcement, not deferred agent routing refactoring.
  **Tester instructions:** extend [blocking tests](../../tests/contract/test_constitutional_compliance.py#L107) and
  [MockPipeline](../../tests/integration/test_ingestion_pipeline.py#L6), injecting spies for storage/forwarding. Positive: approved
  source and eligible lapsed source before deadline. Negative: rejected, deactivated, unknown, and expired IDs across API and
  worker paths. Edge: already-cached chain, in-flight payload at revocation, and exact deadline. Assert no signal write/forward.
  **Ownership/dependencies:** API ingestion/Data Engineer; AUD-001, AUD-003, AUD-007, AUD-018.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_constitutional_compliance.py tests/integration/test_ingestion_pipeline.py tests/integration/test_governance_grace_period.py -q`.
  Completion requires enforcement-path assertions, not just rejection of a new assignment.

- [ ] **AUD-003 (P1): Connect and complete the failed-re-review grace lifecycle.**

  **Original obligations:** T027, T030, T031, T035, T054; FR-006, FR-012b, NFR-005; US2-AS4 and the sixth rehearsal.
  **Expected vs actual/impact:** previously approved and assigned sources failing re-review enter warned grace, default 72h,
  with authorized extension/revocation and automatic expiry. [Derivation](../../apps/api/app/services/governance_registry.py#L157)
  immediately rejects; [helpers](../../apps/api/app/services/governance_registry.py#L193) are not connected to assessment or a scheduler.
  **Developer instructions:** retain pre-review eligibility, make the failed-review transition explicit, configure grace duration,
  connect an idempotent expiry/reconciliation worker, and send durable governance-lead notifications. Persist rationale/actor for
  overrides, clear dates after compliant remediation, and recompute governance/cache eligibility atomically.
  **Tester instructions:** replace manual setup in [grace tests](../../tests/integration/test_governance_grace_period.py#L59)
  with actual review submissions and a fake clock/scheduler. Positive: initial 72h grace, extension, remediation. Negative:
  never-approved/unassigned failures do not acquire an undeserved grace allowance; unauthorized override fails. Edge: exactly
  at expiry, restart during grace, extension racing expiry, repeated worker execution, malformed legacy missing end date.
  **Ownership/dependencies:** Governance service owner/SRE; AUD-001, AUD-004, AUD-005, AUD-008, AUD-018.
  **Future validation/completion:** V-PY; `python -m pytest tests/integration/test_governance_grace_period.py tests/integration/test_governance_rereview.py -q`.
  Complete when review-triggered grace, visible notification, expiry without a dashboard visit, and ingestion decisions are asserted.

- [ ] **AUD-004 (P1): Require a complete applicable-principle profile before approval.**

  **Original obligations:** T025, T026, T027, T034, T048, T057; FR-004, FR-005, FR-006, FR-014, SC-002, SC-003.
  **Expected vs actual/impact:** all applicable principles need current, attributable assessments; incomplete work cannot become
  whole-source compliance. [Current derivation](../../apps/api/app/services/governance_registry.py#L157) approves any nonempty
  set without adverse values, and [the test](../../tests/contract/test_constitutional_compliance.py#L98) codifies two-principle approval.
  **Developer instructions:** derive status from the complete versioned principle set, applicability decisions, current assessments,
  and outstanding conditions. Keep missing principles visible and distinguish approval from incomplete assessment. Preserve
  superseded history; do not treat `not_applicable` as an unexplained shortcut around required review.
  **Tester instructions:** reuse [_register_source/_make_assessment](../../tests/contract/test_constitutional_compliance.py#L17).
  Positive: all applicable principles compliant; justified non-applicable principles; complete conditional profile. Negative:
  one/two/five of six, duplicate principle IDs, adverse privacy assessment, blank applicability rationale. Edge: final principle
  arrives after assignment, obsolete-version assessment, or supersession removes the only valid current record.
  **Ownership/dependencies:** Governance Lead and domain/API owner; resolve principle mapping with AUD-009; atomicity AUD-005.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_constitutional_compliance.py tests/contract/test_governance_dashboard.py -q`.
  Complete when no incomplete profile is approved or hidden from missing-assessment counts and all conditional decisions are retained.

- [ ] **AUD-005 (P1): Make governance transitions atomic and concurrency-safe.**

  **Original obligations:** T014, T016, T020, T026, T037, T038, T039; FR-005, FR-009, FR-010, FR-013, NFR-004, SC-006.
  **Expected vs actual/impact:** state, current-record uniqueness, derived state, and corresponding audit must agree even on failure.
  [Multi-write supersession](../../apps/api/app/services/governance_registry.py#L110) and
  [unconditional Cosmos upsert](../../apps/api/app/repositories/governance_repository.py#L270) have no transactional/ETag guards.
  **Developer instructions:** define aggregate boundaries and use supported conditional/transactional operations or a durable
  reconciliation/outbox protocol. Enforce one current source/principle assessment, one active primary, one active chain, and one
  hazard/jurisdiction rule under concurrent writers. Make retries idempotent; do not return success for an unaudited transition.
  **Tester instructions:** parameterize existing [supersession](../../tests/contract/test_constitutional_compliance.py#L71) and
  [assignment/chain tests](../../tests/contract/test_governance_assignment.py#L64) with an injected backend failure model.
  Positive: normal transition/retry. Negative: failure at each state/audit write. Edge: concurrent reviews, primary replacements,
  chain replacements, stale ETags, and replay after a worker restart. Assert exact active/current counts and recoverable audit parity.
  **Ownership/dependencies:** Data Engineer/Cosmos owner; coordinate AUD-006, AUD-007, AUD-016, AUD-017.
  **Future validation/completion:** V-PY then separately authorized V-STORE;
  `python -m pytest tests/contract/test_constitutional_compliance.py tests/contract/test_governance_assignment.py -q`.
  Deterministic tests must expose partial commits; durability closure additionally needs stored failure/concurrency run evidence.

- [ ] **AUD-006 (P1): Enforce immutable, attributable, reconstructive governance audit records.**

  **Original obligations:** T011, T016, T017, T020, T021, T026, T028, T029, T030, T031, T037, T038, T039, T049, T057;
  FR-013, FR-016, SC-006.
  **Expected vs actual/impact:** immutable events reconstruct every state transition. [Audit upsert](../../apps/api/app/repositories/governance_repository.py#L456)
  can overwrite a supplied existing event ID; [event model](../../packages/domain/src/domain/models/governance_audit.py#L36)
  and memory references are mutable. Registration stores a name/seed marker, assessment events omit rationale/conditions,
  and chain events store only a step count; implicit revocation and approval/rejection actions are omitted.
  **Developer instructions:** use create-only audit persistence and defensive immutable snapshots; bind actors/scopes to auth.
  Version event schemas and retain complete necessary before/after or reconstructive payloads, including supersession links,
  conditional approval, rejection, revocation, precedence, rationale, and grace lifecycle. Reconcile events with AUD-005's commit protocol.
  **Tester instructions:** extend [audit cases](../../tests/contract/test_governance_dashboard.py#L85) using existing registration,
  assessment, and assignment helpers. Positive: replay all action types to identical normalized registry state. Negative: duplicate
  audit ID, mutation of returned event/details, omitted event, forged actor. Edge: retry, equal timestamps, seed import, supersession,
  primary replacement, and redacted sensitive fields without losing reconstructability.
  **Ownership/dependencies:** Data Engineer, Governance Lead, Security Engineer; AUD-001, AUD-005, AUD-007, AUD-025.
  **Future validation/completion:** V-PY/V-STORE; `python -m pytest tests/contract/test_governance_dashboard.py tests/contract/test_governance_assignment.py -q`.
  Complete only with zero replay differences, duplicate-write rejection, and an explicit immutable-retention policy; no retrospective fabricated events.

- [ ] **AUD-007 (P1): Define and enforce governance tenant/agency scope.**

  **Original obligations:** T014, T016, T040, T041, T049, T055; FR-013, FR-015, FR-016, NFR-002.
  **Expected vs actual/impact:** sensitive governance decisions must follow organizational access policy, even if catalogue metadata
  is shared. [Source-only partitions](../../apps/api/app/repositories/governance_repository.py#L296),
  [cross-partition queries](../../apps/api/app/repositories/governance_repository.py#L281), and
  [source-only cache keys](../../apps/api/app/services/governance_cache.py#L20) ignore middleware scope.
  **Developer instructions:** document which catalogue records are global and which assessments/routing/audit records are tenant
  or agency owned. Enforce that decision with trusted request context, partition/query predicates, cache namespaces, and mutation
  checks. Migrate legacy `live` defaults deliberately; do not infer authority from a caller-supplied tenant header.
  **Tester instructions:** reuse [dashboard client fixture](../../tests/integration/test_governance_dashboard_api.py#L10) and
  [cache helper](../../tests/integration/test_governance_cache.py#L11). Positive: authorized same-scope access and intentionally shared
  public metadata. Negative: another agency/simulation reading or modifying sensitive decisions. Edge: identical source IDs in two
  tenants, cache hits after tenant switch, missing context, global-reference exceptions, and audit exports/queries under scoped access.
  **Ownership/dependencies:** Security/API/Data Engineer; policy decision depends on AUD-001; coordinate storage/cache migration.
  **Future validation/completion:** V-PY; `python -m pytest tests/integration/test_governance_dashboard_api.py tests/integration/test_governance_cache.py tests/contract/test_governance_dashboard.py -q`.
  Complete when scope policy is approved and assertions prove both permitted sharing and denied cross-scope operations, not just a tenant label.

### Governance Domain and Lifecycle

- [ ] **AUD-008 (P1): Persist and expose real source/Constitution re-review work.**

  **Original obligations:** T020, T028, T029, T035, T047; FR-012, FR-012a, FR-014; EC-02, ASM-010.
  **Expected vs actual/impact:** material changes start a new review cycle and constitutional amendments flag all affected existing
  assessments. [Triggers](../../apps/api/app/services/governance_registry.py#L172) only append audit events; pending remains zero.
  **Developer instructions:** persist source-version/Constitution-version and per-principle re-evaluation state, distinguish material
  changes from no-ops/cosmetic edits, and expose an authorized amendment trigger consumed by the actual amendment workflow.
  Cover format, availability, provider, and terms-of-use changes; preserve approval history while review is pending and invoke
  grace only on the qualifying failed review, not on every edit.
  **Tester instructions:** extend [re-review tests](../../tests/integration/test_governance_rereview.py#L29) and dashboard assertions.
  Positive: each material field and an amendment flags affected records and changes the pending count. Negative: no-op edit,
  duplicate amendment, unassessed source, unauthorized trigger. Edge: new/retired principle, overlapping source/Constitution change,
  and completing only part of the new cycle. Assert durable flags and their clearance, not merely event count.
  **Ownership/dependencies:** Governance Lead/API owner; AUD-004, AUD-005, AUD-009; downstream notifications AUD-003.
  **Future validation/completion:** V-PY; `python -m pytest tests/integration/test_governance_rereview.py tests/contract/test_governance_dashboard.py -q`.
  Complete when affected records and dashboard state track the active review version deterministically across restart and repeated triggers.

- [ ] **AUD-009 (P1): Provide versioned, principle-specific assessment criteria.**

  **Original obligations:** T007, T025, T026, T032, T033, T034; FR-004, FR-004a, FR-005, FR-012a; US2-AS1, US2-AS2, EC-03, EC-05.
  **Expected vs actual/impact:** assessors see the required safety, coordination, provenance/freshness, privacy/agreement/residency,
  multilingual, and platform questions. [The form](../../apps/web/src/components/governance/AssessmentForm.tsx#L5) supplies labels
  and generic free text, and its six historical principle names do not map explicitly to [current constitutional sections](../../.specify/memory/constitution.md#L70).
  **Developer instructions:** agree a versioned mapping with the constitutional owner; render the approved criteria beside each
  principle, record rubric version/applicability, and show missing principles without inventing assessments. Preserve old labels
  as historical evidence. Do not amend the Constitution or automate compliance judgments to resolve this conflict.
  **Tester instructions:** reuse [_make_assessment](../../tests/contract/test_constitutional_compliance.py#L30),
  [ComplianceCard](../../apps/web/src/components/governance/ComplianceCard.tsx#L35), and the governance E2E file.
  Positive: all six specified criterion groups with conditions/gaps and history. Negative: absent criteria, obsolete rubric accepted
  as current, privacy concern without mitigation. Edge: non-public multilingual applicability, private IoT without agreement,
  social value plus misinformation risk, and Constitution amendment preserving historical assessment labels.
  **Ownership/dependencies:** Governance/Safety Lead and UX/API owners; AUD-008, AUD-011; constitutional mapping approval is external.
  **Future validation/completion:** V-PY/V-WEB; `python -m pytest tests/contract/test_constitutional_compliance.py -q`;
  `corepack pnpm --filter @ama/web exec playwright test test_governance_dashboard.spec.ts --project=chromium`.
  Complete when criterion content, rubric version, missing-principle presentation, and human-only decisions are asserted.

- [ ] **AUD-010 (P1): Share one registry composition and make bootstrap failure recoverable.**

  **Original obligations:** T001, T002, T003, T005, T014, T017, T019, T022, T024; FR-001, FR-001a, NFR-004; US1-AS2.
  **Expected vs actual/impact:** register, list, retrieve, assess, and assign address the same source in every supported mode.
  [Separate module instances](../../apps/api/app/api/data_sources.py#L11) and [one-sided seed startup](../../apps/api/app/api/governance.py#L60)
  split local state; the `finally` marker prevents recovery after a failed seed attempt.
  **Developer instructions:** compose repository/service dependencies once per application and share them across routers and
  dashboard adapters. Make production backend selection explicit and fail visibly if durable storage is required but absent.
  Move controlled, idempotent seed initialization into a recoverable lifecycle; retain existing records, and report partial failures.
  Do not remove the existing [Cosmos container](../../infra/main.bicep#L701) or claim persistence is wholly missing.
  **Tester instructions:** extend [registry tests](../../tests/contract/test_data_source_registry.py#L31) using a real TestClient,
  plus `SEED_ROOT` and injected memory/Cosmos-compatible backends. Positive: register then GET/compliance/assignment through separate
  routers; repeated import creates no duplicates. Negative: failed seed read/write and missing production backend. Edge: partial
  import retry, process restart, existing user-edited seed record, and two app instances sharing authorized test storage.
  **Ownership/dependencies:** API composition/Data Engineer; AUD-005, AUD-007; test isolation AUD-024.
  **Future validation/completion:** V-PY/V-STORE; `python -m pytest tests/contract/test_data_source_registry.py tests/integration/test_governance_dashboard_api.py -q`.
  Complete when cross-router read-after-write and recovery work in supported modes, with no silent production dictionary fallback.

- [ ] **AUD-011 (P1): Validate governance metadata and updates at the trusted boundary.**

  **Original obligations:** T006, T007, T008, T017, T020, T026, T037; FR-002, FR-003, FR-005, FR-010.
  **Expected vs actual/impact:** required metadata/rationale is nonempty, kind/sub-category is valid, and invalid updates are rejected
  without persistence. [Registration defaults](../../apps/api/app/api/data_sources.py#L14) allow empty provider/classification/cadence;
  [PATCH](../../apps/api/app/services/governance_registry.py#L87) bypasses model validation and accepts arbitrary status strings.
  **Developer instructions:** validate a merged model before saving, explicitly distinguish required new-registration fields from
  migrated legacy data, constrain status and kind/sub-category pairs, and reject blank explanation/scope/actor/condition/gap values.
  Keep platform-derived compliance/governance fields protected. Do not blindly enable assignment validation on the self-mutating
  trust-rank after-validator; revalidate a coherent update instead.
  **Tester instructions:** extend [_make_source](../../tests/contract/test_data_source_registry.py#L18) and
  [_make_assessment](../../tests/contract/test_constitutional_compliance.py#L30). Positive: every valid kind and legitimate metadata
  update. Negative: missing/whitespace required fields, invalid status, incompatible sub-category, blank list members. Edge:
  Unicode provider names, null versus omitted PATCH values, invalid legacy documents, empty update, and failed validation leaving no mutation.
  **Ownership/dependencies:** Domain/API owner; AUD-005, AUD-012, AUD-013; compatibility policy requires Data Engineer review.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_constitutional_compliance.py tests/contract/test_governance_assignment.py -q`.
  Complete with consistent documented 4xx responses and zero invalid persisted/returned records.

- [ ] **AUD-012 (P1): Preserve trust-tier compatibility and define effective derived trust.**

  **Original obligations:** T006, T020, T024; FR-002a; data-model reconciliation and EC-06.
  **Expected vs actual/impact:** tier/rank stay consistent and legacy rank values remain meaningful; derived trust is bounded by
  input trust. [The after-validator](../../packages/domain/src/domain/models/data_source.py#L61) overwrites legacy rank from a
  default tier and does not run on the service's `setattr` update. The model has no input-bound effective-trust representation.
  **Developer instructions:** establish unambiguous legacy decoding and conflicting-input policy, derive the numeric rank from the
  selected canonical tier on all writes, and prevent PATCH response/storage disagreement. Specify nominal tier 7 versus effective
  input-bounded trust using existing provenance contracts; do not invent authoritative trust from a computed result.
  **Tester instructions:** extend [rank test](../../tests/contract/test_data_source_registry.py#L46). Positive: each of seven
  tier/rank mappings and a tier-changing PATCH. Negative: contradictory explicit tier/rank, invalid legacy rank, derived source
  claiming unsupported authoritative trust. Edge: rank-only legacy records, missing input provenance, mixed tier-1/tier-6 inputs,
  nested derived inputs, and memory/Cosmos round trips. Record unspecified effective-trust semantics as a decision before coding them.
  **Ownership/dependencies:** Domain/Data Engineer and Governance Lead; AUD-011, AUD-005; preserve existing consumers.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_data_source_registry.py -q`.
  Complete when old ranks survive decoding, all response/stored/readback ranks agree, and effective trust cannot exceed its documented input bound.

- [ ] **AUD-013 (P1): Enforce guarded, terminal source deactivation.**

  **Original obligations:** T020, T021, T024; FR-001, FR-006, FR-013; US1-AS3; DataSource status transitions.
  **Expected vs actual/impact:** retain history, reject deactivation when an active incident is using its active chain, and prevent
  resurrection through generic PATCH. [Current deactivation](../../apps/api/app/services/governance_registry.py#L98) checks only
  whether it is already deactivated; [update](../../apps/api/app/services/governance_registry.py#L87) can restore `available` directly.
  **Developer instructions:** resolve incident/chain usage from authoritative state in the authorized scope; implement the 409
  guard and terminal transition in one mutation path. Ensure PATCH cannot bypass timestamps/audit or the guard. Retain assessments,
  assignments, chain versions, and audit history, while revoking active eligibility/cache publication.
  **Tester instructions:** extend [deactivation cases](../../tests/contract/test_data_source_registry.py#L83) with chain/incident
  fixtures. Positive: unused or non-active-incident source deactivates and history remains readable. Negative: active chain in an
  active incident and PATCH resurrection. Edge: concurrent activation, repeated deactivation (documented 409), initially offline
  source, and cached chain. Assert no partial mutation on conflict and blocked ingestion afterward.
  **Ownership/dependencies:** Registry/incident service owners; AUD-001, AUD-002, AUD-005, AUD-018.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_governance_assignment.py -q`.
  Complete when both deactivation entry paths enforce identical guards and terminal state, with complete retained history.

- [ ] **AUD-014 (P1): Resolve the actor/runtime catalogue contract and detect stale references.**

  **Original obligations:** T008, T009, T015, T037, T038, T045; FR-007, FR-009, FR-009c, ASM-008.
  **Expected vs actual/impact:** current recognized targets must be catalogue-backed and stale assignments flagged.
  [Static validation](../../apps/api/app/validators/governance_validators.py#L5) neither loads nor versions a catalogue;
  [spec-004 actors](../../.github/agents/AGENTS.md#L11) are development-time roles, not the five runtime targets.
  **Developer instructions:** obtain an architecture/product decision defining a versioned mapping or separate authoritative runtime
  view tied to spec 004. Validate new writes against it and reconcile persisted assignments/chains on removal/rename. Preserve
  historical identities for audit; do not silently admit every Copilot actor as a runtime target or crash reading retired names.
  **Tester instructions:** extend [agent validation tests](../../tests/contract/test_governance_assignment.py#L88) and chain cases.
  Positive: all authorized mapped runtime agents. Negative: typo, unmapped actor, removed target, forged catalogue version. Edge:
  rename with existing records, addition without code edits, catalogue temporarily unavailable, and historical retired references.
  Assert dashboard flags and rejected new assignments, not just Pydantic's literal rejection.
  **Ownership/dependencies:** Solution Architect/Product Owner, catalogue and runtime-agent owners; AUD-008, AUD-016, AUD-022.
  **Future validation/completion:** V-PY/V-DOC; `python -m pytest tests/contract/test_governance_assignment.py -q`.
  Complete when the approved catalogue relationship is explicit and mutation/reconciliation tests demonstrate FR-009c.

- [ ] **AUD-015 (P1): Validate the full handoff contract, not only continuity.**

  **Original obligations:** T009, T015, T038, T043, T045; FR-008, FR-009, FR-009a; US3-AS2.
  **Expected vs actual/impact:** ordered steps, recognized agents, valid categories/thresholds, a primary-aligned first sender,
  and compatible payload contracts. [Current validator](../../apps/api/app/validators/governance_validators.py#L40) ignores
  numbering and payload references, while [service](../../apps/api/app/services/governance_registry.py#L288) accepts no-primary chains.
  **Developer instructions:** validate positive contiguous sequence numbers, primary existence/alignment, applicable category enums,
  finite inclusive confidence thresholds, and payload compatibility using the actual runtime contract definitions. Define how
  omitted optional payload references select defaults. Record chain versions/timestamps and reject incompatible changes before deprecation.
  **Tester instructions:** extend [_assign_primary and chain tests](../../tests/contract/test_governance_assignment.py#L47).
  Positive: multi-step compatible chain and thresholds 0/1. Negative: empty chain, zero/negative/duplicate/out-of-order numbering,
  unknown agent/category, incompatible or unknown payload reference, missing primary, wrong first sender, nonfinite/out-of-range threshold.
  Edge: allowed new signal categories, optional default schema, replacement failure retaining the old chain, and history timestamps.
  **Ownership/dependencies:** API Architect/domain owner; AUD-005, AUD-014, AUD-016; agent consumption remains downstream.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_governance_assignment.py -q`.
  Complete when each invalid case is rejected atomically and every returned active chain has proven schema/primary compatibility.

- [ ] **AUD-016 (P1): Recompute assignment, chain, and governance status consistently.**

  **Original obligations:** T008, T026, T030, T037, T038, T042, T045, T048; FR-007, FR-009, FR-010, FR-014, SC-003.
  **Expected vs actual/impact:** `fully_governed` always means a valid primary, compatible active chain, and approved complete profile.
  [Derivation](../../apps/api/app/services/governance_registry.py#L326) is invoked only by assignment/chain writes;
  [primary replacement](../../apps/api/app/services/governance_registry.py#L263) does not revalidate the retained chain.
  **Developer instructions:** maintain the invariant on every assessment, assignment, chain, grace, and source lifecycle transition.
  Define primary/secondary replacement and coordination semantics; revoke or flag an incompatible old chain and invalidate cached
  eligibility. Record implicit revocations and preserve prior records. Do not merely patch the displayed status string.
  **Tester instructions:** extend [assignment cases](../../tests/contract/test_governance_assignment.py#L64), using complete-profile
  fixtures from AUD-004. Positive: primary plus secondary with explicit scopes and valid chain. Negative: revoked/absent primary,
  rejected profile labelled fully governed, mismatched replacement primary. Edge: assess-before-assign versus assign-before-assess,
  grace/remediation, deactivation, secondary-only source, and repeated replacement. Assert invariant and historical audit after each mutation.
  **Ownership/dependencies:** Registry/domain owner; AUD-004, AUD-005, AUD-006, AUD-014, AUD-015, AUD-018.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_governance_assignment.py tests/contract/test_constitutional_compliance.py tests/contract/test_governance_dashboard.py -q`.
  Complete when operation order cannot produce contradictory governance status or an incompatible advertised chain.

- [ ] **AUD-017 (P1): Make precedence authoritative, unique, and queryable as a decision.**

  **Original obligations:** T010, T039, T045; FR-010, FR-010a; EC-04, EC-06; rehearsal 8.
  **Expected vs actual/impact:** jurisdiction override precedes national default, valid approved sources are referenced, and unresolved
  equal-tier conflicts request human resolution. [Set](../../apps/api/app/services/governance_registry.py#L344) performs no eligibility
  validation; [Cosmos storage](../../apps/api/app/repositories/governance_repository.py#L393) uses random IDs, permitting duplicate keys.
  **Developer instructions:** enforce a unique hazard/jurisdiction business key and valid jurisdiction/eligible source reference.
  Expose effective precedence through the service/query contract, with explicit trust fallback and unresolved-tie outcome. Reconcile
  rules when a referenced source is revoked. Track downstream agent integration separately if it requires FR-009b-excluded refactoring.
  **Tester instructions:** extend [precedence tests](../../tests/contract/test_governance_assignment.py#L163) through service/HTTP,
  not just `service._repo`. Positive: override wins, national fallback, no override for another state. Negative: unknown/deactivated/
  rejected source, invalid jurisdiction, competing duplicate rules. Edge: null versus absent national jurisdiction, equal tiers with
  no rule, source revoked after rule creation, and concurrent replacement. Assert explicit human-resolution results, not arbitrary first row.
  **Ownership/dependencies:** Governance/API Architect and domain authority owner; AUD-002, AUD-005, AUD-007, AUD-012.
  **Future validation/completion:** V-PY/V-STORE; `python -m pytest tests/contract/test_governance_assignment.py -q`.
  Complete when the public query contract proves deterministic inheritance/uniqueness and explicit unresolved conflict handling.

### Serving and Operator Workflows

- [ ] **AUD-018 (P1): Deliver cache resilience and mutation-wide invalidation within the agreed scope.**

  **Original obligations:** T040, T041, T046; FR-009a, FR-009b, NFR-001, NFR-002, NFR-003, NFR-004.
  **Expected vs actual/impact:** configured TTL, shared Redis-backed lookups, useful last-known-good data on registry outage, and
  safe fallback without halting processing. [Cache expiry deletes data](../../apps/api/app/services/governance_cache.py#L20);
  [lookup](../../apps/api/app/api/governance.py#L252) has no outage branch and only chain-PUT invalidates locally.
  **Developer instructions:** resolve API/client responsibility with the FR-009b owner, implement the promised server/cache contract,
  configure TTL default 300s, separate refresh expiry from outage retention, and define safe-default/degraded responses. Invalidate
  eligibility/chain data across replicas on relevant mutations, with tenant-safe keys and a documented bound preventing revoked data
  from remaining usable indefinitely. Do not treat Redis dedup support in the ingestion worker as governance-cache delivery.
  **Tester instructions:** extend [_make_chain/cache cases](../../tests/integration/test_governance_cache.py#L11), injecting fake
  clock, failing registry, and Redis-compatible storage. Positive: miss/hit, refresh, supported stale fallback. Negative: no cache
  plus outage, invalidated rejected source, cross-tenant key. Edge: exact TTL, Redis-only failure, registry-only failure, multiple replicas,
  concurrent invalidation, and recovery. Assert warnings/fallback contract and continued safe processing; no sleeps for clock control.
  **Ownership/dependencies:** Registry/SRE and downstream agent owners; AUD-002, AUD-007, AUD-015, AUD-016, AUD-023.
  **Future validation/completion:** V-PY then V-MEASURE; `python -m pytest tests/integration/test_governance_cache.py -q`.
  Complete when outage/retention/invalidation behavior is tested and ownership is resolved without falsely claiming deferred agent integration.

- [ ] **AUD-019 (P1): Connect the replacement dashboard to current governance truth.**

  **Original obligations:** T025, T036, T047, T049, T051, T052, T053; FR-011, FR-013, FR-014, SC-005, SC-006.
  **Expected vs actual/impact:** registration/assessment/assignment changes appear in the actual landing dashboard.
  [Construction omits the repository](../../apps/api/app/api/routes/governance_dashboard.py#L71);
  [fallback statistics](../../apps/api/app/services/governance_data_service.py#L230) equate availability with compliance,
  and [detail](../../apps/api/app/services/dashboard_aggregation_service.py#L185) fabricates pending records/empty histories.
  **Developer instructions:** wire a scoped registry adapter into the active aggregation path; read actual assessments, assignments,
  chains, deadlines, and audit. Never turn seed availability into an approval or rendering time into an assessment date. Label
  fallback/degraded provenance explicitly, return 404 for unknown source detail, and refresh/invalidate after mutations.
  **Tester instructions:** extend [real-client dashboard tests](../../tests/integration/test_governance_dashboard_api.py#L68).
  Positive: create, assess, assign, define chain, and reread through the redirected UI/API. Negative: seeded unassessed source must
  not be compliant; unknown ID must not yield invented detail. Edge: outage after a real snapshot, deactivation, conditional approval,
  grace countdown, and historical supersession. Assert actual values/history rather than key presence or HTTP 200 alone.
  **Ownership/dependencies:** Dashboard and Registry owners; AUD-004, AUD-007, AUD-008, AUD-010, AUD-016, AUD-022.
  **Future validation/completion:** V-PY/V-WEB; `python -m pytest tests/integration/test_governance_dashboard_api.py -q`;
  `corepack pnpm --filter @ama/web exec playwright test test_governance_dashboard.spec.ts --project=chromium`.
  Complete when the active UI agrees with authoritative source state and transparently distinguishes unavailable data from compliance.

- [ ] **AUD-020 (P1): Complete the source and assignment UI workflow on the canonical API.**

  **Original obligations:** T023, T032, T033, T043, T044, T051, T053; FR-001, FR-002, FR-003, FR-007, FR-008, FR-011, SC-004.
  **Expected vs actual/impact:** planner can register/update/deactivate and architect can assign/edit all chain settings.
  [Administration is placeholder-only](../../apps/web/src/app/governance/data-sources/page.tsx#L22);
  [assignment view](../../apps/web/src/app/governance/%5BdataSourceId%5D/assignments/page.tsx#L28) and
  [editor](../../apps/web/src/components/governance/HandoffChainEditor.tsx#L26) call `/api/v1`, while
  [configured API prefix](../../apps/api/app/core/settings.py#L10) and [proxy](../../apps/web/next.config.ts#L28) use `/api`.
  **Developer instructions:** reuse existing governance components and the working assessment-form pattern; connect a real source
  table/form, assignment creation/replacement, and editor load/save to the canonical client. Display provider, data type, cadence,
  coverage, trust, category/sub-category, status, assignments and chains. Add sub-category/trust/governance filters and editable
  category/payload settings. Preserve existing chain values; handle 4xx/5xx/network errors without success callbacks or stuck saving state.
  **Tester instructions:** strengthen [governance E2E](../../tests/e2e/test_governance_dashboard.spec.ts#L4). Positive: full workflow
  survives reload, secondary responsibility and threshold/category round-trip. Negative: forbidden role, invalid input, failed PUT,
  unavailable API. Edge: source IDs requiring URL encoding, existing chain editing, zero threshold, no matching sources, mobile/keyboard
  access, and failed fetch retaining a clearly stale prior view. Assert rows and persistence, not placeholders or conditional clicks.
  **Ownership/dependencies:** Web/UX owner; AUD-001, AUD-009, AUD-010, AUD-011, AUD-013, AUD-015, AUD-019, AUD-021.
  **Future validation/completion:** V-WEB;
  `corepack pnpm --filter @ama/web exec playwright test test_governance_dashboard.spec.ts --project=chromium` and the same command with `--project=mobile`.
  Complete when every named workflow/control is usable and persisted, and no incorrect `/api/v1/data-sources` request remains.

- [ ] **AUD-021 (P2): Reconcile the public governance API contract and error behavior.**

  **Original obligations:** T018, T019, T031, T039, T040, T047, T049, T052; FR-003, FR-009a, FR-011, FR-013, NFR-001.
  **Expected vs actual/impact:** declared filters, errors and cache headers work consistently. [Listing](../../apps/api/app/api/data_sources.py#L49)
  omits `agent_name`, [dashboard](../../apps/api/app/api/governance.py#L268) ignores it, and
  [audit](../../apps/api/app/api/governance.py#L298) uses different date parameter names and unguarded parsing.
  **Developer instructions:** implement agent filtering through active assignments; expose `X-Cache-Status` as a header; validate
  typed date ranges/timezones and alias `from`/`to`; return the specified missing-source result. Agree and synchronize request/response/
  error schemas with the [local OpenAPI](contracts/openapi-governance.yaml#L15), including optional/null fields and category evolution.
  **Tester instructions:** add real-route tests to [registry](../../tests/contract/test_data_source_registry.py#L52),
  [assignment](../../tests/contract/test_governance_assignment.py#L102), and [audit tests](../../tests/contract/test_governance_dashboard.py#L85).
  Positive: each filter alone and combined, cache HIT/MISS header, bounded audit range. Negative: unknown enum, invalid ISO date,
  reversed dates, nonexistent source. Edge: timezone offsets, equal boundary timestamps, revoked assignment, null national scope,
  and legacy clients. Assert body schema/status/header and selected records, not only a success code.
  **Ownership/dependencies:** API Architect; AUD-001, AUD-007, AUD-011, AUD-018; contract changes require explicit compatibility review.
  **Future validation/completion:** V-PY; `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_governance_assignment.py tests/contract/test_governance_dashboard.py -q`.
  Complete when actual HTTP behavior matches an approved contract and malformed requests produce controlled 4xx outcomes without mutation.

- [ ] **AUD-022 (P2): Make governance gaps and summary/filter counts complete and consistent.**

  **Original obligations:** T042, T047, T048, T050, T051, T052; FR-011, FR-012a, FR-014, SC-002, SC-003, SC-005; US4-AS1, US4-AS3.
  **Expected vs actual/impact:** operators see incomplete assessments, absent primaries/chains, lapsed review and invalid references.
  [Detection](../../apps/api/app/services/governance_registry.py#L363) only tests nonempty collections; derived gap fields stay at zero;
  [cards](../../apps/web/src/components/governance/GovernanceSummary.tsx#L20) omit required counts.
  **Developer instructions:** define one gap projection shared by API, mutation telemetry and both UI paths. Include missing required
  principles, primary assignment, valid chain, re-review, and stale catalogue references; preserve distinct no-assessment/no-assignment
  reasons. Define active versus historical denominators and filtered versus global totals, and render agent/geographic/governance filters.
  **Tester instructions:** reuse [_register/_assess](../../tests/contract/test_governance_dashboard.py#L17) and assignment fixtures.
  Positive: mixed complete/incomplete sources produce exact independent counts. Negative: one assessment or one secondary cannot
  erase outstanding gaps. Edge: deactivated history, multiple gaps on one source, no matching filters, lapsed/expired sources,
  conditionally approved sources, and mutation order. Assert both gap-record count and unique affected-source count where displayed.
  **Ownership/dependencies:** Registry/Dashboard owner; AUD-004, AUD-008, AUD-014, AUD-016, AUD-019, AUD-021.
  **Future validation/completion:** V-PY/V-WEB; `python -m pytest tests/contract/test_governance_dashboard.py tests/integration/test_governance_dashboard_api.py -q`.
  Complete when every displayed count/filter has a documented denominator and matches the authoritative projection after each mutation.

### Assurance, Privacy, and Readiness

- [ ] **AUD-023 (P2): Emit all required governance observability signals on the real paths.**

  **Original obligations:** T040, T041, T047, T054; FR-013, NFR-005.
  **Expected vs actual/impact:** per-lookup latency, hit/miss metrics, mutation-updated gaps, approaching-expiry warnings, and audit
  failures integrate with hub monitoring. [Logs](../../apps/api/app/services/governance_registry.py#L378) are dashboard-read-driven;
  [lookup timing](../../apps/api/app/services/governance_registry.py#L422) misses cache hits; cache counters have no metric export.
  **Developer instructions:** instrument the public lookup and cache, publish the common gap projection after committed mutations,
  issue idempotent approaching-expiry signals from the lifecycle worker, and preserve audit-failure events with correlation/context.
  Reuse the [hub telemetry integration](../../apps/api/app/main.py#L12), avoid sensitive content and unbounded metric-label cardinality,
  and ensure telemetry failure cannot falsely commit an unaudited governance change.
  **Tester instructions:** add `caplog` and injected metric/notifier assertions to [cache tests](../../tests/integration/test_governance_cache.py#L21)
  and [dashboard/audit tests](../../tests/contract/test_governance_dashboard.py#L85). Positive: each of five signal classes emitted at
  the intended trigger. Negative: audit persistence failure is observable; read-only dashboard calls do not substitute for mutation
  events. Edge: cache HIT, no dashboard visitors, warning-window boundary, repeated scheduler ticks, and telemetry exporter outage.
  **Ownership/dependencies:** SRE/observability owner; AUD-003, AUD-005, AUD-018, AUD-022.
  **Future validation/completion:** V-PY then V-MEASURE for exported evidence;
  `python -m pytest tests/integration/test_governance_cache.py tests/integration/test_governance_grace_period.py tests/contract/test_governance_dashboard.py -q`.
  Complete when exact trigger/field assertions pass and an authorized monitoring sample demonstrates integration without PII leakage.

- [ ] **AUD-024 (P2): Replace vacuous/service-only acceptance evidence with connected tests.**

  **Original obligations:** T024, T034, T035, T045, T046, T052, T053; FR-001, FR-004, FR-006, FR-009, FR-011,
  FR-012b, FR-013, FR-015, NFR-002, NFR-003; all four user stories and their acceptance scenarios.
  **Expected vs actual/impact:** named tests must falsify the required behavior through its real boundary.
  [Original service fixture](../../tests/contract/test_data_source_registry.py#L14),
  [manual grace expiry](../../tests/integration/test_governance_grace_period.py#L80), and
  [conditional E2E checks](../../tests/e2e/test_governance_dashboard.spec.ts#L10) miss the connected failures above.
  **Developer instructions:** retain useful unit tests, add real-router fixtures with shared injected storage and realistic principal
  dependencies, and give E2E deterministic seeded states. Replace `pytest.raises(Exception)` with exact error/status assertions;
  remove conditional skipping of required controls. Add Cosmos-backend parity/failure tests instead of mocking the service under test.
  **Tester instructions:** reuse all seven original Python files, [MockPipeline](../../tests/integration/test_ingestion_pipeline.py#L6),
  [new dashboard client](../../tests/integration/test_governance_dashboard_api.py#L10), and the existing Playwright config.
  Positive: complete register/review/assign/chain/dashboard flow. Negative: remove a required control or authorization/ingestion guard
  and verify the matching test fails. Edge: backend exception, empty filtered result, expired cache, supersession, and mobile navigation.
  **Ownership/dependencies:** QA/API/Web owners; incorporate AUD-001 through AUD-023 cases without treating their mocks as execution proof.
  **Future validation/completion:** V-PY/V-WEB;
  `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_constitutional_compliance.py tests/contract/test_governance_assignment.py tests/contract/test_governance_dashboard.py tests/integration/test_governance_rereview.py tests/integration/test_governance_grace_period.py tests/integration/test_governance_cache.py -q`;
  `corepack pnpm --filter @ama/web exec playwright test test_governance_dashboard.spec.ts --project=chromium`.
  Complete only when each acceptance condition has non-vacuous assertions and retained revision-bound results; source authorship alone is insufficient.

- [ ] **AUD-025 (P2): Map AU governance privacy controls and retain explicit country gates.**

  **Original obligations:** T007, T011, T026, T055, T057; FR-004a, FR-015, FR-016, FR-CAP-005-001, FR-CAP-005-002; ASM-007, ASM-010, SCP-009, SCP-010.
  **Expected vs actual/impact:** AU-v1 governance data has an approved privacy/classification/access/retention policy; non-AU promotion
  remains gated. [Generic classifier](../../apps/api/app/middleware/classifier_gateway.py#L36) is not connected to governance and
  [assessment metadata](../../packages/domain/src/domain/models/constitutional_assessment.py#L20) has no regime/version classification.
  **Developer instructions:** map the current AU APP obligations and sensitive governance fields to reviewed controls, including
  minimal actor identifiers, PII handling, retention, classification, and lawful access. Preserve audit reconstructability without
  publishing unnecessary personal details. Document an enforceable default-deny country/transfer policy where this registry influences
  egress; do not implement deferred PH/JP/BD regimes or reinterpret the [bounded model-hosting carve-out](../../.specify/memory/constitution.md#L245).
  **Tester instructions:** reuse [classifier test pattern](../../apps/api/tests/contract/spec_035/test_classifier_branches.py#L46)
  with actual governance routes, not only `/outcomes`. Positive: approved AU handling and authorized review. Negative: sensitive
  fields exposed to unauthorized roles, unsupported country activation, unjustified transfer request. Edge: mixed-scope data,
  unavailable classifier/policy, historical records, and the explicitly approved bounded model-hosting exception.
  **Ownership/dependencies:** Compliance Auditor/Security Engineer and legal/data owner; AUD-001, AUD-006, AUD-007, AUD-009.
  **Future validation/completion:** V-PY/V-DOC;
  `python -m pytest tests/contract/test_constitutional_compliance.py apps/api/tests/contract/spec_035/test_classifier_branches.py -q`.
  Complete only with approved AU control mapping and governance-path assertions; country activation and legal approval remain external gates.

- [ ] **AUD-026 (P2): Establish lookup performance and outage evidence.**

  **Original obligations:** T040, T041, T046, T054, T056, T057; NFR-001, NFR-002, NFR-003, NFR-004; plan dashboard-load target.
  **Expected vs actual/impact:** lookup p95 <=50ms and hub-equivalent resilience are measured under a declared representative workload.
  [Synchronous SDK path](../../apps/api/app/repositories/governance_repository.py#L252),
  [per-source queries](../../apps/api/app/services/governance_registry.py#L363), and
  [in-memory cache tests](../../tests/integration/test_governance_cache.py#L21) establish neither outcome.
  **Developer instructions:** remove blocking I/O from async request execution where measurements demand it, share/close clients,
  bound lookup/query work and retries, and document availability/failover behavior. Extend the existing cache test file with a
  clearly separated measurement harness; proposed test names `lookup_latency` and `registry_outage` are not existing tests.
  **Tester instructions:** V-MEASURE; at least 1,000 representative lookups, declared concurrency and warm/cold mix, API-boundary timing,
  raw samples and p95 calculation. Positive: healthy deployment meets <=50ms. Negative: injected Cosmos/Redis failure exercises
  documented fallback. Edge: replica restart, expired/empty cache, concurrent governance mutation, regional/service recovery,
  and dashboard load below the plan's 2s target. Never substitute dictionary-only timings for service latency.
  **Ownership/dependencies:** SRE/performance owner; AUD-005, AUD-010, AUD-018, AUD-019, AUD-023, AUD-024.
  **Future validation/completion:** after the proposed cases exist, V-MEASURE;
  `python -m pytest tests/integration/test_governance_cache.py -k "lookup_latency or registry_outage" -q`.
  Complete with retained environment/revision-bound load/fault reports, measured targets, and explicit remaining availability limitations.

- [ ] **AUD-027 (P2): Obtain real rehearsal, readiness, and success-criterion evidence.**

  **Original obligations:** T012, T013, T022, T056, T057; SC-001, SC-002, SC-003, SC-004, SC-005, SC-006.
  **Expected vs actual/impact:** the eight [rehearsals](quickstart.md#L129) and six success outcomes have attributable results.
  [Checked tasks](tasks.md#L143) and [seed test >=40](../../tests/contract/test_data_source_registry.py#L116) do not establish them.
  **Developer instructions:** prepare a deterministic readiness export and reproducible rehearsal path after functional fixes.
  Measure seed-ID intersection, not a hardcoded count; retain source/assessment/assignment/chain and audit snapshots. Provide a
  human workflow and usability protocol with role, start/end events, participant denominator, and recorded approval decisions.
  **Tester instructions:** Positive: all eight rehearsals with registered sources and actual guards. Negative: omitted seed source,
  unreviewed principle, missing chain, unresolved gap, or audit event must fail its criterion. Edge: exactly 90% catalogue coverage,
  30-minute workflow boundary, 90% user denominator and two-minute gap-identification boundary, conditional approval and deactivated
  history. SC-001 needs the SME panel; SC-002/SC-003 need an operational readiness snapshot; SC-006 needs reconstructive replay.
  **Ownership/dependencies:** QA/Governance Lead/SME panel and UX research; AUD-002 through AUD-024 as applicable, AUD-026 for NFR evidence.
  **Future validation/completion:** V-PY/V-WEB plus scheduled authorized human rehearsal;
  `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_constitutional_compliance.py tests/contract/test_governance_assignment.py tests/contract/test_governance_dashboard.py -q`;
  `corepack pnpm --filter @ama/web exec playwright test test_governance_dashboard.spec.ts --project=chromium`.
  Complete only with >=90% named-source coverage and panel validation, zero readiness assessment/assignment/chain gaps, workflow <30min,
  >=90% tested users finding gaps within 2min, and zero audit replay differences. Automated success cannot replace human measurements.

- [ ] **AUD-028 (P2): Repair this specification's evidence linkage and qualify review claims.**

  **Original obligations:** T056, T057; ASM-008, ASM-009, PER-007, PER-008, PER-009, HYP-003, SCP-009; associated review/checklist claims.
  **Expected vs actual/impact:** a claimed consultation, persona validation, rubric improvement, or completed rehearsal has a scoped
  record. [HYP-003](spec.md#L224) cites absent `specs/028-capstone-alignment/evidence/HYP-HYP-003.md`; the
  [stub contract](../028-capstone-alignment/contracts/evidence-stub.contract.md#L7) requires a correctly named co-located record.
  **Developer instructions:** resolve the hypothesis's owner/ID without borrowing spec 001's unrelated HYP-003. A possible new
  location is `specs/005-data-source-governance/evidence/HYP-003.md` (proposed, not existing evidence), subject to the register's
  change-control rules. Record per-spec baseline/comparator and named consultation scope; qualify unsupported historical PASS/
  validated labels rather than manufacturing retrospective evidence. Preserve the original reviewed artifacts in this audit.
  **Tester instructions:** V-DOC; check six required stub headings, >=2 preconditions, quantified falsification, owning-spec linkage,
  creation status `Not tested`, and legitimate later status transitions. Positive: revision-bound actual consultation/SME record.
  Negative: author name, proxy-only validation, portfolio aggregate, wrong hypothesis owner, or broken link used as approval.
  Edge: same numeric HYP ID in another feature, renamed comparator file, deferred non-AU personas, and no historical evidence recoverable.
  **Ownership/dependencies:** Product Owner/Governance Lead and specification evidence owner; AUD-009, AUD-014, AUD-027.
  **Future validation/completion:** V-DOC; `git diff --check -- specs/005-data-source-governance` plus the ID/link checks described below
  and manual evidence-authority review. Complete when links resolve to correctly owned evidence and every retained execution/approval
  claim is supported or explicitly UNVERIFIED; no fabricated sign-off or automatic hypothesis validation.

## Requirement Coverage

The denominator is **27 FR identifiers** (25 original plus two capstone amendments), **five NFRs**, and **six SCs**.
Every ID appears separately. Status applies to the full stated obligation; related tasks provide the developer/tester work.

| Requirement | Status | Expected versus inspected implementation/test evidence | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | Catalogue/CRUD exist, but instances split, arbitrary input IDs can enter ingestion, and operator administration is incomplete: [instances](../../apps/api/app/api/data_sources.py#L11), [worker](../../apps/api/app/services/ingestion/pipeline_base.py#L192), [registry tests](../../tests/contract/test_data_source_registry.py#L31). | AUD-002, AUD-010, AUD-020, AUD-027 |
| FR-001a | IMPLEMENTED | Machine-loadable 46-entry catalogue covers the enumerated named families; [JSON](../../packages/domain/src/domain/seed/data_sources_australia.json#L1), [loader](../../packages/domain/src/domain/seed/bootstrap.py#L43), [import assertions](../../tests/contract/test_data_source_registry.py#L115). This credits authored/importable catalogue content, not full national completeness or SME approval. | AUD-010, AUD-027 |
| FR-002 | PARTIAL | Fields exist, but required metadata can be empty and UI omits data type/cadence: [model](../../packages/domain/src/domain/models/data_source.py#L35), [request defaults](../../apps/api/app/api/data_sources.py#L14), [limited field assertions](../../tests/contract/test_data_source_registry.py#L121). | AUD-011, AUD-012, AUD-020 |
| FR-002a | PARTIAL | Seven tiers map on construction, but legacy rank-only records and PATCH diverge; effective derived trust is not established: [validator](../../packages/domain/src/domain/models/data_source.py#L61), [test](../../tests/contract/test_data_source_registry.py#L46). | AUD-012 |
| FR-003 | PARTIAL | Backend kind/sub-category filters exist; valid pair validation and UI sub-category filtering do not: [list](../../apps/api/app/api/data_sources.py#L49), [table](../../apps/web/src/components/governance/DataSourceTable.tsx#L36), [kind test](../../tests/contract/test_data_source_registry.py#L58). | AUD-011, AUD-020, AUD-021 |
| FR-004 | CONFLICT | Six historical principles are stored/displayed, but applicable-principle completeness and current-Constitution mapping are absent: [enum](../../packages/domain/src/domain/models/constitutional_assessment.py#L6), [current Constitution](../../.specify/memory/constitution.md#L315), [two-principle approval test](../../tests/contract/test_constitutional_compliance.py#L98). | AUD-004, AUD-009 |
| FR-004a | MISSING | Criteria exist in [the requirement](spec.md#L129), but inspected [form](../../apps/web/src/components/governance/AssessmentForm.tsx#L5) and card expose labels/free text, not six principle-specific question sets. No matching UI assertion found in searched web tests. | AUD-009, AUD-024 |
| FR-005 | PARTIAL | Assessment metadata and history exist; actor is caller-supplied, empty rationale/list members pass, and atomic uniqueness is absent: [create](../../apps/api/app/api/governance.py#L118), [model](../../packages/domain/src/domain/models/constitutional_assessment.py#L20), [validation tests](../../tests/contract/test_constitutional_compliance.py#L49). | AUD-001, AUD-005, AUD-011 |
| FR-006 | MISSING | Required ingestion gate is absent; [only new assignment is blocked](../../apps/api/app/services/governance_registry.py#L263), [test mirrors that narrower behavior](../../tests/contract/test_constitutional_compliance.py#L107), [ingestion writes directly](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12). | AUD-002, AUD-003, AUD-013 |
| FR-007 | PARTIAL | Primary/secondary creation exists but no authorized-route binding, catalogue relationship, or UI assignment control: [assign](../../apps/api/app/services/governance_registry.py#L263), [positive test](../../tests/contract/test_governance_assignment.py#L65). | AUD-001, AUD-014, AUD-016, AUD-020 |
| FR-008 | PARTIAL | Ordered-list fields, thresholds/categories stored; ordering/payload validation and category editing incomplete: [step](../../packages/domain/src/domain/models/handoff_chain.py#L22), [validator](../../apps/api/app/validators/governance_validators.py#L40), [valid-chain assertion](../../tests/contract/test_governance_assignment.py#L103). | AUD-015, AUD-020 |
| FR-009 | PARTIAL | Five-name, continuity and numeric range checks exist; payload compatibility and primary absence escape validation: [validator](../../apps/api/app/validators/governance_validators.py#L40), [negative tests](../../tests/contract/test_governance_assignment.py#L126). | AUD-014, AUD-015, AUD-016 |
| FR-009a | PARTIAL | Structured lookup returns target/confidence/category fields, but validity/eligibility and serving contract are incomplete: [lookup](../../apps/api/app/api/governance.py#L252), [model](../../packages/domain/src/domain/models/handoff_chain.py#L22), [cache helper tests](../../tests/integration/test_governance_cache.py#L21). | AUD-002, AUD-015, AUD-018, AUD-021 |
| FR-009b | IMPLEMENTED | Explicit downstream boundary in [requirement](spec.md#L142) and [research](research.md#L77). No agent-runtime routing implementation or execution is credited or demanded here. | AUD-018 for NFR ownership clarification only |
| FR-009c | CONFLICT | Hardcoded five-name set is not the referenced development-actor catalogue and cannot detect changed names: [set](../../apps/api/app/validators/governance_validators.py#L5), [catalogue purpose](../../.github/agents/AGENTS.md#L11), [literal-only rejection test](../../tests/contract/test_governance_assignment.py#L88). | AUD-014 |
| FR-010 | PARTIAL | Shared primary/secondary roles and scope strings persist, but lifecycle/coordination can leave incompatible chains: [assignment](../../apps/api/app/services/governance_registry.py#L263), [secondary assertion](../../tests/contract/test_governance_assignment.py#L73). | AUD-005, AUD-011, AUD-016 |
| FR-010a | PARTIAL | Private repository override/national fallback exists; unique eligible rules and public tie-resolution outcome absent: [resolver](../../apps/api/app/repositories/governance_repository.py#L418), [private helper test](../../tests/contract/test_governance_assignment.py#L177). | AUD-017 |
| FR-011 | PARTIAL | Original API summary and newer dashboard exist, but active UI is seed-only and required agent/chain/gap filters/state are incomplete: [composition](../../apps/api/app/api/routes/governance_dashboard.py#L71), [legacy summary](../../apps/api/app/services/governance_registry.py#L378), [weak filter test](../../tests/integration/test_governance_dashboard_api.py#L86). | AUD-019, AUD-020, AUD-021, AUD-022 |
| FR-012 | PARTIAL | Any update with assessments writes a re-review event, without material-change discrimination or persisted review work: [trigger](../../apps/api/app/services/governance_registry.py#L172), [audit-only assertion](../../tests/integration/test_governance_rereview.py#L30). | AUD-008 |
| FR-012a | PARTIAL | Uncalled amendment helper counts audit events; no versioned invalidation and pending=0: [helper](../../apps/api/app/services/governance_registry.py#L177), [test](../../tests/integration/test_governance_rereview.py#L51). | AUD-008, AUD-009 |
| FR-012b | PARTIAL | Manual start/extend/block/expiry code exists; automatic failed-review transition, schedule, config and notifications missing: [grace](../../apps/api/app/services/governance_registry.py#L193), [manual tests](../../tests/integration/test_governance_grace_period.py#L59). | AUD-002, AUD-003, AUD-023 |
| FR-013 | PARTIAL | Many audit writes and retrieval exist, but not every transition, immutable storage, authentic identity or replay payload: [audit helper](../../apps/api/app/services/governance_registry.py#L32), [upsert](../../apps/api/app/repositories/governance_repository.py#L456), [two-action test](../../tests/contract/test_governance_dashboard.py#L86). | AUD-001, AUD-005, AUD-006, AUD-021 |
| FR-014 | PARTIAL | Empty-assessment/empty-assignment checks work in service tests, but incomplete profiles/primary/chain gaps and active UI are not connected: [detector](../../apps/api/app/services/governance_registry.py#L363), [tests](../../tests/contract/test_governance_dashboard.py#L70). | AUD-004, AUD-019, AUD-022 |
| FR-015 | MISSING | No attached governance role enforcement after route/middleware search: [helpers](../../apps/api/app/api/governance.py#L46), [router inclusion](../../apps/api/app/api/router.py#L75), [middleware scope](../../apps/api/app/middleware/rbac_check.py#L32). Original tests do not exercise role denials. | AUD-001, AUD-007, AUD-024 |
| FR-016 | PARTIAL | Managed-identity Cosmos access exists, but sensitive asset access/classification/scope and reliable audit remain incomplete: [client](../../apps/api/app/repositories/governance_repository.py#L252), [classifier exclusion](../../apps/api/app/middleware/classifier_gateway.py#L36), [audit model](../../packages/domain/src/domain/models/governance_audit.py#L36). | AUD-001, AUD-005, AUD-006, AUD-007, AUD-025 |
| NFR-001 | UNVERIFIED | Timing log exists; no inspected <=50ms p95 API measurement. [Service timer](../../apps/api/app/services/governance_registry.py#L422), [cache tests](../../tests/integration/test_governance_cache.py#L21). | AUD-018, AUD-023, AUD-026 |
| NFR-002 | CONFLICT | Constructor TTL=300 exists server-side; no Redis/retained expired fallback; agent-side obligation conflicts with runtime deferral. [Cache](../../apps/api/app/services/governance_cache.py#L6), [TTL test](../../tests/integration/test_governance_cache.py#L31), [boundary](spec.md#L142). | AUD-018, AUD-026 |
| NFR-003 | CONFLICT | Safe agent defaults belong to deferred runtime integration; API lookup has no outage fallback and tests exercise no unavailable registry: [lookup](../../apps/api/app/api/governance.py#L252), [test file](../../tests/integration/test_governance_cache.py#L1). | AUD-018, AUD-024, AUD-026 |
| NFR-004 | UNVERIFIED | Cosmos/Redis provisioning exists, but survival/failover/recovery outcomes are not established; split local state and seed failure also matter: [container](../../infra/main.bicep#L701), [bootstrap](../../apps/api/app/api/governance.py#L64), [backend](../../apps/api/app/repositories/governance_repository.py#L37). | AUD-005, AUD-010, AUD-018, AUD-026 |
| NFR-005 | PARTIAL | Audit failure log, miss-path timer, and read-driven gap/expiry logs exist; mutation metrics/cache export are incomplete: [audit exception](../../apps/api/app/services/governance_registry.py#L32), [summary logging](../../apps/api/app/services/governance_registry.py#L378), [cache statistics test](../../tests/integration/test_governance_cache.py#L56). | AUD-023 |
| SC-001 | UNVERIFIED | 46 unique seed entries were counted by JSON inspection; test only requires >=40 imports. No registry intersection snapshot or SME-panel validation: [seed test](../../tests/contract/test_data_source_registry.py#L116), [criterion](spec.md#L196). | AUD-010, AUD-027 |
| SC-002 | UNVERIFIED | No operational-readiness all-principle snapshot; code can falsely approve partial coverage: [criterion](spec.md#L197), [test](../../tests/contract/test_constitutional_compliance.py#L98). | AUD-004, AUD-008, AUD-009, AUD-027 |
| SC-003 | UNVERIFIED | No snapshot proving every approved source has assignment/chain and zero gaps; stale status/incomplete-gap logic contradict the intended gate: [criterion](spec.md#L198), [derivation](../../apps/api/app/services/governance_registry.py#L326). | AUD-015, AUD-016, AUD-022, AUD-027 |
| SC-004 | UNVERIFIED | No timed authorized-user study; source/assignment UI is incomplete: [criterion](spec.md#L199), [placeholder](../../apps/web/src/app/governance/data-sources/page.tsx#L22). | AUD-020, AUD-027 |
| SC-005 | UNVERIFIED | No participant denominator/timing record; current dashboard is not live, and conditional tests do not measure gap identification: [criterion](spec.md#L200), [E2E](../../tests/e2e/test_governance_dashboard.spec.ts#L19). | AUD-019, AUD-022, AUD-024, AUD-027 |
| SC-006 | UNVERIFIED | No reconstructive replay run; current event payloads/atomicity cannot support the claimed gap-free audit: [criterion](spec.md#L201), [audit test](../../tests/contract/test_governance_dashboard.py#L86). | AUD-005, AUD-006, AUD-027 |
| FR-CAP-005-001 | PARTIAL | AU regime is explicitly in scope inside a deferred-country amendment, but governance control/assessment mapping is not established; PH/JP/BD remain deliberately deferred. [Requirement](spec.md#L239), [documentation-only decision](../028-capstone-alignment/evidence/decision-record.md#L11), [classifier](../../apps/api/app/middleware/classifier_gateway.py#L36). | AUD-009, AUD-025, AUD-028 |
| FR-CAP-005-002 | UNVERIFIED | Default-forbid transfer rule and promotion prerequisites are authored; no governance-specific transfer control or legal activation evidence identified. No cross-border transfer is asserted to have occurred. [Requirement](spec.md#L240), [bounded exception](../../.specify/memory/constitution.md#L245). | AUD-025, AUD-028 |

## Acceptance and Edge-Case Coverage

AS identifiers below are local labels for each separately numbered scenario in the corresponding user story, not new specification IDs.

| Scenario | Status | Inspected implementation and assertion | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Scenario](spec.md#L20): metadata fields exist, but [table](../../apps/web/src/components/governance/DataSourceTable.tsx#L36) omits type/cadence and active replacement is not the live catalogue. [List test](../../tests/contract/test_data_source_registry.py#L53) counts service rows only. | AUD-010, AUD-011, AUD-019, AUD-020 |
| US1-AS2 | PARTIAL | [Scenario](spec.md#L21): [POST](../../apps/api/app/api/data_sources.py#L38) saves in its own repository; no complete add-source UI/cross-router immediacy test. [Registration test](../../tests/contract/test_data_source_registry.py#L32). | AUD-001, AUD-010, AUD-020 |
| US1-AS3 | PARTIAL | [Scenario](spec.md#L22): [deactivate](../../apps/api/app/services/governance_registry.py#L98) preserves record/timestamp; [test](../../tests/contract/test_data_source_registry.py#L84) never verifies ingestion exclusion, incident guard, or retained linked history. | AUD-002, AUD-006, AUD-013 |
| US1-AS4 | PARTIAL | [Scenario](spec.md#L23): [kind filter](../../apps/api/app/api/data_sources.py#L49) and [service assertion](../../tests/contract/test_data_source_registry.py#L58) exist, but original UI default URL is wrong and new matrix category options omit social/IoT/field reports. | AUD-020, AUD-021, AUD-024 |
| US2-AS1 | PARTIAL | [Scenario](spec.md#L37): [profile route](../../apps/api/app/api/governance.py#L108) returns current/history; [page](../../apps/web/src/app/governance/%5BdataSourceId%5D/compliance/page.tsx#L24) shows only existing assessments, not every required principle/criteria. | AUD-004, AUD-009, AUD-024 |
| US2-AS2 | PARTIAL | [Scenario](spec.md#L38): [card](../../apps/web/src/components/governance/ComplianceCard.tsx#L35) renders gaps/conditions and [service validation](../../tests/contract/test_constitutional_compliance.py#L57) requires lists, but blank elements/criteria coverage are unguarded and no rendering assertion was found. | AUD-009, AUD-011, AUD-024 |
| US2-AS3 | PARTIAL | [Scenario](spec.md#L39): partial assessment, conditions, server time and editable assessor persist via [form](../../apps/web/src/components/governance/AssessmentForm.tsx#L80); authenticated conditional-approval identity and event semantics are not established. | AUD-001, AUD-004, AUD-006, AUD-011 |
| US2-AS4 | MISSING | [Scenario](spec.md#L40): [test](../../tests/contract/test_constitutional_compliance.py#L107) blocks assignment, while [ingestion](../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12) still accepts the source. | AUD-002, AUD-003 |
| US3-AS1 | PARTIAL | [Scenario](spec.md#L54): [assignment storage](../../apps/api/app/services/governance_registry.py#L263) and [positive assertion](../../tests/contract/test_governance_assignment.py#L65) exist; authorization and UI create path do not. | AUD-001, AUD-014, AUD-016, AUD-020 |
| US3-AS2 | PARTIAL | [Scenario](spec.md#L55): [continuity checks](../../apps/api/app/validators/governance_validators.py#L40) and [negative assertion](../../tests/contract/test_governance_assignment.py#L126) exist; payload compatibility and current catalogue validation do not. | AUD-014, AUD-015 |
| US3-AS3 | SUPERSEDED for runtime filtering; PARTIAL for retained configuration | [Scenario](spec.md#L56) is narrowed by [clarification](spec.md#L90) and [FR-009b](spec.md#L142). Threshold storage/query exists in [chain model](../../packages/domain/src/domain/models/handoff_chain.py#L22); operational forwarding is downstream, while configuration/editor/serving fixes remain. | AUD-015, AUD-018, AUD-020 |
| US3-AS4 | PARTIAL | [Scenario](spec.md#L57): per-source [profile](../../apps/api/app/services/governance_registry.py#L318) exists; no complete active governance map combining all sources, assignments, chains, thresholds, and gaps. | AUD-019, AUD-020, AUD-022 |
| US4-AS1 | PARTIAL | [Scenario](spec.md#L71): [service summary](../../apps/api/app/services/governance_registry.py#L378) includes most counters; [test](../../tests/contract/test_governance_dashboard.py#L51) covers only a subset; actual landing path is disconnected. | AUD-019, AUD-022 |
| US4-AS2 | PARTIAL | [Scenario](spec.md#L72): [legacy filtering](../../apps/api/app/api/governance.py#L268) exists; [new data service](../../apps/api/app/services/governance_data_service.py#L623) emits seed-pending entries, and [test](../../tests/integration/test_governance_dashboard_api.py#L86) checks 200 only. | AUD-019, AUD-021, AUD-024 |
| US4-AS3 | PARTIAL | [Scenario](spec.md#L73): [detector](../../apps/api/app/services/governance_registry.py#L363) and [unassigned test](../../tests/contract/test_governance_dashboard.py#L77) cover empty assignments, but new matrix's zero gaps and absent unassigned filter hide them. | AUD-019, AUD-020, AUD-022 |
| EC-01: multiple consuming agents | PARTIAL | [Edge case](spec.md#L79); [secondary assignment test](../../tests/contract/test_governance_assignment.py#L73) proves recording, not unambiguous lifecycle after primary/chain changes. | AUD-015, AUD-016 |
| EC-02: source format/availability/terms change | PARTIAL | [Edge case](spec.md#L80); [source-change test](../../tests/integration/test_governance_rereview.py#L30) asserts an audit marker only; terms/version/workflow state are not represented. | AUD-003, AUD-008 |
| EC-03: social intelligence plus misinformation risk | PARTIAL | [Edge case](spec.md#L81); tier-6 [social seed](../../packages/domain/src/domain/seed/data_sources_australia.json#L443) and assessment conditions/gaps support human recording; no demonstrated assessed social source, criterion presentation, or enforcement test. | AUD-002, AUD-009, AUD-025, AUD-027 |
| EC-04: national source with jurisdictional differences | PARTIAL | [Edge case](spec.md#L82); geography and [precedence inheritance](../../apps/api/app/repositories/governance_repository.py#L205) exist; per-jurisdiction source terms/formats/applicability and authorized variation workflow are not established. | AUD-008, AUD-017, AUD-025 |
| EC-05: private IoT without agreement | PARTIAL | [Edge case](spec.md#L83); model/form can record a privacy gap, but no agreement-specific worksheet/control or source-blocking assertion exists. [Assessment validation](../../apps/api/app/services/governance_registry.py#L110). | AUD-002, AUD-009, AUD-011, AUD-025 |
| EC-06: contradictory same-hazard/location sources | PARTIAL | [Edge case](spec.md#L84); [private resolver test](../../tests/contract/test_governance_assignment.py#L177) covers inheritance; [generic contradiction detector](../../apps/agents/risk_assessment/correlation.py#L132) does not consult those records or implement the required equal-tier/no-rule decision contract. | AUD-012, AUD-017 |

## Original Task Coverage

Each row preserves the original checkbox and evaluates the task's actual scope. IMPLEMENTED setup/model/view slices do not
waive shared authorization, lifecycle, integration, or execution findings. Evidence under tests is inspected assertion source only.

| Original task | Original checkbox | Status | Concrete implementation and test evidence | Follow-ups |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Source routes](../../apps/api/app/api/data_sources.py#L9) and [governance routes](../../apps/api/app/api/governance.py#L58) are substantive routers, included by the application, not empty files. Their behavior is separately audited below. | AUD-001, AUD-010 |
| T002 | [X] | IMPLEMENTED | [Registry class](../../apps/api/app/services/governance_registry.py#L26) and [cache class](../../apps/api/app/services/governance_cache.py#L9) are constructed by routes and exercised by [service fixture](../../tests/contract/test_data_source_registry.py#L14)/[cache tests](../../tests/integration/test_governance_cache.py#L21). Stub-creation scope met; production guarantees are not. | AUD-010, AUD-018 |
| T003 | [X] | IMPLEMENTED | [Repository facade/backend selection](../../apps/api/app/repositories/governance_repository.py#L29) is used by [registry constructor](../../apps/api/app/services/governance_registry.py#L27); later Cosmos completeness is T014. | AUD-005, AUD-007 |
| T004 | [X] | IMPLEMENTED | [Validator functions](../../apps/api/app/validators/governance_validators.py#L31) are called by [assignment/chain services](../../apps/api/app/services/governance_registry.py#L263); [chain tests](../../tests/contract/test_governance_assignment.py#L126) assert narrow checks. | AUD-014, AUD-015 |
| T005 | [X] | IMPLEMENTED | [Router aggregation](../../apps/api/app/api/router.py#L75) and [app inclusion](../../apps/api/app/main.py#L73) mount both routers via the existing owning abstraction. No registration-in-main absence claim. | AUD-001, AUD-010 |
| T006 | [X] | PARTIAL | [All requested fields](../../packages/domain/src/domain/models/data_source.py#L35) exist; [rank validator](../../packages/domain/src/domain/models/data_source.py#L61) breaks rank-only compatibility and PATCH consistency. [Test](../../tests/contract/test_data_source_registry.py#L46) covers construction only. | AUD-011, AUD-012, AUD-013 |
| T007 | [X] | PARTIAL | [Assessment model](../../packages/domain/src/domain/models/constitutional_assessment.py#L20) has fields and literal statuses; [service](../../apps/api/app/services/governance_registry.py#L110) checks list presence, but nonempty values/version/current uniqueness are incomplete. [Tests](../../tests/contract/test_constitutional_compliance.py#L49). | AUD-004, AUD-005, AUD-009, AUD-011 |
| T008 | [X] | PARTIAL | [Assignment model](../../packages/domain/src/domain/models/agent_governance.py#L13) records role/scope/actor; catalogue, nonempty scope and lifecycle invariants are incomplete. [Primary/secondary tests](../../tests/contract/test_governance_assignment.py#L64). | AUD-011, AUD-014, AUD-016 |
| T009 | [X] | PARTIAL | [Step/chain models](../../packages/domain/src/domain/models/handoff_chain.py#L22) carry fields; ordering/payload/primary validation and updated timestamps incomplete. [Chain assertions](../../tests/contract/test_governance_assignment.py#L102). | AUD-014, AUD-015 |
| T010 | [X] | PARTIAL | [Precedence model](../../packages/domain/src/domain/models/functional_domain_precedence.py#L8) and [repo helper](../../apps/api/app/repositories/governance_repository.py#L205) exist; eligibility/uniqueness constraints absent. [Private helper test](../../tests/contract/test_governance_assignment.py#L177). | AUD-005, AUD-017 |
| T011 | [X] | PARTIAL | [Mutable audit model](../../packages/domain/src/domain/models/governance_audit.py#L36) supplies fields/action enum but not immutability. [Audit assertion](../../tests/contract/test_governance_dashboard.py#L86) checks only two action names. | AUD-006, AUD-007 |
| T012 | [X] | IMPLEMENTED | [46-entry JSON](../../packages/domain/src/domain/seed/data_sources_australia.json#L1) contains named BoM/GA/fire/SES, health/transport/utilities, sensor, social, community, field and derived families. [Load/field tests](../../tests/contract/test_data_source_registry.py#L115) exist; SME coverage is UNVERIFIED. | AUD-027 |
| T013 | [X] | IMPLEMENTED | [Bootstrap key](../../packages/domain/src/domain/seed/bootstrap.py#L59) loads the catalogue and [registry import](../../apps/api/app/services/governance_registry.py#L57) consumes it. [Seed test](../../tests/contract/test_data_source_registry.py#L116) covers import source. | AUD-010, AUD-027 |
| T014 | [X] | PARTIAL | [Cosmos backend](../../apps/api/app/repositories/governance_repository.py#L264) implements all six entity accesses and [provisioned partition](../../infra/main.bicep#L701) matches. No complete transaction, scope, or actual SDK/durability evidence; original fixtures use default backend selection. | AUD-005, AUD-006, AUD-007, AUD-010, AUD-026 |
| T015 | [X] | CONFLICT | [Hardcoded agents and continuity validator](../../apps/api/app/validators/governance_validators.py#L5) do not implement the [referenced catalogue](../../.github/agents/AGENTS.md#L11). [Invalid-agent test](../../tests/contract/test_governance_assignment.py#L88) only constructs a Literal-invalid model. | AUD-014, AUD-015 |
| T016 | [X] | PARTIAL | [Audit helper](../../apps/api/app/services/governance_registry.py#L32) appends/logs failures, but [Cosmos upsert](../../apps/api/app/repositories/governance_repository.py#L456) can replace IDs and mutation/audit commits are separate. | AUD-005, AUD-006 |
| T017 | [X] | PARTIAL | [POST](../../apps/api/app/api/data_sources.py#L38) reaches [register/save/audit](../../apps/api/app/services/governance_registry.py#L71); mandatory validation/authentication and shared service absent. [Registration test](../../tests/contract/test_data_source_registry.py#L32) is service-only. | AUD-001, AUD-006, AUD-010, AUD-011, AUD-024 |
| T018 | [X] | PARTIAL | [Listing route](../../apps/api/app/api/data_sources.py#L49) supports source-field filters but no agent filter. [Kind/trust tests](../../tests/contract/test_data_source_registry.py#L58) do not cover all advertised filters or HTTP. | AUD-010, AUD-021, AUD-024 |
| T019 | [X] | IMPLEMENTED | [GET route](../../apps/api/app/api/data_sources.py#L76) reaches [404-producing service](../../apps/api/app/services/governance_registry.py#L78) and backend point-read; single-source retrieval slice exists. HTTP/missing-source assertion and shared auth/composition risks remain. | AUD-001, AUD-010, AUD-024 |
| T020 | [X] | PARTIAL | [PATCH route](../../apps/api/app/api/data_sources.py#L82) reaches [unvalidated mutation/re-review](../../apps/api/app/services/governance_registry.py#L87); [update tests](../../tests/contract/test_data_source_registry.py#L99) only check a provider and event name. | AUD-001, AUD-005, AUD-008, AUD-011, AUD-012, AUD-013 |
| T021 | [X] | PARTIAL | [Deactivation](../../apps/api/app/services/governance_registry.py#L98) saves timestamp/history record but no incident guard/ingestion gate. [Tests](../../tests/contract/test_data_source_registry.py#L83) cover status and repeated call only. | AUD-002, AUD-006, AUD-013 |
| T022 | [X] | PARTIAL | [Import loop](../../apps/api/app/services/governance_registry.py#L57) loads/bootstrap-skips existing IDs; [route startup](../../apps/api/app/api/governance.py#L64) is one-sided/best-effort with no retry after failure. [Seed test](../../tests/contract/test_data_source_registry.py#L116) checks one fresh service. | AUD-005, AUD-010, AUD-027 |
| T023 | [X] | PARTIAL | [DataSourceTable](../../apps/web/src/components/governance/DataSourceTable.tsx#L36) has kind/status filters only, default `/api/v1`, missing sub-category/trust filters. [E2E filter](../../tests/e2e/test_governance_dashboard.spec.ts#L10) is conditional and has no row assertion. | AUD-020, AUD-024 |
| T024 | [X] | PARTIAL | [12 registry cases](../../tests/contract/test_data_source_registry.py#L31) exercise direct services, a subset of filters, simple deactivation and >=40 seeds. Missing HTTP, auth, invalid metadata, guard, persistence parity, deterministic SC-001 coverage. | AUD-010, AUD-011, AUD-012, AUD-013, AUD-021, AUD-024, AUD-027 |
| T025 | [X] | IMPLEMENTED | [GET profile](../../apps/api/app/api/governance.py#L108) reaches [source check and current/history split](../../apps/api/app/services/governance_registry.py#L148); [supersession test](../../tests/contract/test_constitutional_compliance.py#L71) verifies current IDs. Shared auth/complete-rubric risks do not negate this retrieval slice. | AUD-001, AUD-004, AUD-009, AUD-024 |
| T026 | [X] | PARTIAL | [POST](../../apps/api/app/api/governance.py#L118) and [supersession service](../../apps/api/app/services/governance_registry.py#L110) implement sequential history and list-presence checks. Actor validation, all-principle/rubric semantics, atomicity and complete audit absent. | AUD-001, AUD-004, AUD-005, AUD-006, AUD-009, AUD-011 |
| T027 | [X] | PARTIAL | [Derivation](../../apps/api/app/services/governance_registry.py#L157) aggregates existing statuses, but incomplete profiles become compliant, failed re-review skips grace, and ingestion remains unguarded. [Tests](../../tests/contract/test_constitutional_compliance.py#L85). | AUD-002, AUD-003, AUD-004, AUD-016 |
| T028 | [X] | PARTIAL | [Source-change helper](../../apps/api/app/services/governance_registry.py#L172) only writes an event; [integration test](../../tests/integration/test_governance_rereview.py#L30) asserts only that marker. | AUD-008 |
| T029 | [X] | PARTIAL | [Amendment helper](../../apps/api/app/services/governance_registry.py#L177) is unconnected and creates no flags/version; [tests](../../tests/integration/test_governance_rereview.py#L50) assert returned counts, not re-evaluation state. | AUD-008, AUD-009 |
| T030 | [X] | PARTIAL | [Manual lifecycle](../../apps/api/app/services/governance_registry.py#L193) supports default duration/helpers, but no automatic review transition/scheduler/notifications; [expiry test](../../tests/integration/test_governance_grace_period.py#L80) edits state and calls the helper directly. | AUD-002, AUD-003, AUD-023 |
| T031 | [X] | PARTIAL | [Override route](../../apps/api/app/api/governance.py#L139) supports extend/block and 400/409 guards through service; actor is `api-user`, authorization absent, and no route/rationale test. [Service tests](../../tests/integration/test_governance_grace_period.py#L66). | AUD-001, AUD-003, AUD-006, AUD-021 |
| T032 | [X] | IMPLEMENTED | [ComplianceCard](../../apps/web/src/components/governance/ComplianceCard.tsx#L35) renders status/explanation/gaps/conditions/assessor/date and is used by [current/history page](../../apps/web/src/app/governance/%5BdataSourceId%5D/compliance/page.tsx#L68). No inspected rendering assertion; old principle labels need reconciliation. | AUD-009, AUD-024 |
| T033 | [X] | PARTIAL | [Working page/load](../../apps/web/src/app/governance/%5BdataSourceId%5D/compliance/page.tsx#L24) and [new assessment form](../../apps/web/src/components/governance/AssessmentForm.tsx#L80) exist, use `/api`, and show errors. Missing criteria/missing-principle presentation and authentic assessor binding remain. | AUD-001, AUD-004, AUD-009, AUD-024 |
| T034 | [X] | PARTIAL | [Seven compliance cases](../../tests/contract/test_constitutional_compliance.py#L49) cover sequential creation/supersession, list presence and assignment denial; they neither prove ingestion blocking nor complete-principle approval and codify the two-principle shortcut. | AUD-002, AUD-004, AUD-005, AUD-011, AUD-024 |
| T035 | [X] | PARTIAL | [Re-review cases](../../tests/integration/test_governance_rereview.py#L29) inspect audit counts; [grace cases](../../tests/integration/test_governance_grace_period.py#L59) call lifecycle helpers. No automatic review-to-grace path, notification/warning or continued-ingestion assertion. | AUD-002, AUD-003, AUD-008, AUD-023, AUD-024 |
| T036 | [X] | IMPLEMENTED | [GET governance](../../apps/api/app/api/governance.py#L168) calls [profile](../../apps/api/app/services/governance_registry.py#L318) to retrieve active assignments/chain after source existence check. [Assignment tests](../../tests/contract/test_governance_assignment.py#L64) exercise underlying writes; direct HTTP read assertions missing. | AUD-001, AUD-010, AUD-016, AUD-024 |
| T037 | [X] | PARTIAL | [Assignment route](../../apps/api/app/api/governance.py#L178) reaches [sequential primary revocation and non-compliant gate](../../apps/api/app/services/governance_registry.py#L263). Authorization, catalogue mapping, concurrency and chain consistency are incomplete. [Tests](../../tests/contract/test_governance_assignment.py#L64). | AUD-001, AUD-005, AUD-006, AUD-014, AUD-016 |
| T038 | [X] | PARTIAL | [PUT](../../apps/api/app/api/governance.py#L207) invokes [validation/deprecation](../../apps/api/app/services/governance_registry.py#L288) and local invalidation; payload/ordering/primary and cross-replica correctness missing. [Tests](../../tests/contract/test_governance_assignment.py#L102). | AUD-001, AUD-005, AUD-015, AUD-016, AUD-018 |
| T039 | [X] | PARTIAL | [GET/POST precedence](../../apps/api/app/api/governance.py#L231) call list/save, not effective resolution. [Repository test](../../tests/contract/test_governance_assignment.py#L177) proves helper inheritance only; duplicates/references/conflicts untested. | AUD-001, AUD-005, AUD-017, AUD-021 |
| T040 | [X] | PARTIAL | [Lookup](../../apps/api/app/api/governance.py#L252) queries/cache-serializes active chain, but Redis/header/outage/eligibility guarantees incomplete and p95 UNVERIFIED. [Cache tests](../../tests/integration/test_governance_cache.py#L21) never call HTTP lookup. | AUD-002, AUD-018, AUD-021, AUD-026 |
| T041 | [X] | PARTIAL | [Memory TTL/cache counters](../../apps/api/app/services/governance_cache.py#L9) exist; no governance Redis client, stale outage retention, safe default or comprehensive invalidation. [TTL/hit tests](../../tests/integration/test_governance_cache.py#L21) cover the limited implementation. | AUD-007, AUD-018, AUD-023, AUD-026 |
| T042 | [X] | PARTIAL | [Derivation](../../apps/api/app/services/governance_registry.py#L326) produces expected happy-path assigned/fully-governed states; [test](../../tests/contract/test_governance_assignment.py#L103) proves one order only. Rejection/primary replacement leaves inconsistent state. | AUD-004, AUD-016, AUD-022 |
| T043 | [X] | PARTIAL | [Editor](../../apps/web/src/components/governance/HandoffChainEditor.tsx#L26) edits sender/target/threshold only; categories never rendered, no existing-chain hydration, wrong URL and missing save failure handling. No direct UI assertion found. | AUD-015, AUD-020, AUD-024 |
| T044 | [X] | PARTIAL | [View](../../apps/web/src/app/governance/%5BdataSourceId%5D/assignments/page.tsx#L28) displays assignments/chain but uses `/api/v1`, swallows failures and has no assignment creation control. Named E2E never asserts assignment workflow. | AUD-020, AUD-024 |
| T045 | [X] | PARTIAL | [Eight assignment/precedence cases](../../tests/contract/test_governance_assignment.py#L64) cover limited happy/negative cases. Missing HTTP/auth/catalogue change/schema/ordering/uniqueness/real resolution/concurrent lifecycle assertions. | AUD-005, AUD-014, AUD-015, AUD-016, AUD-017, AUD-024 |
| T046 | [X] | PARTIAL | [Five cache cases](../../tests/integration/test_governance_cache.py#L21) cover hit/miss, zero TTL, invalidation, clear and rate; no unavailable registry, retained stale data, safe routing, Redis or HTTP header checks. | AUD-018, AUD-023, AUD-024, AUD-026 |
| T047 | [X] | PARTIAL | [Dashboard route](../../apps/api/app/api/governance.py#L268) builds summary/active source list; `agent_name` is ignored and [pending count](../../apps/api/app/services/governance_registry.py#L406) is zero. New landing path does not consume these mutations. | AUD-008, AUD-019, AUD-021, AUD-022 |
| T048 | [X] | PARTIAL | [Two missing-collection checks](../../apps/api/app/services/governance_registry.py#L363) and [tests](../../tests/contract/test_governance_dashboard.py#L70) exist; no complete review/primary/chain/stale-reference projection or connected per-source UI count. | AUD-004, AUD-016, AUD-022 |
| T049 | [X] | PARTIAL | [Audit endpoint](../../apps/api/app/api/governance.py#L298) delegates filterable sorted backend retrieval; aliases/timezone/errors/source 404/auth differ from contract. [Action test](../../tests/contract/test_governance_dashboard.py#L94) is service-only. | AUD-001, AUD-006, AUD-007, AUD-021 |
| T050 | [X] | PARTIAL | [Eight cards](../../apps/web/src/components/governance/GovernanceSummary.tsx#L20) omit assigned/gap/re-review counters and are behind the superseded entry presentation. [Original E2E](../../tests/e2e/test_governance_dashboard.spec.ts#L4) checks only Total Sources. | AUD-019, AUD-022, AUD-024 |
| T051 | [X] | PARTIAL | [Root redirects](../../apps/web/src/app/governance/page.tsx#L29) to [new dashboard](../../apps/web/src/app/governance/dashboard/page.tsx#L20). Entry presentation is evidenced supersession, but required live source/governance filters/map/gaps are not delivered by the replacement. | AUD-019, AUD-020, AUD-022 |
| T052 | [X] | PARTIAL | [Seven dashboard cases](../../tests/contract/test_governance_dashboard.py#L46) cover some counts, empty collections and two action names. Missing real HTTP filters, per-source gaps, all action/date queries and actual dashboard read-after-write. | AUD-019, AUD-021, AUD-022, AUD-024 |
| T053 | [X] | PARTIAL | [Four Playwright cases](../../tests/e2e/test_governance_dashboard.spec.ts#L4) contain conditional checks and no filter-result assertion. [New E2E](../../tests/e2e/governance-dashboard.spec.ts#L11) proves intended redirect/navigation source, not original governance acceptance or execution. | AUD-020, AUD-024, AUD-027 |
| T054 | [X] | PARTIAL | [Audit failure log](../../apps/api/app/services/governance_registry.py#L32), [dashboard-triggered warning/gap log](../../apps/api/app/services/governance_registry.py#L378) and [lookup timer](../../apps/api/app/services/governance_registry.py#L422) exist; required mutation metrics/hit path/export incomplete. | AUD-023, AUD-026 |
| T055 | [X] | MISSING | Required attached authorization absent after middleware/router/caller trace: [helpers](../../apps/api/app/api/governance.py#L46), [production scope](../../apps/api/app/middleware/entra_auth.py#L38), [source routes](../../apps/api/app/api/data_sources.py#L9). No original denial assertions. | AUD-001, AUD-007, AUD-025 |
| T056 | [X] | UNVERIFIED | [Eight-step rehearsal instructions](quickstart.md#L129) and [checkbox](tasks.md#L143) exist; no scoped execution record found. Manual helper tests cannot prove the rehearsal occurred. | AUD-026, AUD-027, AUD-028 |
| T057 | [X] | UNVERIFIED | [Six criteria](spec.md#L196) and [checkbox](tasks.md#L144) exist; no SME/timing/readiness/replay measurements establish them. Each outcome is assessed separately above. | AUD-004, AUD-006, AUD-019, AUD-026, AUD-027, AUD-028 |

## Associated Claims Assessment

### All 28 Quality-Checklist Claims

The original checklist is entirely checked. Rows below distinguish a sound authored requirement from a demonstrated outcome.

| Claim at original line | Status | Assessment and related follow-up |
| --- | --- | --- |
| [9: no implementation details](checklists/requirements.md#L9) | CONFLICT | Spec names fields, storage-related APIs/contracts and a package seed path; this is not purely implementation-free prose. AUD-028. |
| [10: user/business focus](checklists/requirements.md#L10) | IMPLEMENTED | Four role-oriented stories and operational outcomes are authored. Not evidence of user testing. |
| [11: nontechnical audience](checklists/requirements.md#L11) | PARTIAL | Stories are readable; field/API/runtime-cache details still require technical interpretation. AUD-028. |
| [12: mandatory sections complete](checklists/requirements.md#L12) | IMPLEMENTED | Scenarios, requirements, entities, assumptions and outcomes are present; amendments add further taxonomy. |
| [16: no clarification markers](checklists/requirements.md#L16) | IMPLEMENTED | Full local spec contains no unresolved placeholder marker; substantive catalogue/cache/version conflicts still exist. AUD-014/AUD-018. |
| [17: testable/unambiguous requirements](checklists/requirements.md#L17) | CONFLICT | Agent catalogue identity, runtime cache ownership, approval completeness and current Constitution require resolution. AUD-004/AUD-009/AUD-014/AUD-018. |
| [18: measurable SCs](checklists/requirements.md#L18) | IMPLEMENTED | Six measurable targets are written. No result is implied. AUD-027 obtains measurements. |
| [19: technology-agnostic SCs](checklists/requirements.md#L19) | IMPLEMENTED | Coverage/readiness/time/usability/audit outcomes are not tied to a language or cloud SDK. |
| [20: acceptance scenarios defined](checklists/requirements.md#L20) | IMPLEMENTED | All 15 numbered scenarios are authored and individually assessed here. |
| [21: edge cases identified](checklists/requirements.md#L21) | IMPLEMENTED | Six are authored; delivery is separately PARTIAL above. |
| [22: clear scope boundary](checklists/requirements.md#L22) | CONFLICT | FR-009b is explicit, but agent-side NFR wording and the historical routing-only inclusion need harmonization. AUD-018/AUD-028. |
| [23: dependencies/assumptions identified](checklists/requirements.md#L23) | IMPLEMENTED | Catalogue, Constitution, runtime deferral and AU context are named; their satisfaction/validation is not proved. |
| [27: all FRs have clear acceptance](checklists/requirements.md#L27) | PARTIAL | Core scenarios exist; authorization, versioning, metrics, race/failure behavior and deferred-country controls lack concrete original acceptance assertions. AUD-024/AUD-025. |
| [28: scenarios cover primary flows](checklists/requirements.md#L28) | IMPLEMENTED | Catalogue, review, assignment and dashboard flows are specified. No performed rehearsal inferred. |
| [29: feature meets SC outcomes](checklists/requirements.md#L29) | UNVERIFIED | Checklist cannot establish catalogue panel approval, readiness, workflow/usability timing or audit replay. AUD-027. |
| [30: no implementation leakage](checklists/requirements.md#L30) | CONFLICT | Same authored-prose conflict as line 9; do not rewrite history in this audit. AUD-028. |
| [34: trust tiers defined](checklists/requirements.md#L34) | IMPLEMENTED | Seven semantics and mapping are written; implementation compatibility remains PARTIAL (AUD-012). |
| [35: principle criteria specified](checklists/requirements.md#L35) | IMPLEMENTED | FR-004a specifies criteria in prose, but actual assessor presentation is MISSING (AUD-009). |
| [36: latency/cache/degradation NFRs](checklists/requirements.md#L36) | IMPLEMENTED | NFRs are authored; cache scope is CONFLICT and measured outcomes UNVERIFIED (AUD-018/AUD-026). |
| [37: amendment trigger defined](checklists/requirements.md#L37) | IMPLEMENTED | Requirement is explicit, implementation is audit-only (AUD-008). |
| [38: model divergence/reconciliation](checklists/requirements.md#L38) | PARTIAL | [Reconciliation table](data-model.md#L207) exists, but trust field/property choice and legacy decoding differ from research/code. AUD-011/AUD-012. |
| [39: cross-spec agent validation required](checklists/requirements.md#L39) | IMPLEMENTED | Obligation is written; current catalogue/runtime mismatch remains CONFLICT (AUD-014). |
| [40: registry security requirements](checklists/requirements.md#L40) | IMPLEMENTED | FR-015/FR-016 are explicit, but attached enforcement is MISSING (AUD-001). |
| [41: hierarchical precedence](checklists/requirements.md#L41) | PARTIAL | Repository inheritance exists; active eligible uniqueness/public resolution/human tie behavior incomplete (AUD-017). |
| [42: agent refactoring deferred](checklists/requirements.md#L42) | IMPLEMENTED | Explicit scope statement; respected by this audit, not a runtime pass. |
| [43: structured seed delivered](checklists/requirements.md#L43) | IMPLEMENTED | JSON/loader/import source exists with 46 unique entries; SME/operational coverage UNVERIFIED (AUD-027). |
| [44: grace period defined](checklists/requirements.md#L44) | IMPLEMENTED | FR-012b specifies it; automatic lifecycle/notifications are not implemented end-to-end (AUD-003). |
| [45: observability required](checklists/requirements.md#L45) | IMPLEMENTED | Five categories are specified; actual mutation/hit/expiry/export coverage is PARTIAL (AUD-023). |

Checklist notes correctly restate the seed, seven tiers, five NFRs, grace period and runtime deferral. The statement that the
spec is ready for planning is an authored readiness opinion, not evidence that implementation, test execution, or approval occurred.

### Plan Gate Claims

Each PASS below is evaluated independently; neither section identifies an executed gate run or approval record for this baseline.

| Gate claim | Status | Evidence assessment |
| --- | --- | --- |
| [Pre: Life Safety](plan.md#L30) | PARTIAL | Assignment denial exists; active ingestion/grace/audit protections do not satisfy the claim. AUD-002/AUD-003/AUD-006. |
| [Pre: Multi-Agent Coordination](plan.md#L31) | PARTIAL | Stored assignments/chains exist; catalogue and lifecycle consistency incomplete. AUD-014/AUD-015/AUD-016. |
| [Pre: Trust/Provenance](plan.md#L32) | PARTIAL | Fields/catalogue exist; validation, compatibility and precedence incomplete. AUD-011/AUD-012/AUD-017. |
| [Pre: Privacy/Security](plan.md#L33) | PARTIAL | Requirements and identity-backed storage exist, but governance route/tenant/classification controls are not demonstrated. AUD-001/AUD-007/AUD-025. |
| [Pre: Multilingual/Accessibility](plan.md#L34) | PARTIAL | Criterion is required but not rendered as guidance; no human review/accessibility execution proof. AUD-009/AUD-024. |
| [Pre: Cloud Platform](plan.md#L35) | PARTIAL | Cosmos/Redis infrastructure exists; governance cache does not use Redis and deployment/residency outcomes remain UNVERIFIED. AUD-018/AUD-026. |
| [Pre: Quality/Readiness](plan.md#L36) | UNVERIFIED | Observability/dashboard/audit gaps remain, with no rehearsal or operational readiness evidence. AUD-023/AUD-027. |
| [Post: Life Safety](plan.md#L40) | PARTIAL | Model/service assignment rule is not an ingestion guard; graceful re-review and immutable audit claims are not supported. AUD-002/AUD-003/AUD-005/AUD-006. |
| [Post: Multi-Agent Coordination](plan.md#L41) | PARTIAL | Continuity check exists, but catalogue/schema/primary/precedence assertions exceed implementation. AUD-014/AUD-015/AUD-016/AUD-017. |
| [Post: Trust/Provenance](plan.md#L42) | PARTIAL | Nominal tier fields and catalogue exist; consistent compatibility and assessor criteria do not. AUD-009/AUD-011/AUD-012. |
| [Post: Privacy/Security](plan.md#L43) | PARTIAL | OpenAPI bearer/403 declarations do not enforce runtime roles. No sensitive-governance policy/approval proof. AUD-001/AUD-007/AUD-025. |
| [Post: Multilingual/Accessibility](plan.md#L44) | PARTIAL | Assessment enum supports recording, but criteria and actual assessor UI checks incomplete. No new alert generation is charged to this spec. AUD-009/AUD-024. |
| [Post: Cloud Platform](plan.md#L45) | PARTIAL | [Cosmos storage/container](../../infra/main.bicep#L701) is concrete; promised governance Redis use and operational regional resilience are not demonstrated. AUD-018/AUD-026. |
| [Post: Quality/Readiness](plan.md#L46) | UNVERIFIED | Test-first instructions, logging source, and numbered SCs do not establish test chronology, execution, monitoring outcomes, or readiness. AUD-023/AUD-024/AUD-027. |

The plan's closing "no constitution violations" statement is not sustainable as an implementation conclusion given the above
application-level gaps. The planned 50-100 catalogue scale versus 46 authored records is recorded as context, not invented as
a new hard minimum; FR-001a/SC-001 define the actual acceptance denominator.

### Research Decisions, Checkpoints, and Rehearsals

| Research decision | Status | Assessment |
| --- | --- | --- |
| [Central Cosmos plus Redis](research.md#L3) | PARTIAL | Cosmos implementation/provisioning exists; local split stores and governance memory cache differ from the chosen architecture. AUD-010/AUD-018. |
| [JSON catalogue](research.md#L13) | IMPLEMENTED | Existing JSON loader and catalogue are used by the import service; execution/SME outcome separate. |
| [Kind/sub-category](research.md#L23) | PARTIAL | Fields/filter comparison present; constrained pairing and UI second-level filtering absent. AUD-011/AUD-020. |
| [Tier maps to rank](research.md#L32) | CONFLICT | Research rejects separate redundant storage, while model stores both and incompletely synchronizes them. AUD-012 resolves compatibility explicitly. |
| [Precedence inheritance](research.md#L41) | PARTIAL | Private hierarchy helper exists; valid unique operational decision contract incomplete. AUD-017. |
| [Grace instead of abrupt block](research.md#L50) | PARTIAL | Helper exists, but actual failed-review derivation contradicts the decision. AUD-003. |
| [Catalogue rather than hardcoded names](research.md#L59) | CONFLICT | Current fixed enum/set and development-actor catalogue do not satisfy the decision. AUD-014. |
| [Discrete per-principle records](research.md#L68) | IMPLEMENTED | Separate assessments and historical supersession are represented and used; concurrency/completeness risks remain AUD-004/AUD-005. |
| [Queryable chain API](research.md#L77) | PARTIAL | Endpoint/structured fields exist; serving resilience/header/eligibility incomplete. Runtime refactoring remains deferred. AUD-018/AUD-021. |
| [Existing monitoring integration](research.md#L86) | PARTIAL | Logging uses app telemetry setup, but required mutation/cache metrics and operational export evidence incomplete. AUD-023. |
| [Foundation ready checkpoint](tasks.md#L44) | PARTIAL | Model/repository/helper artifacts exist; security, atomicity, validation and catalogue assumptions remain open. |
| [US1 fully functional checkpoint](tasks.md#L65) | PARTIAL | CRUD service exists; split state, deactivation and operator UI gaps remain. |
| [US2 complete checkpoint](tasks.md#L89) | PARTIAL | Manual assessment/history exists; ingestion, complete principles, real re-review and automatic grace are not delivered. |
| [US3 complete/<=50ms checkpoint](tasks.md#L113) | PARTIAL; latency UNVERIFIED | Assignment/chain source exists; catalogue, payload, precedence, cache and measured performance claims unsupported. |
| [US4 complete checkpoint](tasks.md#L133) | PARTIAL | Original counters exist, but redirect/replacement does not reflect current governance and E2E assertions are weak. |

All eight quickstart test-first phases are authored instructions, not proof of red/green sequencing or successful execution.
The corresponding test assets were read, including newer dashboard assertions; no run log was inferred from those files.

| Rehearsal in [quickstart](quickstart.md#L129) | Execution status | Source-level limitation / evidence needed |
| --- | --- | --- |
| 1. Seed bootstrap | UNVERIFIED | Import source/test exists; require registry-ID intersection and metadata snapshot in the actual shared instance. AUD-010/AUD-027. |
| 2. Six-principle BoM assessment | UNVERIFIED | Require complete applicable-profile record and rubric version; existing two-principle test is insufficient. AUD-004/AUD-009. |
| 3. Primary plus multi-step chain | UNVERIFIED | Require authenticated UI/API round-trip and payload/primary validation. AUD-001/AUD-015/AUD-020. |
| 4. Shared responsibility | UNVERIFIED | Require both roles/scopes and unambiguous chain behavior after replacement. AUD-016. |
| 5. Rejected social source | UNVERIFIED | Assignment rejection assertion exists; also prove no actual ingestion and documented remediation. AUD-002. |
| 6. Failed-review grace | UNVERIFIED | Helper invocation is not a failed-review transition, notification, or scheduled expiry. AUD-003. |
| 7. Governance-gap identification | UNVERIFIED | Require true current-state dashboard and observed users, not conditional banner assertion. AUD-019/AUD-022/AUD-027. |
| 8. Functional-domain precedence | UNVERIFIED | Private helper test is not public/operational conflict resolution; require eligible unique rules and human-tie outcome. AUD-017. |

### Amendment and Other Review Claims

| Identifier/claim | Status | Evidence assessment and disposition |
| --- | --- | --- |
| ASM-007 | IMPLEMENTED as scope; operating outcome UNVERIFIED | [AU-v1 assumption](spec.md#L207) and D-009 document the baseline/deferred countries; no new-country deployment is requested. AUD-025/AUD-028. |
| ASM-008 | UNVERIFIED | [Named agent consultation](spec.md#L208) is a claim, not an invocation transcript, scoped critique, or human approval. Actor files merely show roles exist. AUD-028. |
| ASM-009 | IMPLEMENTED as reference; conformance PARTIAL | [Taxonomy/schema authority](spec.md#L209) is explicit; HYP linkage and persona approval proof do not meet that authority merely by being referenced. AUD-028. |
| ASM-010 | IMPLEMENTED as documented risk; resolution UNVERIFIED | [AU/Asia tension](spec.md#L210) remains open. [Constitution carve-out](../../.specify/memory/constitution.md#L245) is bounded and is not general authorization for non-AU governance storage or country activation. AUD-025. |
| PER-007 | UNVERIFIED | [Validated label](spec.md#L216) cross-refers broadly to AIIMS roles; no spec-005-scoped practitioner/SME validation record accompanies it. The [persona contract](../027-spec-hardening/contracts/persona-profile.md#L7) requires more than a label/proxy. AUD-028. |
| PER-008 | UNVERIFIED | [Technical-actor reference](spec.md#L217) establishes catalogue roles, not validation of governance-lead/safety-lead/architect workflow usability. AUD-014/AUD-027/AUD-028. |
| PER-009 | IMPLEMENTED as placeholder | [Non-AU placeholder and prerequisites](spec.md#L218) are explicit; no SME-approved PH/JP/BD persona is claimed here. Retain the gate. AUD-025/AUD-028. |
| HYP-003 | MISSING referenced artifact; outcome UNVERIFIED | [Claim](spec.md#L224) points to absent malformed filename. [Portfolio baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L3) and [postfeature](../028-capstone-alignment/evidence/rubric-postfeature.md#L1) do not measure this spec's consultation-controlled uplift. AUD-028. |
| SCP-009 | IMPLEMENTED as deferral | [Three promotion preconditions](spec.md#L230) remain requirements, not approvals. No new-country implementation gap is invented. AUD-025/AUD-028. |
| SCP-010 | IMPLEMENTED as boundary | [Constitution ownership](spec.md#L231) is respected: mapping/criteria remediation must obtain the proper decision, not amend supremacy by inference. AUD-009/AUD-025. |
| SCP-011 | IMPLEMENTED as boundary; arbitration outcome UNVERIFIED | [Product-owner/speckit and spec-018/spec-008 authority](spec.md#L232) are documented; this report does not claim those negotiations occurred or require unrelated warning/recovery changes. |
| Feature-028 authoring/sign-off | UNVERIFIED for this feature's execution/approval | [Decision](../028-capstone-alignment/evidence/decision-record.md#L9) says documentation-only; [sign-off section](../028-capstone-alignment/evidence/decision-record.md#L38) names authoring scripts/structural checks, not governance runtime execution or named SME review for 005. AUD-028. |
| Portfolio +2 rubric-band assertion | UNVERIFIED as HYP-003 evidence | [Snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L39) reports a portfolio structural uplift, not the specified per-feature causal consultation comparison. It cannot close HYP-003 or SC-001 through SC-006 here. AUD-028. |
| RISK-NEW-013 treatment/review date | UNVERIFIED | [Risk record](../../docs/risk-register/RISK-NEW-013.md#L8) names tests/schema compatibility and a scheduled 2026-08-11 review. A treatment description or past scheduled date does not prove execution, mitigation effectiveness, or completed review. AUD-011/AUD-012/AUD-024/AUD-028. |

## Document-Only Validation Gate

Immediately after the first report write, validate this document against original input text: exactly one task-table row per
original ID, preserved checkbox states, all 38 requirement rows, all 15 scenario rows and six edge rows, valid status vocabulary,
28 unique unchecked AUD definitions with resolvable references, existing relative evidence targets with valid 1-based line anchors,
and exactly one final newline. Request editor diagnostics for this Markdown file only and repair document defects only.
The final audit response records the actual check outcomes. None of these document checks establishes a product-test, runtime,

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 005 only. Parallel technical reviews examined governance
authorization/eligibility, constitutional and repository invariants, and dashboard/evidence surfaces. The focused
governance contract suites pass (`27 passed`), but the highest-priority source findings remain open and require a
shared authenticated-principal design rather than a local compatibility patch.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| Existing registry/assessment/assignment contracts | Source and focused contract baseline pass. | `python -m pytest tests/contract/test_data_source_registry.py tests/contract/test_governance_assignment.py tests/contract/test_constitutional_compliance.py -q` returned `27 passed`. This does not prove route auth, Cosmos durability, or deployment behavior. |
| AUD-001 / AUD-002 | Open P0. | Governance/data-source routers still derive authorization from editable `X-User-Role` or `api-user`; ingestion eligibility is not enforced at signal/poll entrypoints. A safe fix needs the repository auth principal contract and coordinated negative tests. |
| AUD-003–AUD-018 | Open P1 design/runtime work. | Grace lifecycle, complete applicable-principle derivation, atomic/ETag transitions, immutable replayable audit, tenant policy, re-review state, catalogue validation, chain payload compatibility, precedence, cache fallback, and dashboard live composition remain source gaps identified by the report. |
| AUD-019–AUD-028 | Partial or evidence-gated. | UI/observability/contract alignment and legal, performance, failover, SME, readiness, and reconstructive audit evidence remain unverified; no external or live environment proof was created. |

No product or infrastructure edits were made in this pass. The passing contract baseline is retained, but no P0/P1
governance item is marked complete without authenticated route tests and an explicit owner-approved transition design.
