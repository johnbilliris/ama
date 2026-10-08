# Phase 4 Final Requirements Quality Checklist: Extension List

**Purpose**: Final reviewer gate for the live manually owned plan, privacy-safe 123-task graph, strict current schemas, traceability, and repository evidence boundaries
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates the quality of the written requirements and design. It does not claim that implementation, pull-request gates, external Azure validation, named review, or the human study have occurred.

## Requirement Completeness

- [x] CHK001 Are all 40 functional requirements and all 7 success criteria present with unique, contiguous identifiers? [Completeness, Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK002 Are installed, available, and combined views defined for both entry points and output modes, including no-root and scope-specific empty outcomes? [Completeness, Spec FR-001-FR-004/FR-015/FR-028/FR-038, Tasks T023-T044/T055-T069]
- [x] CHK003 Are activation, metadata health, independent diagnostics, fallback identity, source evidence, coalescence, and conflict requirements complete for every installed-row class? [Completeness, Spec FR-005-FR-014/FR-020/FR-025/FR-027, Tasks T028/T037-T054]
- [x] CHK004 Are catalog requirements complete for configuration validation, source limits, one total deadline, HTTPS redirects, decoded-size bounds, spawned supervision, complete validation, deterministic reconciliation, cleanup, and atomic fallback? [Completeness, Spec FR-016-FR-017/FR-019/FR-021-FR-026/FR-032, Tasks T055-T069]
- [x] CHK005 Are package isolation, root coexistence, protected-state preservation, ephemeral baseline custody, gate ownership, and final execution boundaries all documented? [Completeness, Spec FR-029/FR-033-FR-034/FR-039-FR-040, Plan Repository Safety And CI, Tasks T001-T022/T070-T089/T117-T123]
- [x] CHK006 Are the seven current schemas and two planned ephemeral-only schemas explicitly named and assigned distinct responsibilities? [Completeness, Plan Evidence And Privacy, Tasks T079-T085/T118/T122]
- [x] CHK007 Are sovereign external requirements complete for exactly one standalone Windows x64 VM and one standalone Ubuntu Linux x64 VM in an allowed Australian region, followed by AU-side finalization and named review? [Completeness, Spec FR-035-FR-037, Plan Sovereign External Platform Validation, Tasks T101-T108/T116/T122]
- [x] CHK008 Are human-study requirements complete for Privacy Act notice, consent, purpose limitation, random pseudonyms, separated recruitment/re-identification records, prohibited PII, generic accommodations, AU storage, least privilege, audit, encryption, 90-day deletion/legal hold, withdrawal, and incident handling? [Completeness, Spec FR-030/FR-036/SC-001/SC-006, Plan Human Study, Tasks T090-T100/T115-T116]

## Requirement Clarity

- [x] CHK009 Is the two-exception bootstrap boundary unambiguous, including order and the point after which canonical guarding or internally protected modes are mandatory? [Clarity, Spec Cross-Cutting Phase 3 Refinements, Plan Repository Safety And CI, Tasks Execution Rule/T003/T006]
- [x] CHK010 Is the universal sanitizer contract explicit about external-temp capture, allowed minimized fields, forbidden values, bounded summaries, and secure deletion? [Clarity, Spec Cross-Cutting Phase 3 Refinements, Plan Repository Safety And CI, Tasks T004-T006/T008/T122]
- [x] CHK011 Is every expected-red command paired with a literal byte-identical green command, including the combined and cross-phase pairs? [Clarity, Spec FR-039, Tasks Command Pairing Rule/Dependencies and Execution Order]
- [x] CHK012 Is same-source normalization defined before stable-ID grouping, with same-ID coalescence, contradictory-ID invalidation, and distinct-source duplicate conflicts clearly distinguished? [Clarity, Spec FR-013/FR-025, Plan Installed Inventory, Tasks T046/T051-T052]
- [x] CHK013 Is catalog preference unambiguously independent of source order through priority, case-folded name, raw name, canonical JSON, and ordinal only for byte-identical ties? [Clarity, Spec FR-026, Plan Catalog Collection, Tasks T058/T067]
- [x] CHK014 Are human and JSON usage errors assigned exact, non-overlapping stream, newline, help-precedence, and exit-status contracts? [Clarity, Spec FR-028, Plan Output Contract, Tasks T029/T035/T059]
- [x] CHK015 Is external pre-write authorization defined as a fail-closed sequence covering ARM AU region and network settings, approved private endpoint, Blob host/private DNS, exact container RBAC, VM identity, and current named attestation before any Blob operation? [Clarity, Spec FR-035/Cross-Cutting Phase 3 Refinements, Plan Sovereign External Platform Validation, Tasks T105-T108]
- [x] CHK016 Is external status unambiguously prose-only and `pending-external`, with no repository object representing completion, failure, or current local substitution? [Clarity, Spec FR-037, Plan Evidence And Privacy, Tasks External Truth Rule/T099-T100/T116/T122]

## Requirement Consistency

- [x] CHK017 Do the specification, plan, and tasks consistently prohibit repository runtime, red, baseline, read-only, performance, and external-status payloads while allowing only source, strict schemas, synthetic fixtures, tests, and prose? [Consistency, Spec FR-033/FR-037/Cross-Cutting Phase 3 Refinements, Plan Summary/Evidence And Privacy, Tasks Evidence Rule]
- [x] CHK018 Do the plan and task graph consistently preserve the existing sovereign `specify-cli-quality` job scope, root tool ownership, output isolation, strict contracts, extension behavior, and text oracle? [Consistency, Spec FR-018/FR-029/FR-034, Plan Repository Safety And CI, Tasks T007-T010/T039/T070-T076/T117-T122]
- [x] CHK019 Do schema-shape requirements consistently defer computed allocation, aggregate, performance, digest, and hosted-lifecycle invariants to post-schema semantic validators? [Consistency, Spec FR-030/FR-035/FR-039, Plan Evidence And Privacy, Tasks T086-T104]
- [x] CHK020 Do external lifecycle requirements consistently require conditional fragment/final writes, exact Windows/Ubuntu cardinality, shared session/package/lock/script identity, and approved-or-rejected named review only in the AU store? [Consistency, Spec FR-035-FR-037, Plan Sovereign External Platform Validation, Tasks T101-T108]
- [x] CHK021 Do privacy requirements consistently separate lifecycle completion from SC-001/SC-006 threshold passage and permit valid failed-study evidence? [Consistency, Spec FR-030/FR-036-FR-037, Plan Human Study, Tasks T093-T100]
- [x] CHK022 Do baseline attribution, package gates, final local success, pull-request readiness, and external success remain separate states with no state waiving another? [Consistency, Spec FR-034/FR-037/FR-040, Plan Constitution Check/Implementation Phases, Tasks T015/T117-T123]

## Acceptance Criteria Quality

- [x] CHK023 Can row identity, activation, health, evidence, conflict, permission, and deterministic-order requirements be objectively assessed from the closed projection contract and semantic rules? [Measurability, Spec FR-005-FR-014/FR-019-FR-027, Extension List Schema, Tasks T028/T038-T069]
- [x] CHK024 Can catalog safety and degradation outcomes be objectively assessed from exact source, record, byte, redirect, time, validation, supervision, and cleanup limits? [Measurability, Spec FR-016-FR-017/FR-021-FR-023/FR-032, Catalog Schemas, Tasks T055-T069]
- [x] CHK025 Can SC-002 be recomputed from exactly 3 warmups, 30 durations, one-based rank 29, a 2.000-second threshold, exact P95 equality, and exact pass-flag equality? [Measurability, Spec FR-039/SC-002, Plan Local Validation, Tasks T070/T084/T086-T089/T111-T114]
- [x] CHK026 Can usability eligibility, deterministic allocation, accommodation/replacement handling, aggregates, SC-001, and SC-006 be recomputed from specified closed fields and algorithms? [Measurability, Spec FR-030/SC-001/SC-006, Usability Evidence Schema, Tasks T090-T100]
- [x] CHK027 Can sovereign eligibility and publication be assessed from exact VM resource grammar, IMDS evidence, AU controls, container scope, private networking, attestation, digest, conditional writes, and named decision? [Measurability, Spec FR-035, Platform Evidence Schema, Tasks T101-T108]

## Scenario And Edge-Case Coverage

- [x] CHK028 Are primary, alternate, exception, and recovery requirements documented for all views, malformed observations, identity conflicts, catalog degradation, CLI misuse, and runtime failure? [Coverage, Spec User Stories 1-3/Edge Cases/FR-001-FR-028, Tasks T023-T069]
- [x] CHK029 Are dirty-worktree scenarios documented for staged, unstaged, untracked, absent optional, post-edit workflow baseline, exact equality, custody loss, and mismatch without remediation? [Coverage, Spec FR-033-FR-034, Plan Repository Safety And CI, Tasks T001-T015/T117-T122]
- [x] CHK030 Are privacy exception and recovery scenarios documented for unavailable accommodations, pre-exposure interruption, post-exposure retention, withdrawal timing, legal hold, and security incidents? [Coverage, Spec FR-030/FR-036/SC-001/SC-006, Plan Human Study, Tasks T090-T100]
- [x] CHK031 Are external failure scenarios documented for wrong region, public networking, non-deny defaults, unapproved endpoints, public DNS, host mismatch, VMSS, broader roles, stale/invalid attestation, duplicate writes, digest mismatch, and rejected review? [Coverage, Spec FR-035, Plan Sovereign External Platform Validation, Tasks T101-T108]
- [x] CHK032 Are no-persistence scenarios documented for unverified workstation authorization, schema failure, semantic failure, external-temp deletion, and minimized terminal-only outcomes? [Coverage, Spec FR-033/FR-037/FR-039, Plan Local Validation, Tasks T077-T089/T109-T114/T122]

## Non-Functional Requirements

- [x] CHK033 Are accessibility requirements objectively bounded by exact terminal sizes, literal labels/states, no ANSI, stable token order, and no pager/input rather than a vague comprehension claim? [Clarity, Measurability, Spec FR-018/SC-007, Tasks T039-T044/T115]
- [x] CHK034 Are security and privacy requirements specified for least privilege, managed identity, no credentials/SAS, private transport, encryption, audit, retention, deletion, and value-free output? [Completeness, Security, Spec FR-035-FR-037, Plan Evidence And Privacy, Tasks T090/T105-T108/T116]
- [x] CHK035 Are performance requirements bounded to installed-only network-disabled execution with deterministic fixture identity/count and reproducible machine/runtime metadata? [Completeness, Performance, Spec FR-031/SC-002, Plan Technical Context/Local Validation, Tasks T070/T086-T089/T111-T114]
- [x] CHK036 Are reliability requirements explicit for fail-closed catalog handling, process cleanup, protected-state mismatch, baseline custody loss, schema/semantic failure, and external pre-write denial? [Coverage, Reliability, Spec FR-016-FR-017/FR-021-FR-023/FR-032-FR-035/FR-039, Tasks T011-T015/T055-T069/T101-T114]

## Dependencies, Traceability, And Blockers

- [x] CHK037 Are external dependencies and exclusion boundaries explicit for pre-provisioned AU VMs/storage/networking/identity/RBAC, reviewer, participant cohort, no infrastructure provisioning, and no local real execution? [Dependency, Assumption, Spec Dependencies/Out of Scope/FR-035-FR-037, Plan Constitution Check, Tasks External Truth Rule/T105-T108/T116/T122]
- [x] CHK038 Does the regenerated graph contain exactly 123 unique contiguous task definitions, bounded parallel groups, explicit phase dependencies, and traceability from guard bootstrap through final local disposition? [Traceability, Tasks T001-T123/Dependencies and Execution Order]
- [x] CHK039 Does T021 state the complete canonical guarded lock-generation command rather than only the child `uv sync --project tools/specify-cli --extra dev` command? [Clarity, Spec Cross-Cutting Phase 3 Refinements, Tasks Execution Rule/T021]
- [x] CHK040 Does T022 state the complete canonical guarded lock-fidelity command rather than only the child `uv sync --project tools/specify-cli --extra dev --locked` command? [Clarity, Spec Cross-Cutting Phase 3 Refinements, Tasks Execution Rule/T022]

## Notes

- Checked: 40; unchecked: 0; blockers: none; total: 40.
- Strict AJV 8 Draft 2020-12 compilation succeeded for all seven current schemas with strict mode enabled and zero diagnostics.
- VS Code reports zero Markdown or JSON diagnostics in the feature directory.
- Static structure validation found 123 unique contiguous task IDs (`T001`-`T123`), 16 literal red/green command pairs with zero mismatches, and zero tasks that write forbidden runtime-evidence payloads into the repository.
- T002 is not a guard blocker because it specifies an internal Git operation implemented by the protection module; T015 and T122 are explicitly internally protected dispatcher-owned modes.
- T021 now states the complete canonical guarded lock-generation command `python scripts/spec001/run_local_gates.py --env SPEC001_TEST_MODE=synthetic -- uv sync --project tools/specify-cli --extra dev`.
- T022 now states the complete canonical guarded lock-fidelity command `python scripts/spec001/run_local_gates.py --env SPEC001_TEST_MODE=synthetic -- uv sync --project tools/specify-cli --extra dev --locked`.
- Final disposition: the live manually owned plan and 123-task graph are requirements-quality ready, with no remaining Phase 4 checklist blocker.
- Earlier Phase 4 checklist files retain historical task counts and references; this checklist is the final disposition for the live 123-task graph and does not treat those historical files as current evidence.
- Real VM runs, AU Blob writes, named review, pull-request results, and the 20-person study remain external pending work and are not requirements-quality blockers.
