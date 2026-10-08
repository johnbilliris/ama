# Specification Requirements Quality Checklist: Extension List

**Purpose**: Reassess whether the refined specification is complete, clear, consistent, measurable, traceable, and ready for implementation review
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

**Note**: This checklist evaluates the specification as requirements writing. Checked items are adequately specified; unchecked items are requirement blockers.

## Requirement Completeness

- [x] CHK001 Are all three list scopes, two output modes, two entry points, read-only boundaries, empty states, and no-project-root outcomes explicitly required? [Completeness, Spec FR-001-FR-004/FR-028-FR-029/FR-038]
- [x] CHK002 Are activation, health, diagnostics, identity, capability, coalescence, duplicate, reconciliation, ordering, fallback, provenance, and permission requirements complete for every row class? [Completeness, Spec FR-005-FR-020/FR-024-FR-027]
- [x] CHK003 Are bounded catalog source count, record count, size, redirects, total deadline, spawned supervision, complete validation, and all-or-nothing failure semantics specified? [Completeness, Spec FR-021-FR-023/FR-032]
- [x] CHK004 Are AMA-local packaging, guard-first execution, expanded protected manifest, root coexistence, baseline attribution, test-first sequencing, separated gate ownership, and default local-synthetic implementation on ordinary Windows/Linux without an Azure VM or resource all required? [Completeness, Spec FR-029/FR-033-FR-034/FR-039-FR-040/Cross-Cutting Phase 3 Refinements]
- [x] CHK005 Are exactly standalone Windows x64 and Ubuntu Linux x64 Azure VMs required for sovereign external validation, with IMDS proof and no VMSS ambiguity? [Completeness, Spec FR-035]
- [x] CHK006 Are the profile boundaries complete: local-synthetic accepts only synthetic fixtures/fake transports and rejects production/live data, real catalogs, qualifying evidence, real collect/finalize, and sovereignty/release claims, while sovereign collect/finalize retains AU Blob publication, managed identity, exact RBAC, minimized records, digest, review, and prose-only pending handoff? [Completeness, Spec FR-035-FR-039/Cross-Cutting Phase 3 Refinements]
- [x] CHK007 Are participant requirements complete for adult monthly CLI users with no prior exposure, exact novice/experienced criteria, exact stratum counts, requested accommodations, exclusions, replacements, and retained post-exposure outcomes? [Completeness, Spec FR-030/SC-001/SC-006]
- [x] CHK008 Are deterministic allocation requirements complete for algorithm identifier, seed, variants, SHA-256 ordering input, tie-break, round-robin assignment, and exact recomputation? [Completeness, Spec FR-030/SC-001/SC-006]
- [x] CHK009 Does the Dependencies section clearly separate local-only prerequisites (Python, Git, owner-only temp/IPC, synthetic fixtures, configured HTTPS proxy or cache, and no Azure resource) from sovereign-only prerequisites (signed preflight, AU VM/IMDS/encryption, private networking, immutable ledger, managed identity/RBAC, reviewer, and cohort)? [Gap resolved, Spec Dependencies/Cross-Cutting Phase 3 Refinements/FR-035-FR-037]

## Requirement Clarity

- [x] CHK010 Is same-source coalescence defined before stable-ID grouping, with same-ID observations combined, contradictory IDs producing one invalid identity conflict, and only distinct sources producing duplicate-ID conflicts? [Clarity, Spec FR-013/FR-025]
- [x] CHK011 Is catalog preferred order exact and source-order independent: priority, case-folded name, raw name, normalized record SHA-256, then ordinal only for byte-identical ties? [Clarity, Spec FR-026]
- [x] CHK012 Are human usage errors, JSON usage errors, runtime errors, degraded catalog warnings, and explicit help assigned exact distinct streams, payloads, newlines, and statuses, with help precedence explicit? [Clarity, Spec FR-028]
- [x] CHK013 Is every usability eligibility, allocation, accommodation, exclusion, replacement, and aggregate term quantified sufficiently for deterministic semantic validation? [Clarity, Spec FR-030/SC-001/SC-006]
- [x] CHK014 Is AU-store approved/rejected review distinct from automated internal-consistency validation and absent from repository-local completion state? [Clarity, Spec FR-035-FR-037]
- [x] CHK015 Are the platform-record digest and review values precise enough to remove producer and reviewer interpretation? [Ambiguity resolved, Spec FR-035]
- [x] CHK016 Is local-synthetic baseline completion clearly distinguished from qualifying evidence, sovereignty, release, external completion, and merge readiness, with real pull-request lint, unit, and integration jobs required green? [Clarity, Spec FR-037/Cross-Cutting Phase 3 Refinements]

## Requirement Consistency

- [x] CHK017 Do user stories and functional requirements agree on scope inclusion, installed fallback after catalog failure, duplicate catalog consolidation, and distinct installed/available versions? [Consistency, Spec User Story 3/FR-003-FR-004/FR-012/FR-016-FR-019]
- [x] CHK018 Do identity requirements and edge cases agree on normalized-source coalescence, invalid contradictory IDs, identifier-less isolation, and distinct-source duplicate conflicts? [Consistency, Spec User Story 2.7/Edge Cases/FR-013/FR-020/FR-025]
- [x] CHK019 Do external requirements consistently reserve normal non-synthetic use, qualifying read-only/SC-002 evidence, CI release, and real collect/finalize for sovereign execution while allowing local fake producer/control-boundary tests that cannot create qualifying evidence or success claims? [Consistency, Spec FR-034-FR-039/Cross-Cutting Phase 3 Refinements]
- [x] CHK020 Do usability requirements and success criteria consistently require accommodations to be provided or resolved by pre-exposure exclusion and replacement, never participant declination? [Consistency, Spec FR-030/SC-001/SC-006]
- [x] CHK021 Do protected-state, local-segment baseline attribution, local fake-test success, sovereign qualification, and merge readiness remain independent without allowing one to waive another? [Consistency, Spec FR-033-FR-034/FR-037/FR-039]
- [x] CHK022 Do package isolation requirements preserve root scopes while requiring package-owned Ruff, mypy, coverage, wheel, entry-point, and import-boundary gates? [Consistency, Spec FR-029/FR-034]

