# Rubric-Excellence Checklist: AMA Rubric Improvements

**Purpose**: Validate requirements quality (clarity, completeness, consistency, measurability, coverage) for the 75-item rubric uplift before proceeding to planning.
**Created**: 2026-04-30
**Feature**: [spec.md](../spec.md)

> **What this is**: "Unit tests for English" — each item asks whether the **requirements themselves** are well-written, not whether the code works. Use this in the planning gate; resolve every unchecked item before `/speckit.plan`.

## Requirement Completeness

- [ ] CHK001 - Are decision-rights for every agent (the 6 existing + dependency-notifier) specified in measurable terms? [Completeness, Spec §FR-AG01, FR-AG04]
- [ ] CHK002 - Are kill-switch propagation latency and observability metrics defined for every agent (not just one)? [Completeness, Spec §FR-AG05]
- [ ] CHK003 - Are CMK rotation, key-vault network exposure, and key access-policy requirements specified for the new CMK encryption (FR-S05)? [Completeness, Gap, Spec §FR-S05]
- [ ] CHK004 - Are the OpenTelemetry trace attributes (jurisdiction, incident_id, agent_id, model_version) explicitly enumerated as MUST-be-present? [Completeness, Spec §FR-O07, Gap]
- [ ] CHK005 - Are the per-tier retention durations (audit, operational, security, eval) all individually quantified? [Completeness, Spec §FR-O01]
- [ ] CHK006 - Are RAG citation format, source-confidence threshold, and "no result found" fallback behaviour specified? [Completeness, Spec §FR-AI01, Gap]
- [ ] CHK007 - Are kill-switch + degraded-mode UX requirements defined (operator notice, badge text, alternate workflow)? [Completeness, Spec §FR-AG05, Edge Cases]
- [ ] CHK008 - Are the import-linter rules enumerated beyond "agents MUST NOT import from api" (e.g. domain MUST NOT import from apps)? [Completeness, Spec §FR-Q02, Gap]
- [ ] CHK009 - Is the prompt-library review cadence quantified (e.g. quarterly, per-release)? [Completeness, Spec §FR-AI05]
- [ ] CHK010 - Are sources for the DORA dashboard inputs (workflow_run, deployments, incidents, MTTR computation) specified? [Completeness, Spec §FR-C04]

## Requirement Clarity

- [ ] CHK011 - Is "low-impact connectivity-degraded scenario" quantified (RTT, packet-loss thresholds) for the Field Coordinator path? [Clarity, Edge Cases]
- [ ] CHK012 - Is "dead-letter depth" quantified with specific alert thresholds (count, age) per queue? [Clarity, Spec §FR-O06, FR-O09]
- [ ] CHK013 - Is "consensus event" defined with explicit criteria (number of agents, time window, agreement metric)? [Clarity, Spec §FR-AG09]
- [ ] CHK014 - Is "rolling 30-day window" SLO measurement window aligned with Azure Monitor's evaluation window? [Clarity, Spec §SC-004]
- [ ] CHK015 - Is "AAR coordination gap summary" content schema defined (handoff timeouts, dead-letter cycles, consensus events — what fields)? [Clarity, Spec §FR-AG10]
- [ ] CHK016 - Are the 5 geo-distributed availability test locations explicitly named (e.g. AU-Sydney, AU-Melbourne, NZ-Auckland)? [Clarity, Spec §FR-O10]
- [ ] CHK017 - Is "executive sign-off" for an `--eval-bypass` defined as a specific role + approval mechanism (not free-form)? [Clarity, Edge Cases]
- [ ] CHK018 - Are the binding coverage targets explicit about whether `tests/simulation/`, `tests/devops/`, `tests/benchmark/` are in or out of the measurement? [Clarity, Spec §FR-T01]
- [ ] CHK019 - Is "supersede ADR-031" defined as a workflow (status transitions, link in new ADR, deprecation note in old)? [Clarity, Spec §FR-S02a]
- [ ] CHK020 - Are "structured-output validation" failure semantics defined (raise, fallback to template, both)? [Clarity, Spec §FR-AI04]

## Requirement Consistency

