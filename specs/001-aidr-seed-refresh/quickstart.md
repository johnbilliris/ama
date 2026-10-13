# Quickstart: AIDR Seed Refresh

Phase 3 design reference only. This plan does not execute a refresh, modify
application code, generate implementation tasks, or publish content.

## Existing architecture

1. Canonical catalogue: `packages/domain/src/domain/seed/disasters_australia.json`.
2. Catalogue bootstrap: `packages/domain/src/domain/seed/bootstrap.py`.
3. Cosmos seed upsert: `scripts/seed_loader.py`, existing `seed` container.
4. Dashboard projection: `apps/api/app/services/dashboard_service.py`,
   `_build_from_cosmos`.
5. Web response types: `apps/web/src/lib/api/dashboard.ts`.
6. Incident display and source attribution:
   `apps/web/src/app/incidents/[incidentId]/page.tsx`.

No new service, endpoint, container, request-time AIDR fetch, or separate
narrative field is planned.

## Planned implementation approach

1. Derive the complete current AIDR cohort from the canonical catalogue,
   recording its identifiers as test inputs rather than freezing a historic
   count.
2. Refresh each record's existing `introduction` with the complete available
   AIDR incident content. Preserve stable identifiers, source references, and
   other verified attributes.
3. Include AIDR's required attribution with the actual year of use and omit
   passages identified as third-party content unless the owner permits
   reproduction.
4. Retain verified existing information when a source is unavailable or has
   no additional explanatory text; do not infer missing facts.
5. Verify the heatwave incident
   `aidr-2349-health-national-heatwave-2012` against all material details in
   the feature specification.
6. Use the existing seed upsert/API/page path. Change code only if tests
   demonstrate that the same complete `introduction` is not passed through or
   rendered unchanged.

## Automated verification design

- **Catalogue coverage**: set/uniqueness assertions prove that every current
  AIDR record is covered exactly once, including newly added cohort members.
- **Stored-to-rendered equality**: automated tests compare the captured
  `introduction` value with the dashboard projection and rendered incident
  content, proving the exact value reaches the page unchanged.
- **Content constraints**: check UTF-8 integrity, complete available text,
  retention of verified information for unavailable/incomplete sources,
  non-commercial attribution, and third-party exclusion.
- **Example acceptance**: verify the heatwave account covers all specified
  temperature records, geography, Perth/Sydney impacts, ambulance/hospital
  impacts, and the Bureau's exceptional-event characterization.
- **Regression**: retain seed schema, PII/PSPF, API, and web tests.

The verification design does not require a separate per-record manual
evidence ledger. Tests are to be selected and run during implementation;
none are executed as part of this planning pass.

## Human release gate

The constitution-required human operator review applies before public
dissemination or release of the public-facing output. It is not a prerequisite
for local catalogue refresh, code changes, or automated verification. No
public release is included in this planning scope.
