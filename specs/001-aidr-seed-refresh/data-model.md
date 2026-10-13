# Data Model: Refresh AIDR Seed Incident Content

**Feature**: `001-aidr-seed-refresh`
**Canonical storage**: `packages/domain/src/domain/seed/disasters_australia.json`; loaded through the existing pipeline into the Cosmos DB `seed` container.

## Entity: Seeded AIDR incident

One historical AIDR incident in the canonical seed catalogue. Existing
identity and source fields remain stable through refresh.

| Field | Type | Requirement / behavior |
|---|---|---|
| `incident_id` / persisted `id` | string | Existing stable application identity; preserve. |
| `source` | string | Identifies the in-scope records as `aidr`. |
| `source_id` | integer | Existing AIDR source identifier; preserve for cohort reconciliation. |
| `source_url` | absolute URL string | Existing source page URL; preserve and use for attribution. |
| `introduction` | string | The single incident narrative. Capture the complete available AIDR content, including the full introduction; this same value flows through the API and is rendered unchanged on the incident page. No duplicate source/display field. |
| Existing incident attributes | Existing JSON types | Preserve identifiers, type, jurisdiction, dates, location, impacts, and other verified facts; change only where supported by source information. |

No additional per-record manual evidence ledger or review-status/date fields
are required by this feature.

## Entity: Incident dashboard projection

The existing `GET /incidents/{incident_id}/dashboard` response projects the
stored incident to the web application.

| API field | Source | Behavior |
|---|---|---|
| `incident.introduction` | Seed `introduction` | Return the stored value unchanged, without truncation or summarization; display that same value in “About this Incident.” |
| `incident.sourceUrl` | Seed `source_url` | Preserve the source/attribution link. |

No separate `sourceContent` value is introduced. No review metadata is
required in the public incident response.

## Relationships and lifecycle

- An AIDR source reference (`source_id`, `source_url`) identifies the source
  for an existing stable seed record (`incident_id`/persisted `id`).
- A seed record is loaded by the existing bootstrap and upserted to the
  existing Cosmos `seed` container.
- The dashboard projection reads the stored record; page requests do not
  fetch AIDR.
- A human operator reviews the public-facing output before dissemination or
  release. This release-stage check does not gate local refresh, code changes,
  or automated verification.

## Content-use constraints

1. Intended use of AIDR materials is non-commercial.
2. Reproduced AIDR materials include: “Obtained from the Australian Institute
   for Disaster Resilience, © Commonwealth of Australia [year of use].” The
   published attribution substitutes the actual year of use.
3. Content explicitly identified as third-party-owned is excluded unless its
   owner permits reproduction.

## Validation invariants

1. Automated reconciliation confirms every AIDR record in the current
   canonical catalogue is refreshed exactly once; membership is derived at
   execution time, not fixed to a historic count.
2. For each captured `introduction`, automated tests prove the stored value is
   passed through the dashboard response and rendered unchanged.
3. Available explanatory content is complete; unavailable or incomplete
   source information leaves verified content intact and adds no unsupported
   facts.
4. UTF-8 content integrity is preserved.
5. Source attribution is present, and identified third-party content is not
   reproduced without owner permission.
6. Narrative is rendered as escaped text, not injected source HTML.
7. Existing seed schema and PII/PSPF checks continue to pass.
