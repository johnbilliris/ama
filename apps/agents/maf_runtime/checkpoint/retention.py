"""Checkpoint retention helper (T019, FR-012a).

The ``checkpoints`` Cosmos container has ``defaultTtl=2592000`` (30 days) but
no per-document TTL set on creation. This helper re-stamps every checkpoint
document for a run with ``_ttl=2592000`` once the parent run reaches a terminal
state, starting the 30-day countdown from the moment of terminality (not the
moment the checkpoint was written).

Active runs therefore retain checkpoints indefinitely until they terminate.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from ..errors import CheckpointStoreUnavailableError

logger = logging.getLogger(__name__)

_TTL_SECONDS_DEFAULT = 30 * 24 * 60 * 60  # 30 days


def _build_container() -> Any | None:
    endpoint = os.environ.get("AZURE_COSMOS_ENDPOINT") or os.environ.get("COSMOS_ENDPOINT")
    if not endpoint:
        return None
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential

        client = CosmosClient(endpoint, credential=DefaultAzureCredential())
        db = client.get_database_client(os.environ.get("AZURE_COSMOS_DATABASE_NAME", "disaster-hub"))
        return db.get_container_client(os.environ.get("MAF_CHECKPOINT_CONTAINER", "checkpoints"))
    except Exception:  # noqa: BLE001
        logger.exception("Failed to init Cosmos for checkpoint retention stamp")
        return None


def stamp_terminal(run_id: str, *, ttl_seconds: int = _TTL_SECONDS_DEFAULT) -> int:
    """Mark every checkpoint for *run_id* as TTL-eligible (FR-012a).

    Returns the number of checkpoint documents updated. Callers (typically the
    workflow runtime when a run transitions to a terminal state) treat any
    Cosmos failure here as non-fatal — the parent run is already terminal — but
    log it loudly so retention drift can be detected by the reconciliation job.
    """
    container = _build_container()
    if container is None:
        logger.warning("stamp_terminal(%s): no Cosmos container; skipping (in-memory mode)", run_id)
        return 0

    updated = 0
    try:
        items = list(
            container.query_items(
                query="SELECT * FROM c WHERE c.run_id=@r",
                parameters=[{"name": "@r", "value": run_id}],
                partition_key=run_id,
            )
        )
        for doc in items:
            doc["ttl"] = int(ttl_seconds)
            container.replace_item(item=doc["id"], body=doc)
            updated += 1
    except Exception as exc:  # noqa: BLE001
        # Surface as our typed error so the caller can decide; default policy is log + continue.
        raise CheckpointStoreUnavailableError(
            f"Failed to stamp terminal TTL on checkpoints for run {run_id}: {exc}",
            correlation_id="checkpoint-retention",
            run_id=run_id,
        ) from exc
    logger.info("stamp_terminal: updated %d checkpoints for run %s", updated, run_id)
    return updated


__all__ = ["stamp_terminal"]
