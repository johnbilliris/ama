# Phase 4 Plan Quality Checklist: Extension List

**Purpose**: Evaluate the restored implementation plan and authoritative design artifacts for requirements quality, traceability, strict contract quality, and diagnostic coverage
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates the written requirements and design only. It does not claim that tasks, implementation, CI execution, external Azure validation, review, or the human study have occurred.

## Requirement Completeness

- [x] CHK001 Are all 40 functional requirements and all 7 success criteria present with unique, contiguous identifiers? [Completeness, Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK002 Does the plan define the language, dependencies, storage boundaries, test stack, target platforms, performance goal, constraints, and scale needed to implement the feature? [Completeness, Plan Technical Context]
- [x] CHK003 Are installed, available, and combined views specified across both entry points, both output modes, discovered-root and no-root contexts, and empty results? [Completeness, Spec FR-001-FR-004/FR-015/FR-028/FR-038; Plan Summary/Output Contract]
- [x] CHK004 Are installed-row requirements complete for identity, same-source coalescence, activation, health, diagnostics, capabilities, evidence, and distinct-source conflicts? [Completeness, Spec FR-005-FR-014/FR-020/FR-025/FR-027; Plan Installed Inventory]
- [x] CHK005 Are catalog requirements complete for configuration limits, local and HTTPS retrieval, deadlines, size and record limits, redirects, validation, atomic fallback, cleanup, and deterministic reconciliation? [Completeness, Spec FR-016-FR-017/FR-021-FR-026/FR-032; Plan Catalog Collection]
- [x] CHK006 Are package isolation, protected-state preservation, root regression attribution, external coverage output, and merge-readiness boundaries all documented? [Completeness, Spec FR-029/FR-033-FR-034/FR-037/FR-040; Plan Repository Safety And Root Integration]
- [x] CHK007 Are all seven current schemas and the two planned implementation-owned schemas explicitly distinguished by name and ownership? [Completeness, Plan Evidence And External Validation/Project Structure; Spec FR-039]
- [x] CHK008 Are the external platform and usability lifecycles documented without assigning their real execution, review, or study completion to local implementation? [Completeness, Spec FR-030/FR-035-FR-037; Plan Evidence And External Validation]

## Requirement Clarity

- [x] CHK009 Is the new `specify-cli-quality` job clearly defined as a planned edit to the existing workflow on the sovereign AU self-hosted Linux x64 runner rather than as already-existing evidence? [Clarity, Plan Constitution Check/Repository Safety And Root Integration]
- [x] CHK010 Are the CI job's IMDS location gate, locked sync, Ruff, strict mypy, branch coverage, build, clean install, entry-point smokes, synthetic-fixture restriction, and no-payload/no-artifact boundary explicit? [Clarity, Spec FR-034; Plan Repository Safety And Root Integration]
- [x] CHK011 Is the exact protected manifest stated, including the post-edit workflow baseline and separate raw staged and unstaged Git-diff preservation rules? [Clarity, Spec FR-033; Plan Repository Safety And Root Integration]
- [x] CHK012 Is root coverage isolation explicit about external `COVERAGE_FILE`, external `COVERAGE_RCFILE`, external XML output, unchanged pytest arguments, preflight blocking, and repository coverage-file mutation detection? [Clarity, Spec FR-034; Plan Repository Safety And Root Integration]
- [x] CHK013 Are performance computed fields defined as semantic invariants that require sorted rank-29 P95 recomputation and exact pass-flag equality after schema validation? [Clarity, Spec FR-039/SC-002; Plan Performance Evidence]
- [x] CHK014 Is usability evidence clearly allowed to represent failed SC-001 or SC-006 outcomes, with lifecycle completion separated from threshold passage? [Clarity, Spec FR-030/FR-036/SC-001/SC-006; Plan Usability Evidence]
- [x] CHK015 Are external `collect` and `finalize` responsibilities, inputs, matching rules, conditional writes, canonical output, and review decision boundaries unambiguous? [Clarity, Spec FR-035; Plan Sovereign External Platform Evidence]
- [x] CHK016 Is pending-external unambiguously prose-only with no repository status JSON regardless of external approval, rejection, or study result? [Clarity, Spec FR-036-FR-037; Data Model ExternalValidationStatus]

## Requirement Consistency

- [x] CHK017 Do the plan, specification, research, quickstart, and data model agree that `specify-cli-quality` is PR quality validation and never sovereign platform evidence? [Consistency, Spec FR-034-FR-035; Plan Repository Safety And Root Integration]
- [x] CHK018 Do the authoritative artifacts consistently require unique collect fragments followed by AU-side finalize, canonical validation, named review, and create-if-absent final publication? [Consistency, Spec FR-035; Plan Sovereign External Platform Evidence; Research Decision 14]
- [x] CHK019 Do schema and semantic responsibilities remain consistently separated for performance, usability, catalog-name uniqueness, digests, and hosted lifecycle invariants? [Consistency, Spec FR-030/FR-039; Plan Evidence And External Validation; Data Model]
- [x] CHK020 Do usability requirements consistently permit aggregate values from 0 through 20 while deriving separate 19-of-20 and 18-of-20 pass decisions semantically? [Consistency, Spec FR-030/FR-036/SC-001/SC-006; Plan Usability Evidence]
- [x] CHK021 Do the artifacts consistently keep `pending-external` in specification/handoff/checklists only and prohibit local platform or usability payloads from representing completion? [Consistency, Spec FR-035-FR-037; Data Model ExternalValidationStatus]
- [x] CHK022 Do identity requirements consistently distinguish same-source coalescence, same-source contradictory IDs, distinct-source duplicate IDs, and identifier-less fallback grouping? [Consistency, Spec FR-013/FR-020/FR-025; Plan Installed Inventory; Data Model InstalledSourceRecord]
- [x] CHK023 Do local baseline attribution and actual merge readiness remain distinct, with all real PR jobs required to be green? [Consistency, Spec FR-034/FR-037; Plan Summary/Repository Safety And Root Integration]

## Acceptance Criteria Quality

- [x] CHK024 Are installed-only performance requirements objectively measurable from a named environment, fixture count, warmups, sample count, rank, threshold, duration boundary, and semantic equations? [Measurability, Spec SC-002/FR-039; Plan Performance Evidence]
- [x] CHK025 Are usability outcomes objectively derivable from exact eligibility, allocation, accommodation, replacement, participant, aggregate, and threshold rules? [Measurability, Spec FR-030/SC-001/SC-006; Plan Usability Evidence]
- [x] CHK026 Are sovereign platform acceptance conditions objectively derivable from resource type, OS cardinality, x64 architecture, IMDS location, matching metadata, digest, command outcomes, and named review? [Measurability, Spec FR-035; Plan Sovereign External Platform Evidence]
- [x] CHK027 Are output requirements measurable through exact streams, exit codes, newline rules, literal labels and states, terminal sizes, ANSI absence, token order, and no pager/input? [Measurability, Spec FR-018/FR-028/SC-007; Plan Output Contract]
- [x] CHK028 Are catalog bounds measurable through exact source, record, byte, redirect, and per-source deadline limits plus atomic-failure semantics? [Measurability, Spec FR-021-FR-023; Plan Technical Context/Catalog Collection]

## Scenario And Edge-Case Coverage

- [x] CHK029 Are primary, alternate, exception, and recovery requirements documented for no-root execution, empty scopes, malformed installed records, catalog failure, usage errors, and runtime errors? [Coverage, Spec User Stories/Edge Cases/FR-009-FR-017/FR-028/FR-038]
- [x] CHK030 Are catalog boundary and recovery scenarios documented for oversized or growing local files, decoded remote limits, redirect exhaustion, deadline expiry, malformed sources, and worker cleanup? [Coverage, Spec FR-021-FR-023/FR-032; Plan Catalog Collection]
- [x] CHK031 Are external lifecycle exception scenarios documented for wrong region, VMSS provenance, duplicate keys, mismatched fragments, digest failure, rejected review, and invalid canonical composition? [Coverage, Spec FR-035; Plan Sovereign External Platform Evidence; Data Model SovereignExternalPlatformEvidence]
- [x] CHK032 Are usability exception and recovery scenarios documented for unavailable accommodations, pre-exposure interruption, same-stratum replacement, post-exposure retention, and failed-study evidence? [Coverage, Spec FR-030/FR-036; Plan Usability Evidence]
- [x] CHK033 Are dirty-root scenarios covered for initially absent paths, staged and unstaged bytes, untracked files, external coverage outputs, pre-existing failures, new regressions, and command drift? [Coverage, Spec FR-033-FR-034; Plan Repository Safety And Root Integration]

## Non-Functional Requirements

- [x] CHK034 Are performance, accessibility, privacy, data sovereignty, graceful degradation, auditability, and read-only safety requirements explicit and bounded? [Completeness, Plan Constitution Check/Technical Context; Spec FR-008/FR-018/FR-021-FR-023/FR-029-FR-039]
- [x] CHK035 Are privacy requirements explicit about excluding credentials, SAS tokens, absolute paths, raw exceptions, inventory/source/evidence payloads, and external evidence from logs and repository storage? [Security, Privacy, Spec FR-033-FR-035; Plan Constitution Check/Sovereign External Platform Evidence]
- [x] CHK036 Are accessibility requirements expressed as an objective text oracle plus accommodation rules without claiming that automation proves general comprehension? [Accessibility, Spec FR-018/FR-030/SC-001/SC-006/SC-007; Plan Output Contract/Usability Evidence]

## Dependencies And Assumptions

- [x] CHK037 Are external VM, IMDS, network, managed identity, Blob RBAC, retention, reviewer, and participant prerequisites documented with ownership outside this feature? [Dependency, Spec Dependencies; Plan Constitution Check/Sovereign External Platform Evidence]
- [x] CHK038 Are repository-only authority, no external checkout, no Azure provisioning, no external execution, no fabricated completion, and no commit or push stated as design boundaries? [Assumption, Spec FR-029/FR-035-FR-039; Plan Summary/Technical Context/Implementation Phases]

## Traceability And Diagnostics

- [x] CHK039 Are all requirement clusters traceable from the 40 FRs and 7 SCs into named plan sections, data-model entities, research decisions, quickstart gates, and seven current contracts without relying on implementation status? [Traceability, Spec FR-001-FR-040/SC-001-SC-007; Plan Architecture through Implementation Phases]
- [x] CHK040 Are diagnostics specified for metadata invalidity, activation failure, identity conflict, catalog degradation, usage/runtime errors, schema or semantic invalidity, baseline mismatch, external lifecycle failure, and rejected review? [Completeness, Spec FR-006/FR-009-FR-010/FR-013/FR-016-FR-017/FR-020/FR-028/FR-034-FR-037; Plan Output Contract/Evidence And External Validation]
- [x] CHK041 Is the plan free of unresolved template markers, placeholder sections, and clarification tokens, with all canonical headings populated? [Clarity, Plan]
- [x] CHK042 Do all seven current JSON Schemas parse and compile under Ajv Draft 2020-12 strict mode with unique identifiers, resolved references, formats enabled, and zero warnings? [Diagnostics, Current Contract Set]
- [x] CHK043 Are all seven current schemas closed at their document roots and explicit about required top-level fields, preventing unspecified top-level contract drift? [Clarity, Current Contract Set]
- [x] CHK044 Are the plan and feature directory free of editor diagnostics that would make the requirements or contract artifacts ambiguous? [Diagnostics, Plan/Current Contract Set]

## Notes

- Checked: 44; unchecked: 0; blockers: 0; total: 44.
- Evaluation focus: restored-plan completeness, sovereign CI design, protected-state and root-coverage isolation, current/planned schema ownership, semantic performance and usability evidence, AU Blob collect/finalize lifecycle, prose-only pending handoff, traceability, and diagnostics.
- Depth and audience: formal Phase 4 reviewer gate before task generation or implementation.
- Static evidence: 40 contiguous FR identifiers, 7 contiguous SC identifiers, seven current contract files, complete plan schema inventory, no unresolved template residue, and no VS Code diagnostics in the feature directory.
- Contract evidence: all seven current schemas compiled with local Ajv 8.20 in Draft 2020-12 strict mode, formats enabled, unique `$id` values, and zero warnings.
- The existing workflow does not yet contain `specify-cli-quality`; this is consistent with the plan describing one future reviewed implementation edit and is not a requirements-quality blocker.
- Real CI execution, standalone VM collection, AU-side finalization/review, and the 20-person study remain future implementation or external actions and are not claimed by this checklist.
- Each `/speckit.checklist` run creates a new checklist file; this evaluation leaves prior checklists and authoritative artifacts unchanged.