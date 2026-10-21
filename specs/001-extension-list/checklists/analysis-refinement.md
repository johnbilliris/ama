# Analysis Refinement Checklist: Extension List

**Purpose**: Confirm the latest bounded specification, evidence, CI, and sequencing decisions are explicit and internally consistent
**Created**: 2026-09-21
**Feature**: [Extension List specification](../spec.md)

## Automated PR Gate

- [x] AR001 Is one reviewed edit to `.github/workflows/ci.yml` permitted solely for `specify-cli-quality`, while root `pyproject.toml`, `ruff.toml`, and `.pre-commit-config.yaml` remain unchanged?
- [x] AR002 Does the job require labels `self-hosted`, `ama-au-sovereign`, `azure-au`, `linux`, and `x64`, with AU IMDS verification before package work?
- [x] AR003 Does the job run locked sync, package Ruff check/format, strict mypy, package pytest/coverage, wheel build, clean install, and both smokes using synthetic fixtures and value-free output?
- [x] AR004 Does `.github/workflows/ci.yml` remain protected at its post-edit state for every later executable operation, and do all actual PR lint/unit/integration jobs have to pass before merge?

## External Lifecycle

- [x] AR005 Are `collect` and `finalize` locally tested but never externally executed during implementation?
- [x] AR006 Does collect create one no-overwrite fragment per standalone AU VM under the shared UUID session path using private-endpoint TLS and managed identity?
- [x] AR007 Does finalize require exactly one Windows and one Ubuntu fragment with matching session/package/lock/script version, valid digests, named approved/rejected review, canonical validation, and conditional final creation?
- [x] AR008 Are rejected reviews retained externally while pending-external remains prose-only, with no repository status JSON and no evidence values in terminal, GitHub, or repository persistence?

## Semantic Validation

- [x] AR009 Does performance validation run after schema validation, require exactly 30 durations, compute sorted rank-29 P95, and verify exact P95, threshold 2.000, and passed equality?
- [x] AR010 Does usability schema permit aggregate counts from 0 through 20 while semantic validation separately reports SC-001 pass at 19 and SC-006 pass at 18?
- [x] AR011 Is external completion defined as completed validation/review rather than success-threshold passage?

## Sequencing And Inventory

- [x] AR012 Must all seven current schemas compile and fixture-test green before any expected red?
- [x] AR013 Are expected schema reds limited to the two planned read-only/performance shape contracts and semantic reds limited to missing validators, with runtime payloads external-temp-only and deleted after validation?
- [x] AR014 Are hosted fragment/finalization and performance semantic validators implemented before identical green reruns?
- [x] AR015 Are usability schema execution, conditional schema edit, identical schema green, semantic red, semantic implementation, and identical semantic green separate ordered steps?
- [x] AR016 Is platform schema verification represented by one explicit fixture file and command, with exactly seven current schemas total and two planned schemas?

## Boundaries

- [x] AR017 Are prose-only pending handoff, no repository platform payload, AU Blob-only evidence, exact root coverage isolation, strict schemas, objective text oracle, deterministic usability, same-source coalescence, exact stream ownership, guard-first execution, bounded catalogs, and no external checkout/commit/push preserved?

## Phase 3 Root-Cause Refinement

- [x] AR018 Are all red, baseline, read-only, performance, and status payloads prohibited from repository persistence, with one sanitizer, external-temp raw capture, minimized status, and secure deletion?
- [x] AR019 Are the protected-state self-check and dispatcher self-check the only bootstrap executions, with identical protection required for every later dispatcher-owned mode?
- [x] AR020 Must every expected-red task carry one complete canonical dispatcher command whose green replay is byte-identical, including combined slices, environment, files, `-q`, selectors, and markers?
- [x] AR021 Does the study contract require notice, consent, purpose limitation, random pseudonyms, no direct/free-text identifiers, separate keys/recruitment records, AU storage, least privilege, immutable audit, encryption, 90-day deletion, withdrawal, incident response, and coded accommodations only?
- [x] AR022 Do collect and finalize fail before Blob access unless ARM region/network/private-endpoint state, private DNS, exact container-scoped Blob Contributor RBAC, and a digest-valid named AU pre-write attestation all verify?
- [x] AR023 Are actual study evidence and external lifecycle evidence/attestations AU-store-only, with synthetic local fixtures and value-free terminal summaries?

## Notes

- Checked: 23; unchecked blockers: 0; total: 23.
- This checklist supersedes conflicting external-lifecycle or CI wording in earlier phase checklists; it does not claim implementation, external execution, review, study, or PR completion.
- Existing `tasks.md` was intentionally not modified during this refinement and still contains obsolete repository runtime-evidence paths. It MUST be discarded or regenerated from the refined specification and contracts before implementation; no stale task may be executed.