# AIDR Handbook Licence + Indexing Inventory

**Purpose**: per-handbook record of publication, redistribution rights, and per-handbook indexing approval. Required by FR-AI01 (amended). Defaults to **metadata-only** mode for any handbook not approved here.

> **Approval columns**:
> - `compliance_signoff`: signed by Compliance Auditor persona handle + date.
> - `architecture_signoff`: signed by Solution Architect persona handle + date.
> - `mode`: `full-text` (chunked + embedded), `metadata-only` (title + chapter summaries), or `excluded`.
>
> Until both sign-offs are present, default = `metadata-only`.

## Inventory

| Handbook | Year | Publisher | Citation URL | Redistribution rights | Compliance signoff | Architecture signoff | Mode |
|---|---|---|---|---|---|---|---|
| Incident Management Handbook | 2023 | AIDR | https://www.aidr.org.au/resources/incident-management/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Evacuation Planning Handbook | 2023 | AIDR | https://www.aidr.org.au/resources/evacuation-planning-handbook/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Public Information and Warnings Handbook | 2021 | AIDR | https://www.aidr.org.au/resources/public-information-and-warnings/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Australian Warning System Companion | 2022 | AIDR / AFAC | https://www.aidr.org.au/resources/australian-warning-system/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Community Recovery Handbook | 2018 | AIDR | https://www.aidr.org.au/resources/community-recovery/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Australian Emergency Management Arrangements | 2023 | AIDR | https://www.aidr.org.au/resources/australian-emergency-management-arrangements/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Emergency Planning Handbook | 2020 | AIDR | https://www.aidr.org.au/resources/emergency-planning/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Monitoring & Evaluation Framework for Disaster Recovery | v2 | AIDR | https://www.aidr.org.au/resources/monitoring-and-evaluation-framework-for-disaster-recovery-programs/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |
| Outcomes, Activities and Indicators for Recovery | 2020 | AIDR | https://www.aidr.org.au/resources/outcomes-activities-and-indicators/ | Practitioner use; cite source | _pending_ | _pending_ | metadata-only |

## How to add an approval

1. Verify the handbook's current licence terms on the publisher's site.
2. Append the handbook row above (or update an existing row) with:
   - `compliance_signoff`: `<your-handle> 2026-04-30`
   - `architecture_signoff`: `<your-handle> 2026-04-30`
   - `mode`: `full-text` (after sign-off)
3. Open a PR; reviewers verify signatures.
4. Stream 6 ingestion job (T602) automatically picks up the new mode on next deploy.

## Excluded handbooks

If a handbook is explicitly excluded (e.g. publisher revoked permission), set `mode: excluded`. The ingestion job will:
1. Delete all documents in the AI Search index for that `handbook_id`.
2. Emit a `rag.licence.exclusion_applied` audit event.