- [ ] CHK021 - Are FR-T05 (nightly load tests) and FR-R02 (nightly load tests) deduplicated to a single binding requirement and reflected once in tasks? [Consistency, Spec §FR-T05/FR-R02]
- [ ] CHK022 - Are FR-S01 (private Cosmos production) and FR-C05 (replace 0.0.0.0 rule) deduplicated? [Consistency, Spec §FR-S01/FR-C05]
- [ ] CHK023 - Are autonomy-dial defaults (`dev=high`) consistent with the kill-switch defaults (everywhere off, opt-in)? [Consistency, Spec §FR-AG02, FR-AG05]
- [ ] CHK024 - Is the OIDC migration two-stage rollout consistent with FR-C03 (SHA-pinned actions) — i.e. SHA-pinning happens regardless of which auth model is active? [Consistency, Spec §FR-S02b/FR-C03]
- [ ] CHK025 - Are the Phi shadow path retention (7 years) consistent with `MetricDefinition` retention in the metrics catalogue? [Consistency, Spec §FR-AI03/FR-O02]
- [ ] CHK026 - Is the RAG index Australia-East-only consistent with the constitution carve-out (model-hosting endpoints exempt; index data is NOT model hosting)? [Consistency, Spec §FR-AI01, Constitution §Non-Negotiable 2]
- [ ] CHK027 - Is the SC-001 "rubric Excellent on every dimension" consistent with the FR coverage (every rubric item has an FR)? [Consistency, Spec §SC-001]
- [ ] CHK028 - Are FR-AI06 (Azure OpenAI Private Endpoint) and the Constitution Non-Negotiable #2 carve-out consistent (i.e. Private Endpoint is the AU path; carve-out is for non-AU model availability only)? [Consistency, Constitution §Non-Negotiable 2]
- [ ] CHK029 - Are FR-S03 (CodeQL) language scopes consistent with the actual languages in the repo (Python, TypeScript, Bicep — and PowerShell?)? [Consistency, Spec §FR-S03]
- [ ] CHK030 - Are workbook templates (FR-O04) and runbook workbooks (FR-O08) deduplicated or clearly scoped? [Consistency, Spec §FR-O04/FR-O08]

## Acceptance Criteria Quality

- [ ] CHK031 - Can SC-002 ("auditor opens 'why fired' panel < 30 seconds") be objectively measured (which clock starts/stops)? [Measurability, Spec §SC-002]
- [ ] CHK032 - Can SC-003 ("100% of probes refuse public-network connections") be objectively measured (probe count, frequency, source IPs)? [Measurability, Spec §SC-003]
- [ ] CHK033 - Are SC-004 SLOs (≥99.9% dashboard availability, ≥99.5% handoff success) tied to specific Azure Monitor metric IDs? [Measurability, Spec §SC-004]
- [ ] CHK034 - Are the eval-baseline thresholds in SC-005 published numerically (not just "meet baselines")? [Measurability, Spec §SC-005]
- [ ] CHK035 - Is SC-007 ("under 60 seconds, zero broken links") testable with an automated link-checker plus reviewer time-trial? [Measurability, Spec §SC-007]
- [ ] CHK036 - Is SC-009 (MTTD < 5 min, MTTP < 2 min) measured against which alert types and how is "detect" defined? [Measurability, Spec §SC-009]
- [ ] CHK037 - Are User Story 1 acceptance scenarios verifiable without examining implementation details? [Measurability, Spec §US1]
- [ ] CHK038 - Are User Story 2 "100% of probes" scenarios time-boxed (over what window)? [Measurability, Spec §US2]
- [ ] CHK039 - Is the User Story 5 consensus-event acceptance scenario verifiable from the audit timeline alone? [Measurability, Spec §US5]
- [ ] CHK040 - Are the User Story 6 RTO/MTTR thresholds measurable from a single drill artifact? [Measurability, Spec §US6]

## Scenario Coverage

- [ ] CHK041 - Are recovery flows defined for OIDC migration failure mid-rollout (FR-S02b)? [Coverage, Recovery Flow, Spec §FR-S02b, Edge Cases]
- [ ] CHK042 - Are partial-failure flows defined for RAG index unavailability (Azure AI Search outage)? [Coverage, Exception Flow, Spec §FR-AI01]
- [ ] CHK043 - Are exception flows defined for cosign-verify failure on prompt artifacts (block deploy vs degrade)? [Coverage, Exception Flow, Spec §FR-AI09]
- [ ] CHK044 - Are non-functional load scenarios defined for the new Workbook tile load (e.g. 100 operators viewing simultaneously)? [Coverage, NFR, Gap]
- [ ] CHK045 - Are the rollback flows for a failed Australia Southeast failover (during a real incident) defined? [Coverage, Recovery Flow, Edge Cases]
- [ ] CHK046 - Are alternate flows defined for synthetic monitoring false positives (paging suppression, retry policy)? [Coverage, Spec §FR-O10]
- [ ] CHK047 - Are exception flows defined for autonomy-dial misconfiguration (jurisdiction policy missing or invalid)? [Coverage, Spec §FR-AG02]
- [ ] CHK048 - Are recovery flows defined for kill-switch propagation lag exceeding 30 s? [Coverage, Spec §FR-AG05]
- [ ] CHK049 - Are exception flows defined for an integrity-check failure on the audit ledger (FR-AG07 / US1)? [Coverage, Spec §US1]
- [ ] CHK050 - Are scenarios defined for the Phi shadow path producing significantly different output (drift detection)? [Coverage, Spec §FR-AI03]

## Edge Case Coverage

