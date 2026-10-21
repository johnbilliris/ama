# Phase 4 Simplified External Validation Checklist: Extension List

**Purpose**: Reassess requirements quality after simplifying external platform validation to manual standalone AU Azure VM execution and direct sovereign evidence publication
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates whether the written requirements and design are complete, clear, consistent, measurable, and traceable. It does not claim that implementation, external execution, human review, participant study, or pull-request gates have completed.

## Requirement Completeness

- [x] CHK001 Are all 40 functional requirements and all 7 success criteria present with stable sequential identifiers? [Completeness, Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK002 Is external platform validation bounded to one checked-in script with locally tested collect/finalize modes, one later collect run per standalone Azure Windows/Ubuntu VM, and one later AU-side finalize run? [Completeness, Spec FR-035, Research Decision 14]
- [x] CHK003 Are conditional fragment/final publication over TLS/private endpoint to pre-provisioned AU Blob storage, managed identity, container-scoped RBAC, and prohibited GitHub/repository/log destinations all documented? [Completeness, Spec FR-035/Dependencies]
- [x] CHK004 Is repository external status defined for exactly sovereign platform validation and the human study, with both records fixed to `pending-external` and null evidence path/time? [Completeness, Spec FR-037, External Validation Status Schema]
- [x] CHK005 Does the current platform evidence contract cover exactly one Windows and one Ubuntu standalone-VM record, OS-specific proof, command outcomes, digest, and named review? [Completeness, Spec FR-035, Platform Evidence Schema]
- [x] CHK006 Are root pytest coverage outputs fully externalized through `COVERAGE_FILE`, `COVERAGE_RCFILE`, and XML configuration, with repository coverage paths preflight-blocked and mutation-checked? [Completeness, Spec FR-034, Plan Technical Context/Phase 0 Research Outcome]
- [x] CHK007 Are all SC-002 evidence fields explicitly enumerated, including machine/runtime metadata, fixture identity/count, warmups, durations, rank, P95, threshold, result, and timestamp? [Completeness, Spec SC-002, Data Model PerformanceEvidence]
- [x] CHK008 Are SC-001 and SC-006 evidence requirements complete for eligibility, strata, allocation, accommodations, exclusions, replacements, participant outcomes, and derived aggregates? [Completeness, Spec FR-030/SC-001/SC-006, Data Model UsabilityEvidence]
- [x] CHK009 Are the seven current schemas distinguished from the two planned implementation-owned read-only and performance schemas? [Completeness, Plan Project Structure/Phase 1 Design Outcome]

## Requirement Clarity

- [x] CHK010 Is the external trust boundary unambiguous that schema and semantic checks establish consistency while a named reviewer supplies the independent approved/rejected decision in the AU store? [Clarity, Spec FR-035, Data Model SovereignExternalPlatformEvidence]
- [x] CHK011 Is it explicit that the permitted `specify-cli-quality` workflow is PR validation only and that no workflow, repository payload/path, GitHub log, or GitHub artifact may represent external platform completion? [Clarity, Spec FR-034-FR-037]
- [x] CHK012 Is standalone Azure VM eligibility objectively distinguished from VM scale sets through the required `Microsoft.Compute/virtualMachines` resource-ID grammar and IMDS evidence? [Clarity, Spec FR-035, Platform Evidence Schema]
- [x] CHK013 Is catalog version validity unambiguous that a non-null value must be non-empty, while null or omission normalizes to `unknown`? [Clarity, Spec FR-024, Catalog Source Schema]
- [x] CHK014 Is the FR-018/SC-007 text oracle defined by exact 80x24 and 40x12 terminals with colour disabled, redirected text, literal labels/states, no ANSI, stable token order, and no pager/input? [Clarity, Spec FR-018/SC-007]
- [x] CHK015 Are SC-001 success and SC-006 qualification derived from explicit participant fields rather than subjective reviewer interpretation? [Clarity, Spec FR-030/SC-001/SC-006, Data Model UsabilityEvidence]
- [x] CHK016 Is baseline attribution explicitly separated from merge readiness, with actual pull-request lint, unit, and integration jobs required green? [Clarity, Spec FR-037]

## Requirement Consistency

- [x] CHK017 Do the specification, research, data model, quickstart, and current contracts agree that fragments and canonical platform evidence bypass GitHub and are conditionally created in private AU Blob storage? [Consistency, Spec FR-035-FR-037, Research Decision 14, Data Model SovereignExternalPlatformEvidence]
- [x] CHK018 Do all artifacts agree that pending-external remains prose-only and no status JSON is instantiated regardless of completed external records in the AU store? [Consistency, Spec FR-037, Data Model ExternalValidationStatus, External Validation Status Schema]
- [x] CHK019 Do platform requirements and schema agree on Windows/Ubuntu cardinality, x64 architecture, standalone VM identity, allowed Australian regions, OS-specific proof, and named review? [Consistency, Spec FR-035, Platform Evidence Schema]
- [x] CHK020 Do root-regression requirements consistently preserve the exact pytest argument selection while externalizing coverage data, rc, and XML outputs and prohibiting repository cleanup or restoration? [Consistency, Spec FR-033-FR-034, Plan Constitution Check/Phase 0 Research Outcome]
- [x] CHK021 Do usability prose, schema responsibilities, and semantic-validation design agree on exact SC-001 and SC-006 recomputation rules? [Consistency, Spec FR-030/SC-001/SC-006, Data Model UsabilityEvidence]
- [x] CHK022 Do the plan tree and narrative consistently identify seven current schemas and two planned schemas, with no feature workflow or repository platform-evidence file? [Consistency, Plan Project Structure/Phase 1 Design Outcome]
- [x] CHK023 Do prior source coalescence, allocation, tie-break, protected-manifest, root ownership, and merge-readiness decisions remain represented without contradiction? [Consistency, Spec FR-013/FR-026/FR-030/FR-033-FR-037, Research Decisions 3/7/10/12-17]

## Acceptance Criteria Quality

- [x] CHK024 Can external platform eligibility be assessed from closed record fields, exact cardinality, resource-ID grammar, IMDS location, OS proof, command outcomes, RFC 8785 digest, and review decision? [Measurability, Spec FR-035, Platform Evidence Schema]
- [x] CHK025 Can repository pending status be assessed objectively from exact categories, fixed status values, and null evidence path/time? [Measurability, Spec FR-037, External Validation Status Schema]
- [x] CHK026 Can root coverage isolation be assessed from explicit external locations, immutable command arguments, preflight behavior, and repository mutation comparisons? [Measurability, Spec FR-034]
- [x] CHK027 Can SC-002 be independently calculated from the enumerated evidence fields and nearest-rank `rank=29` rule against `threshold_seconds=2.000`? [Measurability, Spec SC-002, Data Model PerformanceEvidence]
- [x] CHK028 Can FR-018/SC-007 be assessed solely from the objective terminal and redirected-text oracle without asserting general human comprehension? [Measurability, Spec FR-018/SC-007]
- [x] CHK029 Can SC-001 and SC-006 be independently recomputed from participant-level answer, timing, rating, and prohibited-action fields plus exact aggregate thresholds? [Measurability, Spec FR-030/SC-001/SC-006, Data Model UsabilityEvidence]

## Scenario And Edge-Case Coverage

- [x] CHK030 Are external scenarios defined for Windows and Ubuntu success, wrong region, VMSS substitution, missing OS proof, digest mismatch, approved/rejected review, unavailable prerequisites, and pending local status? [Coverage, Spec FR-035-FR-037, Platform Evidence Schema]
- [x] CHK031 Are evidence-leakage scenarios addressed for credentials, SAS tokens, command payloads, terminal values, GitHub artifacts/logs, repository files, and non-AU storage? [Coverage, Spec FR-035, Plan Constitution Check]
- [x] CHK032 Are coverage-output scenarios defined for externally isolated data/rc/XML paths, inability to honor isolation, and repository `.coverage*` or `coverage.xml` creation/change? [Coverage, Spec FR-034]
- [x] CHK033 Are usability alternate, exception, and recovery scenarios defined for accommodations, pre-exposure exclusion, same-stratum replacement, technical interruption, and mandatory post-exposure retention? [Coverage, Spec FR-030/SC-001/SC-006]

## Dependencies And Assumptions

- [x] CHK034 Are standalone AU VMs, IMDS, private networking, pre-provisioned Blob storage, managed identities/RBAC, reviewer, and participant cohort explicitly identified as external prerequisites? [Dependency, Spec Dependencies]
- [x] CHK035 Is the absence of external run, review, study, and pull-request evidence represented as pending execution rather than inferred completion or a local design failure? [Assumption, Spec FR-035-FR-037]

## Traceability And Diagnostics

- [x] CHK036 Is each authoritative simplification traceable across the specification and at least one plan, research, data-model, quickstart, contract, or schema statement? [Traceability, Spec FR-018/FR-024/FR-030/FR-034-FR-037/SC-001-SC-002/SC-006-SC-007]
- [x] CHK037 Do all seven current schema files parse and compile as Draft 2020-12 schemas with declared identifiers and root types? [Traceability, Current Contract Set]
- [x] CHK038 Are all seven current schemas free of strict-validator diagnostics so strict schema compilation succeeds without warnings? [Diagnostics, Current Contract Set]
- [x] CHK039 Are all 106 task definitions uniquely and contiguously identified from T001 through T106 without assigning external execution to local implementation? [Traceability, Tasks T001-T106]
- [x] CHK040 Are feature-directory editor diagnostics clear after the requirements and contract review? [Diagnostics]

## Notes

- Checked: 40; unchecked blockers: 0; total: 40.
- Schema validation: 7/7 current schemas parse and compile under strict AJV Draft 2020-12 semantics with seven unique schema identifiers, all references resolved, and zero strict diagnostics.
- Feature diagnostics: no VS Code diagnostics were reported for `specs/001-extension-list`.
- Structural counts: 40 FRs, 7 SCs, 106 unique contiguous task definitions, seven current schemas, and two planned schemas.
- External completion blockers: the two standalone VM runs, AU Blob publication, named AU-store review, real 20-person study, and actual pull-request lint/unit/integration results remain pending external. These are not requirements-quality failures and are intentionally not represented as checked completion claims.
- Each `/speckit.checklist` run creates a new checklist file; this checklist does not replace the prior requirements, contract, or Phase 4 disposition checklists.
