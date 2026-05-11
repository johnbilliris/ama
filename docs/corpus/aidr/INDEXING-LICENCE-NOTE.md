# AIDR Indexing Licence Note

**Status**: Working position pending Compliance Auditor + Solution Architect sign-off (per FR-AI01 amended).

## Position

The Australian Institute for Disaster Resilience (AIDR) publishes the Australian Disaster Resilience Handbook Collection for use by emergency-management practitioners, governments, and trainers. This platform — the Autonomous Disaster Response Coordination Hub — is a multi-agency emergency-management coordination tool, and our use of the handbooks for **operational grounding** of LLM recommendations falls within the practitioner-use scope the publisher intends.

For the purposes of FR-AI01 (RAG over `docs/aidr/`), the platform:

1. **Stores extracts only inside the AU tenant** — the Azure AI Search index is provisioned in Australia East with no cross-region replication, no public network access, and Private Endpoint only.
2. **Cites every retrieved chunk** with handbook + page reference in the operator-facing recommendation card, preserving attribution.
3. **Does not redistribute** the corpus outside the platform tenant.
4. **Maintains a per-handbook inventory** in [`LICENCE-INVENTORY.md`](LICENCE-INVENTORY.md) capturing publisher, edition, citation URL, redistribution rights, and per-handbook indexing approval — handbooks not present in (or not approved by) the inventory default to **metadata-only** mode (titles + chapter summaries) rather than full-text indexing.

## Governance

- **Approvers** (per FR-AI01): Compliance Auditor + Solution Architect personas.
- **Review cadence**: annual, or whenever AIDR publishes a new edition or licence terms change.
- **Removal request**: if a publisher requests removal of a handbook, the index ingestion job re-runs with the affected `handbook_id` removed and the AI Search documents are deleted within 24 hours.

## Caveat

This note is a **working position**, not a formal legal opinion. Before promoting handbooks beyond metadata-only in production, the per-handbook inventory MUST carry explicit licence sign-off recorded in `LICENCE-INVENTORY.md`. CI will block production deploys that attempt full-text indexing of an unapproved handbook (Stream 6 task T602 enforces).

## References

- Constitution `AIDR Handbook Collection Reference` table.
- Spec 032 FR-AI01 (amended).
- AIDR home: <https://www.aidr.org.au/>
