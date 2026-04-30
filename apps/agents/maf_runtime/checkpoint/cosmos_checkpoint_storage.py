"""Cosmos-backed MAF checkpoint storage (T018, ADR-033-02).

Per ADR-033-02 we use the SDK-provided ``agent_framework_azure_cosmos.CosmosCheckpointStorage``
directly instead of subclassing ``CheckpointStorage`` ourselves. This module is the
thin factory that:

1. Constructs the SDK class with managed identity (``DefaultAzureCredential``) against
   the ``platform`` Cosmos account, ``checkpoints`` container.
2. Wraps Cosmos write/read failures into our canonical ``CheckpointStoreUnavailableError``
   so the workflow runtime can halt the affected run with a typed error rather than
   proceeding without durability (per spec edge case "Checkpoint store is unavailable").
"""

from __future__ import annotations

import logging
import os
from typing import Any

from agent_framework_azure_cosmos import CosmosCheckpointStorage as _SdkCosmosStorage
from azure.identity import DefaultAzureCredential

from ..errors import CheckpointStoreUnavailableError

logger = logging.getLogger(__name__)


class CheckpointStorageWithErrorWrapping:
    """Delegate to the SDK's CosmosCheckpointStorage, normalising failures to our error model."""

    def __init__(self, inner: _SdkCosmosStorage) -> None:
        self._inner = inner

    def __getattr__(self, item: str) -> Any:
        # Default-delegate. The wrapping methods below override save/load specifically.
        return getattr(self._inner, item)

    async def save_checkpoint(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return await self._inner.save_checkpoint(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            run_id = kwargs.get("run_id") or (args[0] if args else None)
            raise CheckpointStoreUnavailableError(
                f"Failed to persist checkpoint to Cosmos: {exc}",
                correlation_id="checkpoint-save",
                run_id=str(run_id) if run_id else None,
                details={"error_type": type(exc).__name__},
            ) from exc

    async def load_checkpoint(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return await self._inner.load_checkpoint(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            raise CheckpointStoreUnavailableError(
                f"Failed to load checkpoint from Cosmos: {exc}",
                correlation_id="checkpoint-load",
                details={"error_type": type(exc).__name__},
            ) from exc


def build_checkpoint_storage(
    *,
    endpoint: str | None = None,
    database_name: str = "platform",
    container_name: str = "checkpoints",
    credential: Any | None = None,
) -> CheckpointStorageWithErrorWrapping:
    """Build the production checkpoint storage backed by Cosmos + managed identity."""
    ep = endpoint or os.environ.get("AZURE_COSMOS_ENDPOINT") or os.environ.get("COSMOS_ENDPOINT")
    if not ep:
        raise CheckpointStoreUnavailableError(
            "AZURE_COSMOS_ENDPOINT not set; cannot build CosmosCheckpointStorage.",
            correlation_id="checkpoint-init",
            details={"reason": "missing_endpoint_env"},
        )
    cred = credential or DefaultAzureCredential()
    inner = _SdkCosmosStorage(
        endpoint=ep,
        database_name=database_name,
        container_name=container_name,
        credential=cred,
    )
    logger.info(
        "checkpoint_storage_initialised",
        extra={"endpoint": ep, "database": database_name, "container": container_name},
    )
    return CheckpointStorageWithErrorWrapping(inner)


__all__ = ["CheckpointStorageWithErrorWrapping", "build_checkpoint_storage"]
