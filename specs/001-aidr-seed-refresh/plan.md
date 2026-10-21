# Implementation Plan: Refresh AIDR Seed Incident Content

**Branch**: `001-aidr-seed-refresh` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)
**Input**: Approved feature specification at `specs/001-aidr-seed-refresh/spec.md`

## Summary

Refresh every AIDR incident in the existing seed catalogue with the complete
available and verified AIDR incident content, including the full `introduction`.
The stored `introduction` remains the sole narrative and is passed through the
existing Cosmos dashboard projection and rendered unchanged on the incident
page. Validate catalogue-wide coverage and stored-to-rendered equality
automatically. Apply AIDR's non-commercial-use attribution conditions and
exclude identified third-party content unless its owner permits reproduction.
Human operator review remains a pre-dissemination/release check; it is not a
prerequisite for local refresh, code changes, or automated verification.

## Technical Context

**Language/Version**: Python 3.12; TypeScript/Node.js 22 for the web workspace
**Primary Dependencies**: Existing domain seed loader; FastAPI API; Next.js 16, React 19
**Storage**: Versioned JSON seed catalogue; existing Azure Cosmos DB `seed` container
**Testing**: pytest for domain/API and seed checks; Vitest/Playwright for web rendering
**Target Platform**: Existing Python API and Next.js web application; Azure-backed runtime
**Project Type**: Full-stack web application with a static seed-data pipeline
**Performance Goals**: No new runtime fetch or service; preserve existing incident-page response behavior
**Constraints**: Preserve stable incident identifiers and source references; retain verified data for unavailable/incomplete sources; do not invent facts; display the same full `introduction` value; escape text rather than render source HTML; omit identified third-party material without its owner's permission; include AIDR attribution with the year of use. Operator review is required before public dissemination/release only.
**Scale/Scope**: All AIDR records in the canonical disaster seed catalogue at refresh time (current checkout baseline: 523; not a permanent fixed count); heatwave example details as specified in the feature spec.

## Constitution Check

**Initial gate (before research): PASS**

- **Human-in-the-loop / public information**: No irreversible operational action is introduced. The constitution-required human operator review of public-facing output is preserved as a prerequisite to dissemination or release. It does not block local catalogue refresh, code changes, or automated validation.
- **Transparency and auditability**: Preserve AIDR source identifiers and URLs, include the specified attribution, and make cohort coverage and narrative equality machine-verifiable. No separate per-record manual evidence ledger is required.
- **Privacy/data sovereignty**: This is historical public-source seed content; no new personal data or data-persisting service is planned. Existing AU-bound runtime storage remains unchanged.
- **Quality gates**: Automated data/API/UI verification and existing repository quality gates are retained; no public release proceeds without operator review.
- **Architecture**: Reuse existing seed, API, and page paths; no infrastructure change or constitution exception is needed.

**Post-design gate: PASS** — the design preserves the operator release gate and source-use constraints without turning them into blockers for local refresh or automated checks. No constitution violation or exception is identified.

## Architecture and Project Structure

The change follows the existing data path:

1. Refresh `packages/domain/src/domain/seed/disasters_australia.json`, keeping
   one narrative in each record's existing `introduction` field.
2. Keep `packages/domain/src/domain/seed/bootstrap.py` and
   `scripts/seed_loader.py` as the existing catalogue loading and Cosmos
   upsert path.
3. Keep the current API projection in
   `apps/api/app/services/dashboard_service.py`.
4. Keep the existing incident display and AIDR source link in
   `apps/web/src/app/incidents/[incidentId]/page.tsx`, with its current API
   types in `apps/web/src/lib/api/dashboard.ts`.
5. Add/update focused tests in the existing domain/API/web test locations to
   prove 100% current-cohort record coverage and exact stored-to-rendered
   `introduction` equality, alongside source completeness, fallback, heatwave,
   attribution, and third-party exclusion checks.

No new endpoint, content store, request-time source fetch, duplicate narrative
field, or manual evidence ledger is planned.

### Documentation (this feature)

```text
specs/001-aidr-seed-refresh/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── incident-dashboard-content.md
└── tasks.md                 # Existing artifact; task generation is out of scope here
```

### Relevant source directories

```text
packages/domain/src/domain/seed/       # Canonical JSON seed and bootstrap
scripts/                                # Existing seed-loader entry point
apps/api/app/services/                  # Dashboard projection
apps/web/src/app/incidents/             # Incident page
apps/web/src/lib/api/                   # Dashboard response types
tests/                                  # Existing Python and web test suites
```

**Structure Decision**: Extend the existing full-stack seed-to-Cosmos-to-API-to-
page flow. The feature is primarily a catalogue refresh with regression
coverage; production service boundaries and storage remain unchanged.

## Content-use and publication controls

- Intended AIDR content use is non-commercial. Reproduce AIDR content with the
  attribution: “Obtained from the Australian Institute for Disaster
  Resilience, © Commonwealth of Australia [year of use].” Use the actual year
  of use in the published attribution.
- Exclude content explicitly identified as belonging to or used with
  permission of a third party unless that owner's permission to reproduce it
  is available.
- Preserve source URLs and do not imply that excluded third-party material is
  AIDR-authored content.
- A human operator reviews the public-facing output before dissemination or
  release, in accordance with the constitution. This gate applies to that
  release boundary only, not to local refresh, code changes, or automated
  verification.

## Complexity Tracking

No constitution violations or additional architectural complexity require
justification.
