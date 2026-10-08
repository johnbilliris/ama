from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

CONTAINER_PARTITION_FIELDS = {
    "kpi_ladder": "kpi_id",
    "kpi_signals": "scenario_id",
    "delta_scorecards": "scenario_id",
    "causal_chains": "capability_id",
    "benchmark_register": "kpi_id",
    "evidence_audit": "audit_id",
    "evidence_audit_dlq": "audit_id",
}
APPEND_ONLY_CONTAINERS = frozenset({"evidence_audit", "evidence_audit_dlq", "kpi_signals"})


class EvidenceContainer(Protocol):
    name: str

    def create_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    def upsert_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]: ...

    def read_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]: ...

    def replace_item(
        self,
        item: str,
        body: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]: ...

    def delete_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> None: ...

    def query_items(
        self,
        query: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        *,
        enable_cross_partition_query: bool = True,
        partition_key: Any | None = None,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> list[dict[str, Any]]: ...

    def all(self) -> list[dict[str, Any]]: ...

    def read_change_feed_page(
        self,
        *,
        continuation: str | None,
        max_item_count: int,
    ) -> tuple[list[dict[str, Any]], str | None]: ...


@dataclass(frozen=True)
class BlobWriteReceipt:
    blob_name: str
    etag: str
    version_id: str | None
    payload_sha256: str
    duplicate: bool = False


class AuditBlobArchive(Protocol):
    def create_json(
        self,
        blob_name: str,
        body: Mapping[str, Any],
        *,
        metadata: Mapping[str, str],
    ) -> BlobWriteReceipt: ...

    def read_json(self, blob_name: str) -> dict[str, Any]: ...

    def list_json(self, prefix: str) -> list[tuple[str, dict[str, Any]]]: ...

    def health(self) -> bool: ...


class InMemoryContainer:
    def __init__(self, name: str, *, append_only: bool = False) -> None:
        self.name = name
        self.append_only = append_only
        self._items: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def upsert_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        del kwargs
        with self._lock:
            item_id = _required_id(body)
            if self.append_only and item_id in self._items:
                raise PermissionError(f"Container {self.name!r} is append-only; use a new id")
            stored = dict(body)
            self._items[item_id] = stored
            return dict(stored)

    def create_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        response_hook = kwargs.pop("response_hook", None)
        with self._lock:
            item_id = _required_id(body)
            if item_id in self._items:
                raise PermissionError(f"Item {item_id!r} already exists")
            stored = dict(body)
            self._items[item_id] = stored
        headers = {
            "etag": f"memory-{item_id}",
            "x-ms-activity-id": f"memory-{item_id}",
            "x-ms-session-token": f"memory:{item_id}",
        }
        if response_hook is not None:
            response_hook(headers, dict(stored))
        return dict(stored)

    def read_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        del partition_key, kwargs
        with self._lock:
            if item not in self._items:
                raise KeyError(item)
            return dict(self._items[item])

    def replace_item(
        self,
        item: str,
        body: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        del kwargs
        if self.append_only:
            raise PermissionError(f"Container {self.name!r} is append-only; replace not allowed")
        with self._lock:
            if item not in self._items:
                raise KeyError(item)
            stored = dict(body)
            self._items[item] = stored
            return dict(stored)

    def delete_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> None:
        del partition_key, kwargs
        if self.append_only:
            raise PermissionError(f"Container {self.name!r} is append-only; delete not allowed")
        with self._lock:
            self._items.pop(item, None)

    def query_items(
        self,
        query: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        *,
        enable_cross_partition_query: bool = True,
        partition_key: Any | None = None,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> list[dict[str, Any]]:
        del query, parameters, enable_cross_partition_query, partition_key
        rows = self.all()
        return [row for row in rows if predicate(row)] if predicate else rows

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(value) for value in self._items.values()]

    def read_change_feed_page(
        self,
        *,
        continuation: str | None,
        max_item_count: int,
    ) -> tuple[list[dict[str, Any]], str | None]:
        start = int(continuation or "0")
        rows = self.all()
        end = min(len(rows), start + max_item_count)
        return rows[start:end], str(end)

    def replace_and_create(
        self,
        replacements: Iterable[tuple[str, dict[str, Any]]],
        created: dict[str, Any],
    ) -> dict[str, Any]:
        if self.append_only:
            raise PermissionError("append-only containers do not support replacement")
        with self._lock:
            snapshot = {key: dict(value) for key, value in self._items.items()}
            try:
                for item_id, body in replacements:
                    if item_id not in self._items:
                        raise KeyError(item_id)
                    self._items[item_id] = dict(body)
                created_id = _required_id(created)
                if created_id in self._items:
                    raise PermissionError(f"Item {created_id!r} already exists")
                self._items[created_id] = dict(created)
            except Exception:
                self._items = snapshot
                raise
            return dict(self._items[created_id])


class CosmosContainerAdapter:
    def __init__(
        self,
        name: str,
        container: Any,
        partition_field: str,
        *,
        append_only: bool = False,
    ) -> None:
        self.name = name
        self._container = container
        self._partition_field = partition_field
        self._append_only = append_only

    def create_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return dict(self._container.create_item(body, **kwargs))

    def upsert_item(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if self._append_only:
            return self.create_item(body, **kwargs)
        return dict(self._container.upsert_item(body, **kwargs))

    def read_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if partition_key is not None:
            return dict(
                self._container.read_item(
                    item=item,
                    partition_key=partition_key,
                    **kwargs,
                )
            )
        rows = list(
            self._container.query_items(
                "SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": item}],
                enable_cross_partition_query=True,
            )
        )
        if not rows:
            raise KeyError(item)
        return dict(rows[0])

    def replace_item(
        self,
        item: str,
        body: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        if self._append_only:
            raise PermissionError(f"Container {self.name!r} is append-only; replace not allowed")
        return dict(self._container.replace_item(item=item, body=body, **kwargs))

    def delete_item(
        self,
        item: str,
        partition_key: Any | None = None,
        **kwargs: Any,
    ) -> None:
        if self._append_only:
            raise PermissionError(f"Container {self.name!r} is append-only; delete not allowed")
        if partition_key is None:
            existing = self.read_item(item)
            partition_key = existing[self._partition_field]
        self._container.delete_item(
            item=item,
            partition_key=partition_key,
            **kwargs,
        )

    def query_items(
        self,
        query: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        *,
        enable_cross_partition_query: bool = True,
        partition_key: Any | None = None,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
    ) -> list[dict[str, Any]]:
        rows = [
            dict(item)
            for item in self._container.query_items(
                query or "SELECT * FROM c",
                parameters=parameters or [],
                enable_cross_partition_query=enable_cross_partition_query,
                partition_key=partition_key,
            )
        ]
        return [row for row in rows if predicate(row)] if predicate else rows

    def all(self) -> list[dict[str, Any]]:
        return self.query_items()

    def read_change_feed_page(
        self,
        *,
        continuation: str | None,
        max_item_count: int,
    ) -> tuple[list[dict[str, Any]], str | None]:
        options: dict[str, Any] = {
            "max_item_count": max_item_count,
            "mode": "LatestVersion",
        }
        if continuation is None:
            options["start_time"] = "Beginning"
        else:
            options["continuation"] = continuation
        pager = self._container.query_items_change_feed(**options)
        pages = pager.by_page()
        try:
            rows = [dict(item) for item in next(pages)]
        except StopIteration:
            return [], continuation
        return rows, getattr(pages, "continuation_token", continuation)


class InMemoryBlobArchive:
    def __init__(self) -> None:
        self._items: dict[str, tuple[bytes, dict[str, str], BlobWriteReceipt]] = {}
        self._lock = threading.RLock()

    def create_json(
        self,
        blob_name: str,
        body: Mapping[str, Any],
        *,
        metadata: Mapping[str, str],
    ) -> BlobWriteReceipt:
        payload = _canonical_json_bytes(body)
        payload_hash = hashlib.sha256(payload).hexdigest()
        with self._lock:
            existing = self._items.get(blob_name)
            if existing is not None:
                if hashlib.sha256(existing[0]).hexdigest() != payload_hash:
                    raise RuntimeError(f"immutable blob conflict for {blob_name}: payload hash mismatch")
                return BlobWriteReceipt(
                    blob_name=blob_name,
                    etag=existing[2].etag,
                    version_id=existing[2].version_id,
                    payload_sha256=payload_hash,
                    duplicate=True,
                )
            receipt = BlobWriteReceipt(
                blob_name=blob_name,
                etag=f'"memory-{payload_hash[:16]}"',
                version_id=None,
                payload_sha256=payload_hash,
            )
            self._items[blob_name] = (payload, dict(metadata), receipt)
            return receipt

    def read_json(self, blob_name: str) -> dict[str, Any]:
        with self._lock:
            try:
                payload = self._items[blob_name][0]
            except KeyError as exc:
                raise KeyError(blob_name) from exc
        return json.loads(payload)

    def list_json(self, prefix: str) -> list[tuple[str, dict[str, Any]]]:
        with self._lock:
            names = sorted(name for name in self._items if name.startswith(prefix))
        return [(name, self.read_json(name)) for name in names]

    def health(self) -> bool:
        return True


class AzureBlobArchive:
    def __init__(self, container_client: Any) -> None:
        self._container = container_client

    def create_json(
        self,
        blob_name: str,
        body: Mapping[str, Any],
        *,
        metadata: Mapping[str, str],
    ) -> BlobWriteReceipt:
        payload = _canonical_json_bytes(body)
        payload_hash = hashlib.sha256(payload).hexdigest()
        blob = self._container.get_blob_client(blob_name)
        from azure.storage.blob import ContentSettings

        try:
            result = blob.upload_blob(
                payload,
                overwrite=False,
                metadata={**metadata, "payload_sha256": payload_hash},
                content_settings=ContentSettings(content_type="application/json"),
            )
            return BlobWriteReceipt(
                blob_name=blob_name,
                etag=str(result.get("etag", "")),
                version_id=result.get("version_id"),
                payload_sha256=payload_hash,
            )
        except Exception as exc:
            if getattr(exc, "status_code", None) != 409:
                raise
            existing_payload = blob.download_blob().readall()
            if hashlib.sha256(existing_payload).hexdigest() != payload_hash:
                raise RuntimeError(f"immutable blob conflict for {blob_name}: payload hash mismatch") from exc
            properties = blob.get_blob_properties()
            return BlobWriteReceipt(
                blob_name=blob_name,
                etag=str(properties.etag),
                version_id=getattr(properties, "version_id", None),
                payload_sha256=payload_hash,
                duplicate=True,
            )

    def read_json(self, blob_name: str) -> dict[str, Any]:
        return json.loads(self._container.get_blob_client(blob_name).download_blob().readall())

    def list_json(self, prefix: str) -> list[tuple[str, dict[str, Any]]]:
        rows = []
        for blob in self._container.list_blobs(name_starts_with=prefix):
            name = blob["name"] if isinstance(blob, dict) else blob.name
            rows.append((name, self.read_json(name)))
        return rows

    def health(self) -> bool:
        properties = self._container.get_container_properties()
        policy = getattr(properties, "immutability_policy", None)
        mode = str(getattr(policy, "policy_mode", "")).lower()
        expiry = getattr(policy, "expiry_time", None)
        return bool(
            getattr(properties, "has_immutability_policy", False)
            and mode == "locked"
            and isinstance(expiry, datetime)
            and expiry.tzinfo is not None
            and expiry.astimezone(UTC) >= datetime.now(UTC) + timedelta(days=2554)
        )


class EvidenceClientRegistry:
    CONTAINER_NAMES = tuple(CONTAINER_PARTITION_FIELDS)
    APPEND_ONLY = APPEND_ONLY_CONTAINERS

    def __init__(
        self,
        containers: Mapping[str, EvidenceContainer] | None = None,
        *,
        blob_archive: AuditBlobArchive | None = None,
        cosmos_client: Any | None = None,
        blob_service_client: Any | None = None,
        telemetry_configured: bool = True,
    ) -> None:
        self._containers = dict(containers or _memory_containers())
        self.blob_archive = blob_archive or InMemoryBlobArchive()
        self._cosmos_client = cosmos_client
        self._blob_service_client = blob_service_client
        self.telemetry_configured = telemetry_configured

    @classmethod
    def from_environment(cls) -> EvidenceClientRegistry:
        if os.environ.get("AMA_TEST_MODE") == "1":
            return cls()

        cosmos_url = cosmos_endpoint()
        blob_url = blob_endpoint()
        app_insights = os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING",
            "",
        ).strip()
        missing = [
            name
            for name, value in (
                ("Cosmos endpoint", cosmos_url),
                ("Blob endpoint", blob_url),
                ("Application Insights connection string", app_insights),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "FR-042/FR-029: production evidence clients require "
                + ", ".join(missing)
                + "; refusing in-memory fallback"
            )

        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        credential = DefaultAzureCredential()
        cosmos_client = CosmosClient(
            cosmos_url,
            credential=credential,
            connection_timeout=4,
            request_timeout=4,
        )
        database_name = os.environ.get("AMA_EVIDENCE_COSMOS_DATABASE", "ama")
        database = cosmos_client.get_database_client(database_name)
        containers = {
            name: CosmosContainerAdapter(
                name,
                database.get_container_client(name),
                partition_field,
                append_only=name in APPEND_ONLY_CONTAINERS,
            )
            for name, partition_field in CONTAINER_PARTITION_FIELDS.items()
        }
        blob_service = BlobServiceClient(
            account_url=blob_url,
            credential=credential,
            connection_timeout=4,
            read_timeout=4,
        )
        blob_container_name = os.environ.get(
            "AMA_EVIDENCE_BLOB_CONTAINER",
            "evidence-audit-cold",
        )
        archive = AzureBlobArchive(blob_service.get_container_client(blob_container_name))
        return cls(
            containers,
            blob_archive=archive,
            cosmos_client=cosmos_client,
            blob_service_client=blob_service,
            telemetry_configured=True,
        )

    def get(self, name: str) -> EvidenceContainer:
        try:
            return self._containers[name]
        except KeyError as exc:
            raise KeyError(f"unknown evidence container: {name}") from exc

    def reset(self) -> None:
        if os.environ.get("AMA_TEST_MODE") != "1":
            raise RuntimeError("evidence registry reset is test-only")
        self._containers = _memory_containers()
        self.blob_archive = InMemoryBlobArchive()

    def health(self) -> dict[str, bool]:
        checks: dict[str, bool] = {}
        for name, container in self._containers.items():
            try:
                container.query_items(predicate=lambda _: False)
                checks[name] = True
            except Exception:
                checks[name] = False
        return checks

    def close(self) -> None:
        for client in (self._cosmos_client, self._blob_service_client):
            close = getattr(client, "close", None)
            if callable(close):
                close()


_registry: EvidenceClientRegistry | None = None
_registry_lock = threading.RLock()


def initialize_registry() -> EvidenceClientRegistry:
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = EvidenceClientRegistry.from_environment()
        return _registry


def get_registry() -> EvidenceClientRegistry:
    return initialize_registry()


def close_registry() -> None:
    global _registry
    with _registry_lock:
        if _registry is not None:
            _registry.close()
            _registry = None


def reset_registry() -> None:
    global _registry
    if os.environ.get("AMA_TEST_MODE") != "1" and "PYTEST_CURRENT_TEST" not in os.environ:
        raise RuntimeError("evidence registry reset is test-only")
    with _registry_lock:
        _registry = EvidenceClientRegistry()


def cosmos_endpoint() -> str:
    return (
        os.environ.get("AMA_EVIDENCE_COSMOS_ENDPOINT")
        or os.environ.get("COSMOS_ENDPOINT")
        or os.environ.get("AZURE_COSMOS_ENDPOINT")
        or ""
    ).strip()


def blob_endpoint() -> str:
    explicit = os.environ.get("AMA_EVIDENCE_BLOB_ENDPOINT", "").strip()
    if explicit:
        return explicit
    account_name = os.environ.get("AMA_EVIDENCE_STORAGE_ACCOUNT_NAME", "").strip()
    return f"https://{account_name}.blob.core.windows.net" if account_name else ""


def _memory_containers() -> dict[str, EvidenceContainer]:
    return {
        name: InMemoryContainer(
            name,
            append_only=name in APPEND_ONLY_CONTAINERS,
        )
        for name in CONTAINER_PARTITION_FIELDS
    }


def _required_id(body: Mapping[str, Any]) -> str:
    item_id = str(body.get("id") or "")
    if not item_id:
        raise ValueError("evidence documents require a non-empty id")
    return item_id


def _canonical_json_bytes(body: Mapping[str, Any]) -> bytes:
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
