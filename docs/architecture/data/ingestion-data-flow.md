---
purpose: Traces the ingestion data flow from external signal sources through Event Hubs/Service Bus to Cosmos DB and agent consumers.
personas:
  - Sector
  - Technical-Architecture
diagrams:
  - SECTOR-02
specs:
  - spec-010
  - spec-014
---

# SECTOR-02 — Ingestion Data-Flow

[→ Architecture index](../README.md)

This page traces external CAP, EDXL, and GeoJSON signals from source systems through the AMA ingestion path to Cosmos DB and agent consumers.

![SECTOR-02: Ingestion Data-Flow](ingestion-data-flow.png)

## Key Elements

- FR-014 coverage for BoM, Geoscience Australia, NEMA, and state agency signal sources.
- Event Hubs and Service Bus act as the broker layer before the Ingest Service normalises payloads.
- Cosmos DB stores jurisdiction-scoped events before the Agents Runtime consumes them.

## VIC CFA Forecast Timestamps

The VIC CFA / VicEmergency OSOM GeoJSON feed can publish forecast event timestamps up to 24 hours ahead. Its GeoJSON normalizer therefore accepts future timestamps within a 24-hour window. Other feeds retain the standard 15-minute future-skew limit; values beyond the VIC CFA window are rejected.

## Himawari Latest-Image Alias

BoM's Himawari FTP listing includes a rolling latest-image alias without a timestamp in its filename. For that alias only, ingestion falls back to the FTP `MDTM` modification time (UTC) as the best available event-time estimate; this is the file update time, not a guaranteed observation time. Timestamped Himawari files and other binary feeds continue to use their existing timestamp rules.

## Local Redis Deduplication

The local Compose ingestion service uses `REDIS_URL=redis://redis:6379/0` for shared deduplication. The worker accepts unauthenticated, non-TLS Redis URLs only in development/test environments and only for local Docker/loopback hosts; deployed Azure connections continue to use `REDIS_HOST` with Entra ID authentication and TLS.

## Local Blob Storage

Compose sets `AZURITE_BLOB_CONNECTION_STRING` to select the local Azurite endpoint and shared-key authentication. The worker accepts that setting only when `AMA_ENVIRONMENT` or `ENVIRONMENT` identifies a development/test environment. When it is absent, `STORAGE_ACCOUNT_NAME` selects Azure Blob Storage with the Container App's system-assigned managed identity; the Azure deployment does not set the Azurite connection string.

## Bounded, Resumable Ingestion

Each pipeline processes at most `max_records_per_cycle` records per cycle (default: 100).
Excess records are retained, not truncated. The worker requires Blob Storage and
persists the entire fetched source snapshot under `raw-payloads/ingestion-backlog/`,
with a separate cursor checkpoint keyed by tenant scope and pipeline identity.
It resumes unfinished snapshots before polling the source again, including after a
worker restart or container recreation. Local durability uses the existing Azurite
data volume; removing that volume removes the backlog.

A renewable blob lease permits only one replica to advance a pipeline checkpoint at
a time. Uploaded snapshots whose initial checkpoint write was interrupted are
discovered and recovered. The cursor advances only after successful handling;
dependency failures and unfinished dedup claims leave the record pending for retry.
If the snapshot upload fails, the running worker retains the fetched records in
memory and retries staging rather than replacing them with another source poll.
Restart durability begins once the snapshot upload has completed; a crash during a
source fetch or before any successful upload still depends on the provider retaining
those records for a later poll.
Rejected or governance-blocked records are retained with their payload and reason
under the backlog's `rejected/` prefix before the cursor advances. Completed source
snapshots are removed only after the final cursor is persisted.

Delivery is **at least once**, not exactly once: a crash before the cycle checkpoint
can replay its already-handled records. Committed dedup keys suppress those replays
while their TTL remains valid; an unfinished claim is not treated as a completed
record. Existing source-specific dedup TTLs are unchanged. Rejected records are
retained for operational review and need a separately agreed retention policy.

Successful backlog cycles are separated by a one-second yield; source polling waits
for the backlog to drain and then uses the configured poll interval. Failed records
retry after the poll interval rather than spinning. This bounds processing per cycle,
not source download size: adapters still fetch a full snapshot, cached in memory
while it drains. Worker startup fails explicitly if `STORAGE_ACCOUNT_NAME` is absent
rather than silently downgrade durability. Directly constructed pipelines used by
tests or other callers can omit a backlog store; those use an in-memory backlog only.

Rolling metrics retain their existing one-hour windows. Expired entries are removed
from the oldest end of each deque without scanning or rebuilding the retained history.

## Related Pages

- [SECTOR-01 — Multi-Jurisdiction Tenancy](multi-jurisdiction-tenancy.md)
- [SECTOR-03 — Integration-Point Map](integration-point-map.md)
- [SECTOR-04 — Jurisdiction-Filter Behaviour](jurisdiction-filter.md)
- [Architecture known gaps](../known-gaps.md)