## Acceptance Criteria Quality

- [x] CHK023 Can list behavior be assessed from exact inclusion, identity, reconciliation, output-channel, empty-state, and error contracts rather than subjective descriptions? [Measurability, Spec FR-002-FR-028/FR-038]
- [x] CHK024 Can catalog safety and performance be assessed from exact source bounds plus every SC-002 environment, fixture, warmup, duration, rank, P95, threshold, result, and timestamp field? [Measurability, Spec FR-021-FR-023/FR-032/SC-002]
- [x] CHK025 Can participant eligibility, deterministic allocation, accommodation handling, and SC-001/SC-006 outcomes be independently recomputed from required evidence fields? [Measurability, Spec FR-030/SC-001/SC-006]
- [x] CHK026 Can sovereign platform eligibility be assessed from standalone VM resource IDs, OS/architecture, OS-specific proof, IMDS location, outcomes, digest, and pseudonymous closed-coded review? [Measurability, Spec FR-035]
- [x] CHK027 Can protected-state preservation and root regression attribution be assessed from exact manifests/commands, external `COVERAGE_FILE`/`COVERAGE_RCFILE`/XML output, repository coverage-path mutation checks, raw Git bytes, normalized result sets, comparison rules, and the no commit/push/stash/revert/reset/restore/stage boundary? [Measurability, Spec FR-033-FR-034, Tasks Worktree Rule]
- [x] CHK028 Is test-first compliance measurable from a focused observed failure before its matching implementation or producer and a subsequent result from the same focus? [Measurability, Spec FR-039]

## Scenario And Edge-Case Coverage

- [x] CHK029 Are primary, alternate, exception, recovery, and non-functional scenarios represented across list scopes, catalog degradation, invalid records, identity conflicts, CLI misuse, and external gates? [Coverage, Spec User Stories 1-3/Edge Cases/FR-001-FR-040]
- [x] CHK030 Are same-source same-ID, same-source contradictory-ID, distinct-source same-ID, identifier-less aliases, and distinct-name-collision scenarios assigned non-overlapping outcomes? [Coverage, Spec Edge Cases/FR-013/FR-020/FR-025]
- [x] CHK031 Are required-accommodation unavailable, technical interruption, same-stratum replacement, and post-exposure retention scenarios explicitly addressed without a declination path? [Coverage, Spec FR-030/SC-001/SC-006]
- [x] CHK032 Are local custody loss and discontinuous non-evidentiary restart, sovereign terminal custody loss after edits, pending external status, AU-store approved/rejected state, wrong region, VMSS, missing proof/review, local substitution, and unavailable sovereign prerequisites addressed? [Coverage, Spec FR-035-FR-039/Cross-Cutting Phase 3 Refinements]
- [x] CHK033 Are local baseline green, pre-existing failure, new failure, comparison failure, and green real-PR gate scenarios assigned distinct readiness meanings? [Coverage, Spec FR-034/FR-037]

## Dependencies And Traceability

- [x] CHK034 Can every FR and SC be traced to at least one plan, research, data-model, quickstart, CLI-contract, or schema design statement? [Traceability, Spec FR-001-FR-040/SC-001-SC-007]
- [x] CHK035 Are the audit mode/sink invariants (`local-synthetic`/`ephemeral-local`, `sovereign`/`immutable-au`) and sovereign preflight audience `spec001-extension-list-sovereign-preflight` traceable to current strict contracts? [Gap resolved, Spec Cross-Cutting Phase 3 Refinements/FR-035, Agent Action Audit Schema, Implementation Prerequisite Attestation Schema]
- [x] CHK036 Are local-development requirements measurable from exact fixture-marker containment and digest checks plus owner-only, locked, canonical, flushed, ephemeral journal behavior, without requiring any Azure resource? [Measurability, Spec Execution Profiles, Plan Action Audit Profiles, CLI Contract, Tasks T004/T006/T008]

## Notes

- Checked: 36; unchecked blockers: 0; total: 36.
- Local-synthetic is the default implementation path on ordinary Windows/Linux. T008 starts its owner-only, peer-authenticated, mode-bound daemon and captures the non-evidentiary baseline; T009 is the first product edit; every later edit/decision is governed by the Post-T008 action clause and the ephemeral two-phase journal.
- Local dependency bootstrap uses only the configured HTTPS package proxy or existing cache; sovereign CI/build/install remains `UV_OFFLINE=1` through an authorized AU cache. Local synthetic/fake tests cover producer and control boundaries but cannot create qualifying evidence or success claims.
- Sovereign external contracts remain resolved and are required only for normal non-synthetic use, qualifying read-only/SC-002 evidence, CI release, and real collect/finalize. Local custody restart is explicitly discontinuous and non-evidentiary; sovereign post-edit custody loss remains terminal.
