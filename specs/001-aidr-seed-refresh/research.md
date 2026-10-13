# Research: Refresh AIDR Seed Incident Content

**Feature**: `001-aidr-seed-refresh`
**Date**: 2026-10-12
**Status**: Decisions complete; no unresolved technical or content-use clarification

The approved specification resolves the former open items: intended use is
non-commercial; AIDR attribution is specified; identified third-party content
is excluded absent owner permission; catalogue coverage and rendered equality
are automated; human review is required before dissemination/release only.
These are operational constraints, not blanket blockers to local work.

## D1. Catalogue and cohort

**Decision**: Use
`packages/domain/src/domain/seed/disasters_australia.json` as the canonical
catalogue. Refresh every record identified as AIDR in the catalogue at
execution time, reconciling by stable `incident_id`/persisted `id` and
`source_id` while preserving each source reference.

**Rationale**:
- `packages/domain/src/domain/seed/bootstrap.py` loads the file as the
  `disasters` catalogue.
- `scripts/seed_loader.py` is the existing Cosmos seed upsert path.
- The current checkout contains 523 AIDR records, including
  `aidr-2349-health-national-heatwave-2012`; this count is a baseline, not a
  permanently fixed acceptance value.

**Alternatives considered**:
1. Refresh only the heatwave record — rejected because the approved scope is
   every seeded AIDR incident.
2. Create a new catalogue, container, or pipeline — rejected because the
   established catalogue and loader already serve this data.
3. Freeze the observed 523 records as a permanent expected count — rejected;
   validation should derive the current cohort and check complete coverage.

## D2. Single narrative and incident display

**Decision**: Preserve the existing `introduction` as the single narrative.
Capture the complete available AIDR incident content, including its full
`introduction`, and pass that exact same value through the dashboard API to
the incident page. Do not create a second source-text field or shortened
display narrative.

**Rationale**:
- FR-002–FR-007 require complete content capture and direct display.
- `DashboardService._build_from_cosmos` already projects
  `doc["introduction"]`; the incident page already displays it.
- Existing escaped text rendering avoids treating source markup as executable
  HTML.

**Alternatives considered**:
1. Store separate full source and display values — rejected by the approved
   single-value requirement.
2. Keep a short summary on the incident page — rejected because the complete
   captured content must be displayed.
3. Fetch AIDR for each page request — rejected because the current static
   catalogue and API flow suffice and should not depend on source-site
   availability at viewing time.

## D3. Coverage, equality, and incomplete sources

**Decision**: Validate the current AIDR cohort automatically: every current
catalogue record is refreshed exactly once, and each captured `introduction`
is passed through storage/API/UI and rendered unchanged. When a source is
unavailable or lacks explanatory text, retain verified existing information
and add no unsupported facts. Do not require a separate per-record manual
evidence ledger.

**Rationale**:
- SC-001/SC-002 define catalogue-wide coverage and exact-value checks.
- Automated set reconciliation plus stored-to-rendered equality is the
  accepted verification method; a manual evidence ledger would add no
  required gate.
- Source availability does not justify fabricating content.

**Alternatives considered**:
1. Use only a few manual spot checks — rejected because they cannot show
   coverage of the full current cohort.
2. Require a hand-maintained evidence ledger for every record — rejected by
   the approved validation scope.
3. Fill gaps with inferred or generated prose — rejected by FR-008.

## D4. Existing serving path and contract

**Decision**: Update the committed seed catalogue and use the existing
bootstrap, Cosmos upsert, dashboard API, and incident page. Keep existing
`introduction` and source URL fields; no new route, response property,
service, or container is needed.

**Rationale**: The existing service projection and page already support the
single narrative value and AIDR source link. Request-time scraping is
unnecessary.

**Alternatives considered**:
1. Add an API endpoint or duplicate narrative field — rejected because the
   current public contract carries the content.
2. Update only fixtures — rejected because the canonical seed and existing
   upsert are the actual catalogue path.

## D5. Reproduction conditions and release review

**Decision**: Treat the approved conditions as implementation constraints:
use is non-commercial; include the required AIDR attribution with the actual
year of use; exclude content explicitly identified as third-party-owned unless
its owner permits reproduction. Preserve the constitution-required human
operator review before public dissemination/release. That review does not
block local refresh, code changes, or automated verification.

**Rationale**: The feature specification records the applicable AIDR terms
and the human release gate. Source-use conditions can be implemented during
local work without a blanket hold; a public release remains subject to
operator review.

**Alternatives considered**:
1. Treat rights/attribution as an unresolved prerequisite to all work —
   rejected by the approved terms and non-commercial-use clarification.
2. Treat the operator review as a prerequisite to local refresh/testing —
   rejected by the specified release-only timing and would exceed the
   constitution's dissemination gate.
3. Reproduce identified third-party content by default — rejected unless the
   owner permits it.

## D6. Verification

**Decision**: Add automated catalogue-wide record-set/uniqueness checks,
stored-to-rendered exact `introduction` equality checks, source fallback and
encoding checks, AIDR attribution and third-party exclusion checks, and the
heatwave-specific acceptance checks. Retain existing seed schema, PII/PSPF,
API, and web regression gates.

**Rationale**: These checks map to the measurable outcomes in the approved
spec and fit the existing test architecture.

**Alternatives considered**:
1. Rely on word counts or manual spot checks — rejected because they do not
   prove cohort coverage or value equality.
2. Add a manual per-record evidence ledger — rejected by the approved
   verification approach.
