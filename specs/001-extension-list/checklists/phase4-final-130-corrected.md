# Phase 4 Final Corrected Requirements Quality Checklist: Extension List

**Purpose**: Final reviewer disposition for the corrected live plan, 130-task graph, seven current schemas, privacy boundaries, and execution custody requirements
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates whether the written requirements and planning artifacts are complete, clear, consistent, measurable, and traceable. It does not claim implementation, pull-request gates, external Azure validation, named review, or the human study have occurred.

## Requirement Completeness

- [x] CHK001 Are all 40 functional requirements and all 7 success criteria present with unique contiguous identifiers? [Completeness, Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK002 Are installed, available, and combined views defined for both entry points and both output modes, including no-root and scope-specific empty outcomes? [Completeness, Spec FR-001-FR-004/FR-015/FR-028/FR-038, Tasks T024-T070]
- [x] CHK003 Are activation, metadata health, diagnostics, fallback identity, source evidence, coalescence, and conflict requirements complete for every installed-row class? [Completeness, Spec FR-005-FR-014/FR-020/FR-025/FR-027, Tasks T029/T038-T055]
- [x] CHK004 Are catalog requirements complete for schema-first configuration, duplicate-name rejection before access, limits, one deadline, HTTPS redirects, decoded-size bounds, spawned supervision, cleanup, and atomic fallback? [Completeness, Spec FR-016-FR-017/FR-019/FR-021-FR-026/FR-032, Tasks T056-T070]
- [x] CHK005 Are package isolation, root coexistence, protected-state preservation, ephemeral baseline custody, gate ownership, and final execution boundaries documented? [Completeness, Spec FR-029/FR-033-FR-034/FR-039-FR-040, Plan Repository Safety And CI, Tasks T001-T023/T071-T100/T123-T130]
- [x] CHK006 Are the seven current schemas and two planned ephemeral-only schemas named and assigned distinct responsibilities? [Completeness, Plan Evidence And Privacy, Tasks T078-T100/T124/T128]
- [x] CHK007 Are human-study privacy requirements complete for notice, consent, purpose limitation, pseudonym separation, prohibited PII, accommodations, AU storage, least privilege, audit, encryption, retention, deletion, withdrawal, and incidents? [Completeness, Spec FR-030/FR-036/SC-001/SC-006, Plan Human Study, Tasks T101-T111/T122]
- [x] CHK008 Are sovereign external requirements complete for exact standalone Windows and Ubuntu AU VMs, pre-write authorization, AU-side finalization, and named review? [Completeness, Spec FR-035-FR-037, Plan Sovereign External Platform Validation, Tasks T112-T122]

## Requirement Clarity

- [x] CHK009 Is the two-exception bootstrap boundary unambiguous, including order and the point after which session-bound guarding is mandatory? [Clarity, Plan Repository Safety And CI, Tasks Execution Rule/T003/T007-T008]
- [x] CHK010 Is the sanitizer contract explicit about external-temp capture, minimized allowed fields, forbidden values, bounded summaries, and secure deletion? [Clarity, Plan Repository Safety And CI, Tasks Evidence Rule/T004-T007/T010/T128]
- [x] CHK011 Are literal start, guarded-child, and final session commands specified with UUID continuity and token/owner/expiry/root/digest custody checks? [Clarity, Tasks Execution Rule/T004/T006/T008/T128]
- [x] CHK012 Is the unfiltered packaging red/green child command fully stated and byte-identical in both tasks? [Clarity, Spec FR-039, Tasks T018/T021]
- [x] CHK013 Are the usability schema run, conditional schema edit, and identical green replay specified as three separate ordered tasks? [Clarity, Tasks T102-T105]
- [x] CHK014 Is every expected-red command paired with a byte-identical green command, including combined and cross-phase pairs? [Clarity, Tasks Command Pairing Rule/T010-T127]
- [x] CHK015 Is external pre-write authorization a fail-closed sequence covering ARM AU location and network settings, approved private endpoint, Blob host/private DNS, exact container RBAC, VM identity, and current named attestation before Blob access? [Clarity, Spec FR-035, Plan Sovereign External Platform Validation, Tasks T117-T120]
- [x] CHK016 Is external status prose-only and `pending-external`, with no repository object representing completion, failure, or local substitution? [Clarity, Spec FR-037, Plan Evidence And Privacy, Tasks External Truth Rule/T112/T122/T124/T128]

## Requirement Consistency

- [x] CHK017 Do the specification, plan, contracts, and tasks consistently prohibit repository runtime, red, baseline, read-only, performance, and external-status payloads while permitting only source, strict schemas, synthetic fixtures, tests, and prose? [Consistency, Spec FR-033/FR-037, Plan Summary/Evidence And Privacy, Tasks Evidence Rule, CLI Contract Root Regression Contract]
- [x] CHK018 Do schema tasks consistently precede semantic-validator tasks, and do schema plus semantic requirements precede producer red/green tasks? [Consistency, Plan Implementation Phases, Tasks T078-T100]
- [x] CHK019 Do all SC-002 schema, semantic, producer-test, and producer requirements repeat the full machine/runtime, fixture, sample, rank, threshold, and pass-field contract? [Consistency, Spec SC-002, Plan Local Validation, Tasks T080/T083/T093/T097/T099]
- [x] CHK020 Do privacy requirements separate lifecycle completion from SC-001/SC-006 threshold passage and permit valid failed-study evidence? [Consistency, Spec FR-030/FR-036-FR-037, Plan Human Study, Tasks T106-T111]
- [x] CHK021 Do baseline attribution, package gates, final local success, pull-request readiness, and external success remain separate states without one waiving another? [Consistency, Spec FR-034/FR-037/FR-040, Plan Constitution Check/Implementation Phases, Tasks T125-T130]
- [x] CHK022 Is the planned CI wording consistent that the existing workflow receives one sovereign `specify-cli-quality` job with no runtime-evidence upload? [Consistency, Plan Summary/Repository Safety And CI, Tasks T009-T012]
- [x] CHK023 Do the execution rule, T128 definition, Phase 10 dependency section, completion graph, and validation discipline consistently assign finalization to T128 after T125/T127 completes? [Consistency, Tasks Execution Rule/T125-T130/Dependencies and Execution Order/Validation Discipline]

## Acceptance Criteria Quality

- [x] CHK024 Can SC-002 be objectively assessed from exactly 3 warmups, 30 durations, one-based rank 29, a 2.000-second threshold, exact P95 equality, and exact pass-flag equality? [Measurability, Spec SC-002, Plan Local Validation, Tasks T080/T083/T093-T100]
- [x] CHK025 Can dirty-state preservation and session continuity be assessed from exact protected paths, staged/unstaged bytes, digests, root identity, token ownership, expiry, baseline binding, and final invalidation? [Measurability, Spec FR-033-FR-034, Plan Repository Safety And CI, Tasks T001-T016/T128]
- [x] CHK026 Can privacy-safe local evidence handling be assessed from schema then semantic validation, authorization-dependent retention, minimized status, and deletion of every external-temp payload? [Measurability, Spec FR-039, Plan Local Validation, Tasks T082-T100/T124/T128]
- [x] CHK027 Can sovereign eligibility and publication be assessed from exact VM composition, ARM/IMDS evidence, AU controls, container scope, private networking, attestation, digests, conditional writes, and named decision? [Measurability, Spec FR-035, Plan Sovereign External Platform Validation, Tasks T113-T120]

## Scenario Coverage

- [x] CHK028 Are primary, alternate, exception, and recovery requirements documented for all views, malformed observations, identity conflicts, catalog degradation, CLI misuse, and runtime failure? [Coverage, Spec User Stories 1-3/Edge Cases/FR-001-FR-028, Tasks T024-T070]
- [x] CHK029 Are custody failure scenarios documented for missing, expired, mismatched, reconnected, wrong-owner, wrong-root, wrong-digest, and discontinuous sessions? [Coverage, Plan Repository Safety And CI, Tasks T004/T006/T013-T016/T128]
- [x] CHK030 Are privacy exception and recovery scenarios documented for unavailable accommodations, interruption, post-exposure retention, withdrawal timing, legal hold, incidents, schema failure, semantic failure, and unverified workstation authorization? [Coverage, Plan Evidence And Privacy/Human Study, Tasks T085-T111/T128]
- [x] CHK031 Are external denial scenarios documented for wrong region, public networking, non-deny defaults, unapproved endpoints, public DNS, host mismatch, VMSS, broader roles, stale attestation, duplicate writes, digest mismatch, and rejected review? [Coverage, Plan Sovereign External Platform Validation, Tasks T113-T120]

## Dependencies And Assumptions

- [x] CHK032 Does the regenerated graph specify exactly 130 unique contiguous task definitions, bounded parallel groups, explicit phase dependencies, and an end-to-end chain from bootstrap through final checklist disposition? [Traceability, Tasks T001-T130/Dependencies and Execution Order]
- [x] CHK033 Are all 18 canonical red/green or identical replay pairs explicitly traceable with no command-string differences? [Traceability, Tasks T010-T127]
- [x] CHK034 Are repository-only authority, no external checkout, no infrastructure provisioning, no real external execution, no study execution, and no fabricated evidence explicit boundaries? [Dependency, Assumption, Spec FR-035-FR-039, Plan Constitution Check, Tasks External Truth Rule/T117-T122/T128]
- [x] CHK035 Are the seven current contracts explicitly required to use Draft 2020-12, strict closed shapes, and unique non-empty identifiers? [Contract Quality, Plan Evidence And Privacy, Tasks T078-T079]
- [x] CHK036 Is strict-schema compilation defined as a blocking prerequisite before planned-schema and semantic work? [Dependency, Tasks T078-T081, Plan Implementation Phases]
- [x] CHK037 Are real VM runs, AU Blob writes, named review, pull-request results, and participant-study outcomes explicitly identified as later external evidence rather than local readiness claims? [Assumption, Boundary, Spec FR-035-FR-037, Plan Constitution Check/Evidence And Privacy, Tasks External Truth Rule/T122/T128-T130]

## Notes

- Checked: 37; unchecked: 0; blockers: 0; total: 37.
- Live static validation found 130 unique contiguous task IDs (`T001`-`T130`) and 18 literal command pairs with zero mismatches.
- The corrected execution-rule header, T128 task definition, Phase 10 dependency section, completion graph, and validation discipline consistently assign finalization to T128 after the T125/T127 exact pair.
- Disposable external-temp validation installed `ajv@8.20.0` and `ajv-formats@3.0.1`, compiled all seven current contracts with Draft 2020-12 strict settings, produced zero diagnostics, and removed the temporary installation afterward.
- The privacy model remains requirements-consistent: runtime evidence, expected-red output, root baselines, read-only/performance objects, and external-status payloads are prohibited from repository persistence; raw output is external-temp only, minimized, and deleted.
- Real VM runs, AU Blob writes, named review, pull-request results, and the participant study remain external pending work and are not requirements-quality blockers.
- Historical Phase 4 checklist files retain their point-in-time results. This file is the latest disposition for the corrected live 130-task graph.