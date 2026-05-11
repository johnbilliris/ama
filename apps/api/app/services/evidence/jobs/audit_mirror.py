"""Change-feed → Blob cold-archive mirror job (T-AMD-04, FR-040)."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

CHECKPOINT_KEY = "audit_mirror_checkpoint"


async def run_mirror_loop(*, registry, blob_client=None, batch_size: int = 100) -> None:
    """Continuously mirror evidence_audit change-feed to Blob cold archive."""
    audit_container = registry.get("evidence_audit")
    dlq_container = registry.get("evidence_audit_dlq")

    while True:
        try:
            items = audit_container.query_items(predicate=lambda x: not x.get("archived_to_blob", False))
            for item in items[:batch_size]:
                try:
                    _mirror_item(item, blob_client=blob_client)
                    item["archived_to_blob"] = True
                    try:
                        audit_container.upsert_item(item)
                    except Exception:
                        pass
                except Exception as exc:
                    logger.error("Mirror failed for %s: %s", item.get("id"), exc)
                    dlq_container.create_item(
                        {
                            "id": f"dlq-{item.get('id', 'unknown')}-{datetime.now(UTC).timestamp()}",
                            "audit_id": item.get("audit_id", ""),
                            "original_id": item.get("id", ""),
                            "error": str(exc),
                            "failed_at": datetime.now(UTC).isoformat(),
                        }
                    )
        except Exception as exc:
            logger.error("Mirror loop error: %s", exc)
        await asyncio.sleep(int(os.environ.get("AUDIT_MIRROR_INTERVAL_S", "30")))


def _mirror_item(item: dict, *, blob_client=None) -> None:
    """Write item to Blob cold archive (or log if no blob client)."""
    if blob_client is None:
        logger.debug("No blob client configured; skipping mirror for %s", item.get("id"))
        return
    blob_name = f"audit/{item.get('audit_id', 'unknown')}/{item.get('id', 'unknown')}.json"
    blob_client.upload_blob(blob_name, json.dumps(item), overwrite=True)
