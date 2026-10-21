# Contract: Incident Dashboard Historical Content

**Feature**: `001-aidr-seed-refresh`
**Interface**: Existing `GET /incidents/{incident_id}/dashboard` API
**Scope**: Preserve the existing response contract while passing the refreshed AIDR narrative directly to the incident page; no new route or narrative field.

## Relevant response fields

| Field | Type | Contract |
|---|---|---|
| `incident.introduction` | `string` | Single incident narrative. For AIDR records, contains the complete available verified explanatory content and is the same value displayed in “About this Incident”. Return in full, without truncation or summarization. |
| `incident.sourceUrl` | `string` | Existing AIDR source/attribution URL; preserve. |

Other existing dashboard fields remain unchanged. No per-record review
metadata is required by this public content contract.

## Invariants

1. Automated catalogue-wide checks confirm that every current AIDR record is
   refreshed exactly once; a historic record count is not hard-coded.
2. For every captured AIDR `introduction`, the dashboard projection returns
   the stored value unchanged and the page renders that exact value in “About
   this Incident.”
3. The page does not substitute a separate summary or duplicate a source
   narrative block.
4. Preserve the source URL and include the required AIDR attribution:
   “Obtained from the Australian Institute for Disaster Resilience, © Commonwealth of Australia [year of use].”
   Use the actual year of use in published output.
5. Exclude content explicitly identified as third-party-owned unless its
   owner permits reproduction.
6. When a source is unavailable or lacks explanatory detail, preserve
   verified content and do not fabricate missing text.
7. Render narrative text as escaped text, never as injected source HTML.
8. No runtime request to AIDR is required to load the incident page.
9. Consumers of existing fields remain compatible; no additive API response
   field is required by this feature.
10. The human operator reviews public-facing output before dissemination or
    release. This review does not block local refresh, code changes, or
    automated validation.

## Representative example (shape only)

```json
{
  "incident": {
    "incidentId": "aidr-2349-health-national-heatwave-2012",
    "introduction": "<complete verified AIDR explanatory account>",
    "sourceUrl": "https://knowledge.aidr.org.au/resources/health-national-heatwave-2012/"
  }
}
```

The placeholder is structural, not incident content. Intended AIDR use is
non-commercial under the applicable terms. Apply the attribution and
third-party-content constraints above. Human operator review remains required
before public dissemination or release.
