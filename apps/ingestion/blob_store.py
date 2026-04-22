"""Raw payload blob archival for ingestion pipelines."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class RawPayloadBlobStore:
    """Archives raw ingestion payloads into Azure Blob Storage (raw-payloads container).

    Uses ``DefaultAzureCredential`` (managed identity in Azure, Azure CLI locally).
    """

    def __init__(self, account_name: str, container_name: str = "raw-payloads") -> None:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{account_name}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        self._client = BlobServiceClient(account_url, credential=credential)
        self._container = self._client.get_container_client(container_name)

    async def store_raw_payload(
        self,
        *,
        data_source_id: str,
        signal_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Store a raw payload blob and return the blob URI."""
        now = datetime.now(UTC)
        blob_name = f"{data_source_id}/{now:%Y/%m/%d}/{signal_id}.json"
        data = json.dumps(payload, default=str).encode()
        self._container.upload_blob(name=blob_name, data=data, overwrite=True)
        uri = f"{self._container.url}/{blob_name}"
        logger.debug("Archived raw payload: %s", uri)
        return uri
