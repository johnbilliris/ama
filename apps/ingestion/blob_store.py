"""Raw payload blob archival for ingestion pipelines."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

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
        payload: dict[str, Any] | bytes,
        file_format: str = "json",
    ) -> str:
        """Store a raw payload blob and return the blob URI."""
        now = datetime.now(UTC)
        safe_source = quote(str(data_source_id), safe="")
        blob_name = f"live/{safe_source}/{now:%Y-%m-%d}/{signal_id}.{file_format}"
        data = json.dumps(payload, default=str).encode() if isinstance(payload, dict) else payload
        await asyncio.to_thread(self._container.upload_blob, name=blob_name, data=data, overwrite=True)
        uri = f"{self._container.url}/{blob_name}"
        logger.debug("Archived raw payload: %s", uri)
        return uri

    async def store_simulation_payload(
        self,
        *,
        simulation_run_id: str,
        data_source_id: str,
        signal_id: str,
        payload: dict[str, Any] | bytes,
        file_format: str = "json",
    ) -> str:
        now = datetime.now(UTC)
        safe_source = quote(str(data_source_id), safe="")
        blob_name = f"simulation/{simulation_run_id}/{safe_source}/{now:%Y-%m-%d}/{signal_id}.{file_format}"
        data = json.dumps(payload, default=str).encode() if isinstance(payload, dict) else payload
        await asyncio.to_thread(self._container.upload_blob, name=blob_name, data=data, overwrite=True)
        uri = f"{self._container.url}/{blob_name}"
        logger.debug("Archived simulation raw payload: %s", uri)
        return uri

    async def append_line(self, blob_path: str, data: bytes) -> None:
        from azure.core.exceptions import HttpResponseError, ResourceExistsError

        container_name, blob_name = blob_path.split("/", 1)
        container_client = self._client.get_container_client(container_name)
        append_blob = container_client.get_blob_client(blob_name).get_append_blob_client()

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                if attempt == 0:
                    try:
                        await asyncio.to_thread(append_blob.create_append_blob)
                    except ResourceExistsError:
                        pass
                await asyncio.to_thread(append_blob.append_block, data)
                return
            except HttpResponseError as exc:
                last_error = exc
                await asyncio.sleep(0.1 * (attempt + 1))

        if last_error is not None:
            raise last_error
