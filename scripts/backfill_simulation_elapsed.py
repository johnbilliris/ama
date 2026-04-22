"""Backfill elapsed-time fields on existing simulation_tenant documents in Cosmos DB.

Sets elapsed_seconds to 0.0 on documents that don't have it, and removes
obsolete fields (last_resumed_at, paused_at, current_elapsed_seconds)
that were replaced by the UI-driven elapsed time model.

Usage:
    COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/ python scripts/backfill_simulation_elapsed.py

Set DRY_RUN=1 to preview changes without writing.
"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OBSOLETE_FIELDS = ("last_resumed_at", "paused_at", "current_elapsed_seconds")


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

    updated = 0
    skipped = 0

    for doc in items:
        tenant_id = doc.get("tenant_id", doc.get("id", "unknown"))
        changed = False

        if "elapsed_seconds" not in doc:
            doc["elapsed_seconds"] = 0.0
            changed = True

        for field in OBSOLETE_FIELDS:
            if field in doc:
                del doc[field]
                changed = True

        if not changed:
            logger.info("SKIP %s — already up to date", tenant_id)
            skipped += 1
            continue

        if dry_run:
            logger.info("WOULD UPDATE %s", tenant_id)
        else:
            container.upsert_item(doc)
            logger.info("UPDATED %s", tenant_id)
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
