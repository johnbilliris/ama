# Tasks: Refresh AIDR Seed Incident Content

**Input**: Approved `spec.md`, regenerated `plan.md`, `data-model.md`,
`contracts/incident-dashboard-content.md`, `quickstart.md`, and current
checklists in this directory.

**Scope**: Refresh the complete current AIDR seed cohort and prove that the
single stored `introduction` value is displayed unchanged. The intended AIDR
use is non-commercial. Include the required attribution:
“Obtained from the Australian Institute for Disaster Resilience, ©
Commonwealth of Australia [year of use].” Exclude content identified as
third-party-owned unless its owner permits reproduction. Do not create a
manual per-record evidence ledger or an unresolved blanket rights blocker.

## Phase 1: Independent verification work

<!-- parallel-group: 1 -->
- [x] T001 [P] Add catalogue-wide automated coverage checks in
  `tests/contract/test_aidr_seed_refresh_coverage.py`: derive the current
  `source: "aidr"` cohort at execution time, assert stable-ID/source-reference
  uniqueness, and verify every current record has refreshed content or a
  verified fallback without hard-coding the observed catalogue count. Include
  UTF-8, non-commercial attribution, and item-level third-party exclusion
  assertions; do not require a per-record manual evidence ledger.
- [x] T002 [P] Add API contract coverage in
  `tests/contract/test_aidr_introduction_passthrough.py` proving that each
  captured `introduction` and `source_url` is returned unchanged by
  `apps/api/app/services/dashboard_service.py`, with no truncation,
  summarization, or separate narrative field.
- [x] T003 [P] Extend `apps/web/tests/unit/incident-page.test.tsx` to prove
  that a multi-paragraph captured `introduction` is rendered in full in
  “About this Incident” as escaped text, with the AIDR attribution/source
  link present and no runtime request to AIDR.

<!-- sequential -->
- [x] T004 Re-inventory the current AIDR cohort from
  `packages/domain/src/domain/seed/disasters_australia.json` and refresh every
  record in that same file. Preserve stable IDs, source IDs/URLs, and verified
  attributes; place the complete available AIDR incident content directly in
  `introduction`; retain verified content for unavailable, incomplete, sparse,
  or non-explanatory sources without inventing facts. For identified
  third-party material, omit it unless owner permission is available. Apply
  the required AIDR attribution with the actual year of use. Reconcile
  membership and outcomes through automated checks, not a manual evidence
  ledger.

<!-- sequential -->
- [x] T005 Validate and correct
  `aidr-2349-health-national-heatwave-2012` in
  `packages/domain/src/domain/seed/disasters_australia.json`. Confirm its
  complete `introduction` covers the first six days of 2013 among the 20
  hottest days for average maximums, geographic extent, the 7 January
  national average maximum record, Perth impacts and ambulance/hospital
  presentations, Alice Springs and Oodnadatta records, Sydney’s 17 January
  record, ambulance treatments and commuter disruption, increased admissions
  for kidney disease, acute renal failure and heart attacks, and the Bureau’s
  exceptional-event characterization.

<!-- sequential -->
- [x] T006 If automated checks identify a broken pass-through or display
  behavior, update only the owning implementation files
  (`apps/api/app/services/dashboard_service.py`,
  `apps/web/src/lib/api/dashboard.ts`, or
  `apps/web/src/app/incidents/[incidentId]/page.tsx`) so the stored
  `introduction` remains the sole narrative, is returned and rendered
  unchanged, is safely escaped, and retains the required attribution/source
  link. Do not add a second content field or runtime source fetch.

## Phase 2: Automated catalogue and rendering validation

<!-- sequential -->
- [x] T007 Run the catalogue coverage, API pass-through, and web rendering
  tests from T001–T003 together with the existing seed schema, loader,
  PII/PSPF, API, and incident-page checks. Confirm automated reconciliation
  covers 100% of the current AIDR cohort exactly once and that every captured
  `introduction` is equal from stored seed through API response to rendered
  page. Resolve failures in the owning data, implementation, or test file.

<!-- sequential -->
- [x] T008 Perform a final local refresh/code/test verification using the
  existing seed loader path without publishing. Confirm no fixed historical
  record count is assumed, all available explanatory text is retained in the
  same `introduction`, unavailable/incomplete sources retain verified content,
  third-party material lacking owner permission is absent, and attribution is
  present.

## Phase 3: Release boundary

<!-- sequential -->
- [ ] T009 Before any public dissemination or release, have a human operator
  review the exact public-facing catalogue/dashboard output and confirm the
  AIDR attribution and item-level third-party permissions. Record the release
  decision in the project’s normal release records. This is a
  pre-dissemination/release task only; it must not block local refresh,
  implementation, or automated validation.

<!-- sequential -->
- [ ] T010 Only after T007–T009 are complete and release approval is explicit,
  use the existing `scripts/seed_loader.py` path to upsert the refreshed
  catalogue to the approved target. Verify the upsert covers the current
  cohort and do not publish when the human release decision is absent.

## Dependencies and execution order

- T001, T002, and T003 are independent parallel test changes because they
  touch distinct files and have no incomplete dependencies.
- T004 must complete before T005; both modify the canonical seed catalogue.
- T006 follows the first automated findings and precedes T007.
- T007 and T008 are local automated validation and do not require human
  review.
- T009 is the constitution-required human review at the dissemination/release
  boundary, not a prerequisite for T004–T008.
- T010 depends on passing automated validation and explicit release approval.

## Completion criteria

- Every current seeded AIDR record is refreshed or safely retains verified
  fallback content, with no fixed cohort count.
- Complete available explanatory content is stored in the single
  `introduction` and rendered unchanged.
- The heatwave account contains every required context category.
- Automated checks prove catalogue-wide completeness and stored-to-rendered
  equality; no manual per-record evidence ledger is required.
- Required AIDR attribution is present, and identified third-party content is
  excluded unless its owner permits reproduction.
- Human operator review occurs before public dissemination/release only.