- [ ] CHK051 - Is the "language fallback" edge case requirement explicit about the order of language preference (priority list)? [Edge Cases, Spec §Edge Cases]
- [ ] CHK052 - Is the "kill-switch engaged during high-severity incident" edge case requirement explicit about audit-log severity tagging? [Edge Cases]
- [ ] CHK053 - Is the "CodeQL false positive on emergency hotfix" bypass requirement explicit about timeout (must be revoked within X hours)? [Edge Cases]
- [ ] CHK054 - Is the "Azure OpenAI Private Endpoint outage" requirement explicit about the SLI it impacts (alert-to-publish time)? [Edge Cases]
- [ ] CHK055 - Are degraded-mode response-time guarantees specified relative to normal-mode SLOs? [Edge Cases, Gap]

## Non-Functional Requirements

- [ ] CHK056 - Are accessibility requirements (WCAG 2.2 AA) specified for the new Workbooks and the hosted API docs? [NFR, Accessibility, Spec §FR-O04, FR-DOC02, Gap]
- [ ] CHK057 - Are localisation requirements specified for the consolidated docs hub (en-AU, plus messages requiring CALD/ATSI translation)? [NFR, Spec §FR-DOC03, Gap]
- [ ] CHK058 - Are performance requirements specified for the new RAG path (retrieval latency added to total recommendation latency)? [NFR, Spec §FR-AI01, Gap]
- [ ] CHK059 - Are security requirements specified for the prompt library access (who can edit, sign, and deploy)? [NFR, Security, Spec §FR-AI05]
- [ ] CHK060 - Are availability requirements for the Workbooks and metric pipelines specified (separate from app SLOs)? [NFR, Spec §FR-O04, FR-O08]

## Dependencies & Assumptions

- [ ] CHK061 - Are the assumed Azure quota commitments for the new resources (AI Search S1, Chaos Studio targets, Sentinel data ingestion) explicit? [Dependency, Gap]
- [ ] CHK062 - Are the assumed third-party service licences (Loom or equivalent for FR-DOC01) documented? [Dependency, Spec §FR-DOC01]
- [ ] CHK063 - Are the assumptions about spec 030's eval framework readiness for FR-AI04, FR-T09 explicit (which spec-030 deliverables must land first)? [Dependency, Spec §FR-AI04, FR-T09]
- [ ] CHK064 - Are the assumptions about spec 031 landing first (FR-C01) explicit in the dependency graph? [Dependency, Spec §FR-C01]
- [ ] CHK065 - Are the assumptions about Entra group ID resolution (FR-I05) explicit about who provides the IDs? [Dependency, Spec §FR-I05]

## Ambiguities & Conflicts

- [ ] CHK066 - Does the spec resolve the apparent conflict between FR-AI03 (Phi shadow stored 7y) and constitution Non-Negotiable #2 carve-out (no regulated data outside AU) when Phi is a non-AU endpoint? [Conflict, Constitution §Non-Negotiable 2]
- [ ] CHK067 - Does the spec resolve which deliverable owns the "metrics catalogue" — observability (FR-O02) or AI evaluation framework (spec 030)? [Ambiguity, Spec §FR-O02]
- [ ] CHK068 - Does the spec resolve which workbook category (operator runbooks vs governance) owns the "executive governance health score" tile? [Ambiguity, Spec §FR-O04, FR-O08]
- [ ] CHK069 - Does the spec resolve whether the "consolidate three doc hubs" (FR-DOC03) is a redirect/single nav, a physical move, or both? [Ambiguity, Spec §FR-DOC03]
- [ ] CHK070 - Does the spec resolve whether import-linter (FR-Q02) is a contract or a new dependency to add to `pyproject.toml`? [Ambiguity, Spec §FR-Q02]

## Traceability

- [ ] CHK071 - Is every Rubric improvement item (1.1 through 17.5) traceable to at least one FR in this spec? [Traceability, Spec §All FRs]
- [ ] CHK072 - Is every FR traceable to at least one acceptance scenario across User Stories 1–8? [Traceability]
- [ ] CHK073 - Is every Success Criterion (SC-001..SC-010) traceable to at least one FR? [Traceability]
- [ ] CHK074 - Is the requirement→test traceability matrix (FR-T07) committed for THIS spec (032), not just future specs? [Traceability, Spec §FR-T07]
- [ ] CHK075 - Are the ADR commitments (ADR-032 supersession, circuit-breaker library choice, OIDC re-introduction) listed in a dependency graph? [Traceability, Spec §FR-S02a, FR-P03]

## Notes

- 75 checklist items mirror the 75 rubric improvements for one-to-one traceability.
- Every unchecked item must be either resolved by spec edits or explicitly accepted as out-of-scope before `/speckit.plan` proceeds.
- Items found OK during planning may be checked off in this file (the planning agent owns that pass).
