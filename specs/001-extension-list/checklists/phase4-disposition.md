# Phase 4 Final Disposition Checklist: Extension List

**Purpose**: Final requirements-quality disposition against the regenerated 106-task graph and the seven current JSON Schema contracts
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates whether the requirements and planning artifacts are complete, clear, consistent, measurable, and traceable. It does not claim that implementation tasks or external validation have been executed.

## Requirement Completeness

- [x] CHK001 Are all 40 functional requirements and all 7 success criteria present with stable sequential identifiers? [Completeness, Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK002 Are the installed, available, and combined scopes specified for both entry points and both output modes, including no-root and empty-state outcomes? [Completeness, Spec FR-001-FR-004/FR-015/FR-028/FR-038, Tasks T023/T029/T033/T050/T060]
- [x] CHK003 Are activation state, metadata health, independent diagnostics, fallback identity, retained evidence, and conflict requirements defined for every installed row class? [Completeness, Spec FR-005-FR-010/FR-013/FR-020/FR-024-FR-027, Extension List Schema]
- [x] CHK004 Are bounded catalog retrieval, complete validation, atomic failure, timeout supervision, and cleanup requirements documented for local and remote sources? [Completeness, Spec FR-016-FR-017/FR-021-FR-023/FR-032, Tasks T046-T057]
- [x] CHK005 Are package isolation, exact root ownership, guard-first execution, dirty-state preservation, baseline comparison, and final-gate separation all specified? [Completeness, Spec FR-029/FR-033-FR-034/FR-039-FR-040, Tasks T001-T016/T062-T069/T092/T099/T102-T106]
- [x] CHK006 Are sovereign external requirements complete for exactly one Windows x64 and one Ubuntu Linux x64 standalone Azure VM run in an allowed Australian region? [Completeness, Spec FR-035, Plan External Handoff Boundary, Tasks T072/T085-T095]
- [x] CHK007 Are deterministic usability eligibility, strata, allocation, accommodations, exclusions, replacements, retained outcomes, and aggregate requirements complete? [Completeness, Spec FR-030/FR-036/SC-001/SC-006, Tasks T076-T084]
- [x] CHK008 Are real standalone-VM runs, AU Blob publication, named review, and the real participant study identified as external dependencies rather than local implementation work? [Completeness, Spec Dependencies/FR-035-FR-037, Tasks External Truth Rule/T101/T106]

## Requirement Clarity

- [x] CHK009 Is same-source normalization explicitly performed before stable-ID grouping, with same-ID coalescence and contradictory-ID invalidation distinguished from distinct-source duplicate conflicts? [Clarity, Spec FR-013/FR-025, Research Decision 3, Tasks T037/T042-T043]
- [x] CHK010 Is catalog preference explicitly order-independent through priority, case-folded catalog name, raw catalog name, canonical JSON, and ordinal only for byte-identical ties? [Clarity, Spec FR-026, Research Decision 7, Tasks T049/T058]
- [x] CHK011 Are human and JSON usage errors assigned exact, non-overlapping stdout, stderr, newline, help-precedence, and exit-status contracts? [Clarity, Spec FR-028, CLI Contract Text Output/JSON Output, Tasks T029/T033/T050]
- [x] CHK012 Is guard-first execution defined with the only two permitted pre-dispatch executions, immediate per-command capture/comparison, and no remediation of dirty state? [Clarity, Spec FR-033/FR-040, Tasks Execution Rule/T001-T005/T104-T106]
- [x] CHK013 Is the platform-record digest defined as SHA-256 over RFC 8785 canonical UTF-8 JSON with only `evidence_digest` omitted? [Clarity, Spec FR-035, Platform Evidence Schema, Tasks T072/T090/T094]
- [x] CHK014 Are review semantics explicit that automated validation proves internal consistency, review occurs in the AU store, and pending-external remains prose-only? [Clarity, Spec FR-035-FR-037, Data Model SovereignExternalPlatformEvidence]
- [x] CHK015 Is deterministic allocation reproducible from the exact algorithm identifier, seed grammar, hash input, participant-ID tie-break, declared variant order, and round-robin assignment? [Clarity, Spec FR-030, Usability Evidence Schema, Tasks T076/T081/T083]
- [x] CHK016 Is merge readiness explicitly stronger than local baseline attribution, requiring actual pull-request lint, unit, and integration jobs to be green? [Clarity, Spec FR-037, Plan Merge Readiness, Tasks T101/T106]

## Requirement Consistency

- [x] CHK017 Do all current artifacts agree on one collect run per standalone AU Azure Windows/Ubuntu VM followed by AU-side finalize with conditional fragment and canonical Blob creation? [Consistency, Spec FR-035, Research Decision 14, Platform Evidence Schema]
- [x] CHK018 Do requirements preserve prose-only pending handoff while completed platform evidence/review remain exclusively in the AU store? [Consistency, Spec FR-035-FR-037, External Validation Status Schema]
- [x] CHK019 Do usability prose, schema constraints, and semantic-validator tasks agree that schema shape alone cannot prove allocation, replacement, accommodation, or aggregate correctness? [Consistency, Spec FR-030/FR-036, Usability Evidence Schema, Tasks T077-T088]
- [x] CHK020 Do identity requirements consistently coalesce same-source same-ID observations, invalidate same-source contradictory IDs, and reserve duplicate-installed conflicts for distinct sources? [Consistency, Spec FR-013/FR-025, Data Model InstalledSourceRecord, Tasks T037/T042-T043]
- [x] CHK021 Do catalog requirements and tasks consistently make preferred-field selection independent of source record order while retaining ordinal as evidence? [Consistency, Spec FR-026, CLI Contract Reconciliation and Tie-breaking, Tasks T049/T058]
- [x] CHK022 Do protected-state equality, root-regression comparison, package gates, and real pull-request readiness remain distinct without one waiving another? [Consistency, Spec FR-033-FR-034/FR-037/FR-040, Tasks T006-T010/T092/T099/T102-T106]
- [x] CHK023 Do the current seven schemas retain distinct responsibilities, with two planned implementation-owned schemas and no local document satisfying sovereign external completion? [Consistency, Plan Project Structure, Tasks T070-T075/T085-T088/T091/T096]

## Acceptance Criteria Quality

- [x] CHK024 Can every row invariant be objectively assessed from closed schema shapes plus the specified semantic rules for identity, activation, health, conflicts, evidence, and permissions? [Measurability, Extension List Schema, Spec FR-005-FR-014/FR-019-FR-027]
- [x] CHK025 Can catalog bounds and failure behavior be assessed from exact limits for sources, records, bytes, redirects, deadlines, validation stages, and cleanup? [Measurability, Spec FR-021-FR-023/FR-032, Catalog Config Schema, Catalog Source Schema]
- [x] CHK026 Can sovereign external eligibility be assessed from standalone resource IDs, exact OS cardinality/proof, IMDS VM/location, outcomes, RFC 8785 digests, and named review? [Measurability, Spec FR-035, Platform Evidence Schema, Tasks T072/T090/T094]
- [x] CHK027 Can usability eligibility and outcomes be independently recomputed from exact participant fields, allocation records, exclusions, replacements, accommodations, and aggregate thresholds? [Measurability, Spec FR-030/SC-001/SC-006, Usability Evidence Schema, Tasks T081/T083-T084]
- [x] CHK028 Can dirty-state preservation and regression attribution be assessed from exact path manifests, external coverage data/rc/XML locations, repository `.coverage*`/`coverage.xml` mutation checks, raw staged/unstaged bytes, normalized sets, and immutable command text? [Measurability, Spec FR-033-FR-034, Tasks T001-T010/T066/T092]
- [x] CHK029 Can merge-readiness reporting distinguish local gate success, pre-existing root failures, new regressions, pending external evidence, and actual pull-request job status? [Measurability, Spec FR-034/FR-037, Plan Merge Readiness, Tasks T099/T101/T106]

## Scenario And Edge-Case Coverage

- [x] CHK030 Are primary, alternate, exception, and recovery requirements present for all scopes, malformed entries, identity conflicts, catalog degradation, CLI misuse, and runtime failure? [Coverage, Spec User Stories 1-3/Edge Cases/FR-001-FR-028, Tasks T027-T061]
- [x] CHK031 Are catalog boundary cases specified for 8/9 sources, 1,000/1,001 records, exact/oversized/growing bodies, redirects, deadline exhaustion, and worker cleanup? [Coverage, Spec FR-021-FR-023/FR-032, Tasks T046-T056]
- [x] CHK032 Are accommodation scenarios defined for fulfilled requests, unavailable required support before exposure, same-stratum replacement, technical interruption, and post-exposure retention? [Coverage, Spec FR-030/SC-001/SC-006, Tasks T076-T084]
- [x] CHK033 Are platform scenarios defined for pending local status, AU-store approved/rejected review, wrong region, VMSS, local substitution, digest mismatch, and invalid platform composition? [Coverage, Spec FR-035-FR-037, Tasks T072/T085-T095]
- [x] CHK034 Are dirty-root scenarios defined for pre-existing staged, unstaged, untracked, absent optional, equal post-state, and mismatch evidence without stash, revert, commit, clean, or repair? [Coverage, Spec FR-033, Tasks T001-T005/T066/T091/T096/T106]

## Dependencies And Assumptions

- [x] CHK035 Are standalone AU VMs, IMDS, private networking, managed identity/RBAC, encrypted retained AU Blob storage, reviewer, and eligible cohort documented as external prerequisites? [Dependency, Spec Dependencies, Tasks External Truth Rule/T101]
- [x] CHK036 Is the distinction between the seven current schemas and the two implementation-owned read-only/performance schemas explicit, including schema-first red/green sequencing? [Dependency, Plan Phase 1 Design Outcome, Tasks T070-T075]
- [x] CHK037 Are repository-only authority, no external checkout, no runner provisioning, no external review or study execution, and no fabricated evidence documented as boundaries? [Assumption, Spec FR-035-FR-039, Tasks Repository Rule/External Truth Rule/T101/T106]

## Traceability And Diagnostics

- [x] CHK038 Does the 106-task graph use unique contiguous IDs, strict task syntax, bounded parallel groups, explicit barriers, and an end-to-end dependency chain from guard bootstrap through final local disposition? [Traceability, Tasks T001-T106/Dependencies and Execution Order]
- [x] CHK039 Is each critical requirement cluster traceable to tests, implementation or producer ownership, evidence validation, and final-gate reporting without assigning external execution to local tasks? [Traceability, Spec FR-001-FR-040/SC-001-SC-007, Tasks T001-T106]
- [x] CHK040 Are diagnostic requirements explicit for metadata invalidity, activation failure, identity conflict, catalog warning, usage error, runtime error, baseline mismatch, schema failure, semantic failure, and rejected review? [Completeness, Spec FR-006/FR-009-FR-010/FR-013/FR-016-FR-017/FR-020/FR-028/FR-034-FR-037, Tasks T037-T050/T085-T088/T102-T106]

## Notes

- Checked: 40; unchecked blockers: 0; total: 40.
- Static validation found 106 unique contiguous task IDs, strict task formatting, all 40 FR and 7 SC identifiers, and seven schemas compiling under strict AJV Draft 2020-12 with unique identifiers, resolved references, and zero strict diagnostics. No VS Code diagnostics remain in the feature directory.
- The two standalone VM collect runs, AU-side finalize/review, actual pull-request lint/unit/integration results, and real 20-person study remain external actions. Their local `pending-external` status is required and is not a requirements-quality blocker.
- Each `/speckit.checklist` run creates a new checklist file; this disposition does not replace the earlier requirements or contract checklists.
