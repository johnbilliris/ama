"""Backfill elapsed-time fields on existing simulation_tenant documents in Cosmos DB.

Adds three fields with safe defaults:
  - elapsed_seconds: 0.0
  - last_resumed_at: datetime.now(UTC) for Active tenants, null otherwise
  - paused_at: datetime.now(UTC) for Paused tenants, null otherwise

Usage:
    COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/ python scripts/backfill_simulation_elapsed.py

Set DRY_RUN=1 to preview changes without writing.
"""

import logging
import os
import sys
from datetime import UTC, datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    if not endpoint:
        logger.error("COSMOS_ENDPOINT environment variable is required")
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "").strip() in ("1", "true", "yes")
    if dry_run:
        logger.info("DRY_RUN mode — no documents will be modified")

    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    db = client.get_database_client("disaster-hub")
    container = db.get_container_client("simulation")

    query = "SELECT * FROM c WHERE c.document_type = 'simulation_tenant'"
    items = list(container.query_items(query, enable_cross_partition_query=True))
    logger.info("Found %d simulation_tenant documents", len(items))

    now = datetime.now(UTC)
    updated = 0
    skipped = 0

    for doc in items:
        tenant_id = doc.get("tenant_id", doc.get("id", "unknown"))
        status = doc.get("status", "")

        if "elapsed_seconds" in doc:
            logger.info("SKIP %s — already has elapsed_seconds", tenant_id)
            skipped += 1
            continue

        doc["elapsed_seconds"] = 0.0

        if status == "Active":
            doc["last_resumed_at"] = now.isoformat()
            doc["paused_at"] = None
        elif status == "Paused":
            doc["last_resumed_at"] = None
            doc["paused_at"] = now.isoformat()
        else:
            doc["last_resumed_at"] = None
            doc["paused_at"] = None

        if dry_run:
            logger.info(
                "WOULD UPDATE %s (status=%s, last_resumed_at=%s, paused_at=%s)",
                tenant_id,
                status,
                doc["last_resumed_at"],
                doc["paused_at"],
            )
        else:
            container.upsert_item(doc)
            logger.info("UPDATED %s (status=%s)", tenant_id, status)
        updated += 1

    logger.info(
        "Done. updated=%d skipped=%d total=%d dry_run=%s",
        updated,
        skipped,
        len(items),
        dry_run,
    )


if __name__ == "__main__":
    main()
