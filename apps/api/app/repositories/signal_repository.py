import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.core.async_io import run_blocking
from app.core.tenant_context import get_current_tenant

from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.repositories.signal_wire import to_signal_document

logger = logging.getLogger(__name__)


def _build_cosmos_client() -> Any:
    """Build a CosmosClient from the ``COSMOS_ENDPOINT`` env var."""
    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class SignalRepository:
    """Tenant-scoped signal read/write operations against the ``signals`` Cosmos DB container.

    When ``COSMOS_ENDPOINT`` is set the repository talks to Cosmos DB.
    Otherwise it falls back to an in-memory dict so that unit / contract
    tests keep working without infrastructure.
    """

    def __init__(
        self,
        cosmos_client: Any = None,
        database_name: str = "disaster-hub",
        tenant_id: str | None = None,
        write_guard: Any = None,
    ):
        self._db_name = database_name
        self._container_name = "signals"
        self._tenant_id = tenant_id
        self._write_guard = write_guard
        self._in_memory: dict[str, dict[str, Any]] = {}
        self._init_error: str | None = None
        environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
        is_production = environment in {"production", "staging"}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                if is_production:
                    raise RuntimeError("SignalRepository failed to initialise Cosmos client") from exc
                logger.warning(
                    "SignalRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._init_error = str(exc)
                self._client = None
        else:
            if is_production:
                raise RuntimeError("SignalRepository requires COSMOS_ENDPOINT in production/staging")
            self._client = None

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    def bind(self, tenant_id: str) -> "SignalRepository":
        bound = object.__new__(SignalRepository)
        bound._db_name = self._db_name
        bound._container_name = self._container_name
        bound._tenant_id = tenant_id
        bound._write_guard = self._write_guard
        bound._in_memory = self._in_memory
        bound._init_error = self._init_error
        bound._client = self._client
        return bound

    async def create_signal(self, tenant_id: str, signal_doc: dict[str, Any]) -> dict[str, Any]:
        self._raise_if_unavailable_for_mutation()
        tenant_id = self._resolve_scope(tenant_id)
        signal_doc["scope"] = tenant_id
        storage_bytes = len(json.dumps(signal_doc, default=str, separators=(",", ":")).encode("utf-8"))
        budget_reserved = await self._reserve_write_budget(tenant_id, storage_bytes)
        live_reserved = await self._reserve_live_capacity(tenant_id)
        container = self._get_container()
        try:
            if container:
                await run_blocking(container.upsert_item, signal_doc)
            else:
                key = f"{tenant_id}:{signal_doc.get('signal_id', signal_doc.get('id', ''))}"
                self._in_memory[key] = signal_doc
        except Exception:
            if budget_reserved:
                await self._write_guard.release_write(tenant_id, "signal", storage_bytes)
            raise
        finally:
            if live_reserved:
                await self._write_guard.release_live_capacity(1)
        return signal_doc

    async def save(self, signal: Signal, scope: str | None = None) -> None:
        """Persist a domain signal with deterministic partition metadata."""
        self._raise_if_unavailable_for_mutation()
        scope = self._resolve_scope(scope)
        signal_doc = to_signal_document(signal, scope)
        storage_bytes = len(json.dumps(signal_doc, default=str, separators=(",", ":")).encode("utf-8"))
        budget_reserved = await self._reserve_write_budget(scope, storage_bytes)
        live_reserved = await self._reserve_live_capacity(scope)

        container = self._get_container()
        try:
            if container:
                await run_blocking(container.upsert_item, signal_doc)
                return
            self._in_memory[f"{scope}:{signal.signal_id}"] = signal_doc
        except Exception:
            if budget_reserved:
                await self._write_guard.release_write(scope, "signal", storage_bytes)
            raise
        finally:
            if live_reserved:
                await self._write_guard.release_live_capacity(1)

    async def get_by_hpk(
        self,
        *,
        signal_id: str,
        scope: str,
        jurisdiction_id: str,
        data_source_id: str,
    ) -> dict[str, Any] | None:
        scope = self._resolve_scope(scope)
        container = self._get_container()
        if container:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                doc = await run_blocking(
                    container.read_item,
                    item=signal_id,
                    partition_key=[scope, jurisdiction_id, data_source_id],
                )
            except CosmosResourceNotFoundError:
                return None
            return doc

        doc = self._in_memory.get(f"{scope}:{signal_id}")
        if doc is None:
            return None
        if str(doc.get("jurisdictionId", doc.get("jurisdiction_id", "national"))) != jurisdiction_id:
            return None
        if str(doc.get("dataSourceId", doc.get("data_source_id", ""))) != data_source_id:
            return None
        return doc

    async def get_signal(
        self,
        tenant_id: str,
        signal_id: str,
        partition_key: str | None = None,
    ) -> dict[str, Any] | None:
        tenant_id = self._resolve_scope(tenant_id)
        container = self._get_container()
        if container:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                pk: list[str] | str | None
                if partition_key is None:
                    pk = None
                elif isinstance(partition_key, str):
                    pk = partition_key.split("/", 2)
                else:
                    pk = partition_key
                doc = await run_blocking(container.read_item, signal_id, partition_key=pk)
                if doc.get("scope") != tenant_id:
                    return None
                return doc
            except CosmosResourceNotFoundError:
                return None
        return self._in_memory.get(f"{tenant_id}:{signal_id}")

    async def list_by_tenant(
        self,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        *,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        allowed_data_source_ids: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        tenant_id = self._resolve_scope(tenant_id)
        container = self._get_container()
        if container:
            conditions = ["c.scope = @scope"]
            params: list[dict[str, object]] = [{"name": "@scope", "value": tenant_id}]
            if owning_agency_id:
                conditions.append("c.owningAgencyId = @owningAgencyId")
                params.append({"name": "@owningAgencyId", "value": owning_agency_id})
            if allowed_jurisdictions:
                conditions.append("ARRAY_CONTAINS(@jurisdictions, c.jurisdictionId)")
                params.append({"name": "@jurisdictions", "value": sorted(allowed_jurisdictions)})
            if allowed_data_source_ids:
                conditions.append("ARRAY_CONTAINS(@dataSources, c.dataSourceId)")
                params.append({"name": "@dataSources", "value": sorted(allowed_data_source_ids)})

            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c._ts DESC OFFSET @offset LIMIT @limit"
            params.extend(
                [
                    {"name": "@offset", "value": offset},
                    {"name": "@limit", "value": limit},
                ]
            )
            items = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            count_query = f"SELECT VALUE COUNT(1) FROM c WHERE {' AND '.join(conditions)}"
            count_params = params[: len(params) - 2] if len(params) >= 2 else params
            total = (
                await run_blocking(
                    lambda: list(
                        container.query_items(
                            count_query,
                            parameters=count_params,
                            enable_cross_partition_query=True,
                        )
                    )
                )
            )[0]
            return items, total
        tenant_signals = []
        for key, value in self._in_memory.items():
            if not key.startswith(f"{tenant_id}:"):
                continue
            if owning_agency_id and value.get("owningAgencyId") != owning_agency_id:
                continue
            if allowed_jurisdictions and value.get("jurisdictionId") not in allowed_jurisdictions:
                continue
            if allowed_data_source_ids and value.get("dataSourceId") not in allowed_data_source_ids:
                continue
            tenant_signals.append(value)
        total = len(tenant_signals)
        return tenant_signals[offset : offset + limit], total

    async def count_by_tenant(self, tenant_id: str) -> int:
        tenant_id = self._resolve_scope(tenant_id)
        container = self._get_container()
        if container:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.scope = @scope"
            return (
                await run_blocking(
                    lambda: list(
                        container.query_items(
                            query,
                            parameters=[{"name": "@scope", "value": tenant_id}],
                            enable_cross_partition_query=True,
                        )
                    )
                )
            )[0]
        return sum(1 for k in self._in_memory if k.startswith(f"{tenant_id}:"))

    async def delete_by_tenant(self, tenant_id: str) -> int:
        tenant_id = self._resolve_scope(tenant_id)
        container = self._get_container()
        if container:
            query = "SELECT c.id, c.scope, c.jurisdictionId, c.dataSourceId FROM c WHERE c.scope = @scope"
            documents = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@scope", "value": tenant_id}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            for document in documents:
                await run_blocking(
                    container.delete_item,
                    item=document["id"],
                    partition_key=[tenant_id, document["jurisdictionId"], document["dataSourceId"]],
                )
            return len(documents)

        keys = [key for key in self._in_memory if key.startswith(f"{tenant_id}:")]
        for key in keys:
            self._in_memory.pop(key, None)
        return len(keys)

    async def query_unassociated(
        self,
        jurisdiction_id: str,
        since: datetime | None = None,
        *,
        scope: str,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        include_all_jurisdictions: bool = False,
    ) -> list[Signal]:
        scope = self._resolve_scope(scope)
        cutoff = since or datetime.min.replace(tzinfo=UTC)
        container = self._get_container()
        if container:
            conditions = ["c.scope = @scope", "c.incident_id = null", "c.occurred_at >= @since"]
            params: list[dict[str, Any]] = [
                {"name": "@scope", "value": scope},
                {"name": "@since", "value": cutoff.isoformat()},
            ]
            if owning_agency_id:
                conditions.append("c.owningAgencyId = @owningAgencyId")
                params.append({"name": "@owningAgencyId", "value": owning_agency_id})
            if allowed_jurisdictions:
                conditions.append("ARRAY_CONTAINS(@allowedJurisdictions, c.jurisdictionId)")
                params.append({"name": "@allowedJurisdictions", "value": sorted(allowed_jurisdictions)})
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)}"
            rows = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            results: list[Signal] = []
            for row in rows:
                jid = str(row.get("jurisdictionId", row.get("jurisdiction_id", ""))).lower()
                if jid == jurisdiction_id.lower() or (
                    jurisdiction_id.lower() == "national" and include_all_jurisdictions
                ):
                    results.append(Signal(**row))
            return results

        matches: list[Signal] = []
        for key, value in self._in_memory.items():
            if not key.startswith(f"{scope}:"):
                continue
            if value.get("incident_id") is not None:
                continue
            if owning_agency_id and value.get("owningAgencyId") != owning_agency_id:
                continue
            jid = str(value.get("jurisdictionId", value.get("jurisdiction_id", ""))).lower()
            if allowed_jurisdictions and jid not in {j.lower() for j in allowed_jurisdictions}:
                continue
            if not (
                jid == jurisdiction_id.lower() or (jurisdiction_id.lower() == "national" and include_all_jurisdictions)
            ):
                continue
            occurred_at = datetime.fromisoformat(str(value.get("occurred_at", "")).replace("Z", "+00:00"))
            if occurred_at < cutoff:
                continue
            matches.append(Signal(**value))
        return matches

    async def update_incident_id(
        self,
        signal_id: str,
        incident_id: str,
        *,
        scope: str,
        expected_incident_id: str | None = None,
    ) -> bool:
        scope = self._resolve_scope(scope)
        container = self._get_container()
        if container:
            conditions = ["c.id = @id", "c.scope = @scope"]
            params: list[dict[str, Any]] = [
                {"name": "@id", "value": signal_id},
                {"name": "@scope", "value": scope},
            ]
            if expected_incident_id is None:
                conditions.append("c.incident_id = null")
            else:
                conditions.append("c.incident_id = @expectedIncidentId")
                params.append({"name": "@expectedIncidentId", "value": expected_incident_id})
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)}"
            docs = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            if not docs:
                return False
            doc = docs[0]
            doc["incident_id"] = incident_id
            kwargs: dict[str, Any] = {}
            if doc.get("_etag"):
                kwargs["etag"] = doc.get("_etag")
                kwargs["match_condition"] = "IfNotModified"
            try:
                await run_blocking(container.replace_item, item=doc["id"], body=doc, **kwargs)
            except TypeError:
                await run_blocking(container.replace_item, item=doc["id"], body=doc)
            return True

        key = f"{scope}:{signal_id}"
        if key not in self._in_memory:
            return False
        if self._in_memory[key].get("incident_id") != expected_incident_id:
            return False
        self._in_memory[key]["incident_id"] = incident_id
        return True

    async def update_validation_decision(
        self,
        *,
        signal_id: str,
        scope: str,
        validation_status: str,
        rationale: str,
        decision_id: str,
        decision: str,
    ) -> bool:
        scope = self._resolve_scope(scope)
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.id = @id AND c.scope = @scope"
            params = [
                {"name": "@id", "value": signal_id},
                {"name": "@scope", "value": scope},
            ]
            docs = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            if not docs:
                return False
            doc = docs[0]
            doc["validation_status"] = validation_status
            doc["validationStatus"] = validation_status
            provenance = doc.get("provenance")
            if not isinstance(provenance, dict):
                provenance = {}
            provenance["tier2DecisionId"] = decision_id
            provenance["tier2Decision"] = decision
            provenance["tier2Rationale"] = rationale
            doc["provenance"] = provenance
            kwargs: dict[str, Any] = {}
            if doc.get("_etag"):
                kwargs["etag"] = doc.get("_etag")
                kwargs["match_condition"] = "IfNotModified"
            try:
                await run_blocking(container.replace_item, item=doc["id"], body=doc, **kwargs)
            except TypeError:
                await run_blocking(container.replace_item, item=doc["id"], body=doc)
            return True

        key = f"{scope}:{signal_id}"
        if key not in self._in_memory:
            return False
        doc = self._in_memory[key]
        doc["validation_status"] = validation_status
        doc["validationStatus"] = validation_status
        provenance = doc.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
        provenance["tier2DecisionId"] = decision_id
        provenance["tier2Decision"] = decision
        provenance["tier2Rationale"] = rationale
        doc["provenance"] = provenance
        self._in_memory[key] = doc
        return True

    async def update_binary_asset_uri(
        self,
        *,
        signal_id: str,
        scope: str,
        source_uri: str,
        stored_uri: str,
    ) -> bool:
        scope = self._resolve_scope(scope)
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.id = @id AND c.scope = @scope"
            params = [
                {"name": "@id", "value": signal_id},
                {"name": "@scope", "value": scope},
            ]
            docs = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            if not docs:
                return False
            doc = docs[0]
            payload = doc.get("payload") if isinstance(doc.get("payload"), dict) else {}
            if str(payload.get("binaryAssetUri", "")).strip() != source_uri:
                return False
            payload["binaryAssetUri"] = stored_uri
            doc["payload"] = payload
            kwargs: dict[str, Any] = {}
            if doc.get("_etag"):
                kwargs["etag"] = doc.get("_etag")
                kwargs["match_condition"] = "IfNotModified"
            try:
                await run_blocking(container.replace_item, item=doc["id"], body=doc, **kwargs)
            except TypeError:
                await run_blocking(container.replace_item, item=doc["id"], body=doc)
            return True

        key = f"{scope}:{signal_id}"
        doc = self._in_memory.get(key)
        if doc is None:
            return False
        payload_value = doc.get("payload")
        if isinstance(payload_value, dict):
            payload = payload_value
        else:
            payload = {}
        if str(payload.get("binaryAssetUri", "")).strip() != source_uri:
            return False
        payload["binaryAssetUri"] = stored_uri
        doc["payload"] = payload
        self._in_memory[key] = doc
        return True

    def _raise_if_unavailable_for_mutation(self) -> None:
        if self._init_error is not None:
            raise RuntimeError(f"SignalRepository unavailable for mutations: {self._init_error}")

    async def _reserve_write_budget(self, tenant_id: str, storage_bytes: int) -> bool:
        if not tenant_id.startswith("sim-") or self._write_guard is None:
            return False
        if not await self._write_guard.reserve_write(tenant_id, "signal", storage_bytes):
            raise PermissionError("Simulation signal budget or throttle limit reached")
        return True

    async def _reserve_live_capacity(self, tenant_id: str) -> bool:
        """Claim shared capacity for an in-flight live write so simulations yield to it."""
        if tenant_id.startswith("sim-") or self._write_guard is None:
            return False
        reserve = getattr(self._write_guard, "reserve_live_capacity", None)
        if reserve is None:
            return False
        await reserve(1)
        return True

    def _resolve_scope(self, requested_scope: str | None) -> str:
        if self._tenant_id is not None:
            if requested_scope is not None and requested_scope != self._tenant_id:
                raise PermissionError("Signal repository scope does not match its tenant binding")
            return self._tenant_id

        try:
            context_scope = get_current_tenant().tenant_id
        except LookupError:
            if requested_scope is None:
                raise ValueError("Signal scope is required outside a tenant request context")
            return requested_scope

        if requested_scope is not None and requested_scope != context_scope:
            raise PermissionError("Requested signal scope does not match the authenticated tenant")
        return context_scope

    @property
    def init_error(self) -> str | None:
        return self._init_error
