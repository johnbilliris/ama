import json
import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Azure Blob Storage helper for raw payloads, binary assets, and audit trails."""

    def __init__(self, blob_service_client: Any = None, container_prefix: str = ""):
        self._client = blob_service_client
        self._container_prefix = container_prefix
        self._local_store: dict[str, bytes] = {}
        self._local_append_store: dict[str, bytearray] = {}

    async def store_raw_payload(
        self,
        data_source_id: str,
        signal_id: str,
        payload: dict[str, Any] | bytes,
        file_format: str = "json",
    ) -> str:
        now = datetime.now(UTC)
        date_str = now.strftime("%Y-%m-%d")
        safe_source = quote(str(data_source_id), safe="")
        blob_path = f"raw-payloads/live/{safe_source}/{date_str}/{signal_id}.{file_format}"

        data = json.dumps(payload, default=str).encode("utf-8") if isinstance(payload, dict) else payload
        await self._upload(blob_path, data)
        return blob_path

    async def store_binary_asset(
        self,
        incident_id: str | None,
        data_source_id: str,
        timestamp: str,
        binary_data: bytes,
        file_format: str = "png",
    ) -> str:
        if incident_id:
            blob_path = f"binary-assets/{incident_id}/{data_source_id}/{timestamp}.{file_format}"
        else:
            blob_path = f"binary-assets/_on-demand/{data_source_id}/{timestamp}.{file_format}"

        await self._upload(blob_path, binary_data)
        return blob_path

    async def store_simulation_payload(
        self,
        simulation_run_id: str,
        data_source_id: str,
        signal_id: str,
        payload: dict[str, Any] | bytes,
        file_format: str = "json",
    ) -> str:
        safe_source = quote(str(data_source_id), safe="")
        blob_path = f"raw-payloads/simulation/{simulation_run_id}/{safe_source}/{signal_id}.{file_format}"
        data = json.dumps(payload, default=str).encode("utf-8") if isinstance(payload, dict) else payload
        await self._upload(blob_path, data)
        return blob_path

    async def _upload(self, blob_path: str, data: bytes) -> None:
        if self._client:
            container_name = blob_path.split("/")[0]
            blob_name = "/".join(blob_path.split("/")[1:])
            container_client = self._client.get_container_client(container_name)
            await container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        else:
            self._local_store[blob_path] = data

    async def append_line(self, blob_path: str, data: bytes) -> None:
        if self._client:
            from azure.core.exceptions import ResourceExistsError
            from azure.storage.blob import BlobClient

            container_name, blob_name = blob_path.split("/", 1)
            container_client = self._client.get_container_client(container_name)
            blob_client: BlobClient = container_client.get_blob_client(blob_name)

            try:
                blob_client.create_append_blob()
            except ResourceExistsError:
                pass

            blob_client.append_block(data)
            return

        existing = self._local_append_store.setdefault(blob_path, bytearray())
        existing.extend(data)

    async def retrieve(self, blob_path: str) -> bytes | None:
        if self._client:
            container_name = blob_path.split("/")[0]
            blob_name = "/".join(blob_path.split("/")[1:])
            container_client = self._client.get_container_client(container_name)
            blob_data = await container_client.download_blob(blob_name)
            return await blob_data.readall()
        if blob_path in self._local_append_store:
            return bytes(self._local_append_store[blob_path])
        return self._local_store.get(blob_path)
