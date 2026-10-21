import asyncio
import logging
import os
import threading
import weakref
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.async_io import run_blocking

from packages.domain.src.domain.models.scenario_run import ScenarioRun
from packages.domain.src.domain.models.simulation_tenant import SimulationTenant

logger = logging.getLogger(__name__)

ARCHIVE_EVIDENCE_DOCUMENT_TYPE = "simulation_archive_evidence"

#: Document types that survive tenant purge because they are retention evidence.
_RETAINED_DOCUMENT_TYPES: frozenset[str] = frozenset({ARCHIVE_EVIDENCE_DOCUMENT_TYPE})


class _SharedCapacityLedger:
    """Process-wide concurrency ledger for in-memory simulation repositories.

    Two repository instances in one process represent two replicas of the same
    logical store, so they must enforce a single cap. Entries are reconciled
    against the live tenants of every registered repository on each operation,
    which keeps the ledger truthful when tenants are archived or deleted without
    an explicit release. Entries are guarded by a plain lock because the critical
    section performs no awaits and must stay valid across event loops.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._repositories: weakref.WeakSet[SimulationRepository] = weakref.WeakSet()
        # tenant_id -> (owning repository ref, confirmed against a stored tenant)
        self._entries: dict[str, tuple[weakref.ReferenceType[SimulationRepository], bool]] = {}

    def register(self, repository: "SimulationRepository") -> None:
        with self._lock:
            self._repositories.add(repository)

    def reserve(self, repository: "SimulationRepository", tenant_id: str, maximum: int) -> bool:
        with self._lock:
            self._repositories.add(repository)
            occupied = self._reconcile()
            if tenant_id in occupied:
                return True
            if len(occupied) >= maximum:
                return False
            self._entries[tenant_id] = (weakref.ref(repository), False)
            return True

    def release(self, tenant_id: str) -> None:
        with self._lock:
            self._entries.pop(tenant_id, None)

    def occupied(self) -> set[str]:
        with self._lock:
            return set(self._reconcile())

    def active_tenants(self, repository: "SimulationRepository") -> list[SimulationTenant]:
        """Capacity-holding tenants visible to every replica sharing this ledger."""
        with self._lock:
            self._repositories.add(repository)
            self._reconcile()
            tenants: dict[str, SimulationTenant] = {}
            for member in list(self._repositories):
                for tenant_id, tenant in list(member._in_memory.items()):
                    if tenant.occupies_capacity():
                        tenants[tenant_id] = tenant
            return list(tenants.values())

    def reset(self) -> None:
        """Drop all reservations and registrations (test and process-restart hygiene)."""
        with self._lock:
            self._entries.clear()
            self._repositories = weakref.WeakSet()

    def _reconcile(self) -> dict[str, tuple[weakref.ReferenceType["SimulationRepository"], bool]]:
        live: dict[str, SimulationRepository] = {}
        for repository in list(self._repositories):
            for tenant_id, tenant in list(repository._in_memory.items()):
                if tenant.occupies_capacity():
                    live[tenant_id] = repository

        retained: dict[str, tuple[weakref.ReferenceType[SimulationRepository], bool]] = {}
        for tenant_id, (reference, confirmed) in self._entries.items():
            if reference() is None:
                continue
            if tenant_id in live:
                retained[tenant_id] = (reference, True)
            elif not confirmed:
                # Reservation taken but the tenant document is not written yet.
                retained[tenant_id] = (reference, False)
        for tenant_id, repository in live.items():
            retained.setdefault(tenant_id, (weakref.ref(repository), True))
        self._entries = retained
        return retained


_CAPACITY_LEDGER = _SharedCapacityLedger()

#: Guards compare-and-set lease updates on the in-memory tenant store.
_MEMORY_LEASE_LOCK = threading.Lock()


def get_shared_capacity_ledger() -> _SharedCapacityLedger:
    return _CAPACITY_LEDGER


def _build_cosmos_client() -> Any:
    """Build a CosmosClient from the ``COSMOS_ENDPOINT`` env var."""
    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class SimulationRepository:
    """Cosmos DB operations for SimulationTenant CRUD against the ``simulation`` container.

    When ``COSMOS_ENDPOINT`` is set the repository talks to Cosmos DB, using
    ``COSMOS_DATABASE`` or the default ``disaster-hub`` database.
    Otherwise it falls back to an in-memory dict so that unit / contract
    tests keep working without infrastructure.
    """

    def __init__(self, cosmos_client: Any = None, database_name: str | None = None):
        self._db_name = database_name or os.environ.get("COSMOS_DATABASE") or "disaster-hub"
        self._container_name = "simulation"
        self._in_memory: dict[str, SimulationTenant] = {}
        self._in_memory_docs: dict[str, dict[str, Any]] = {}
        self._reservation_lock = asyncio.Lock()
        environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "dev").lower()
        is_production = environment in {"production", "staging"}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                if is_production:
                    raise RuntimeError("SimulationRepository failed to initialise Cosmos client") from exc
                logger.warning(
                    "SimulationRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            if is_production:
                raise RuntimeError("SimulationRepository requires COSMOS_ENDPOINT in production/staging")
            self._client = None

        if self._client is None:
            _CAPACITY_LEDGER.register(self)

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    async def create(self, tenant: SimulationTenant) -> SimulationTenant:
        container = self._get_container()
        if container:
            doc = tenant.model_dump(mode="json")
            await run_blocking(container.upsert_item, doc)
        else:
            self._in_memory[tenant.tenant_id] = tenant
        return tenant

    async def create_with_run(self, tenant: SimulationTenant, run: ScenarioRun) -> SimulationTenant:
        tenant_doc = tenant.model_dump(mode="json")
        run_doc = run.model_dump(mode="json")
        run_doc["id"] = run.scenario_run_id
        run_doc["scenario_id"] = tenant.scenario_id
        container = self._get_container()
        if container:
            await run_blocking(
                container.execute_item_batch,
                batch_operations=[
                    ("upsert", (tenant_doc,)),
                    ("upsert", (run_doc,)),
                ],
                partition_key=tenant.scenario_id,
            )
        else:
            self._in_memory[tenant.tenant_id] = tenant
            self._in_memory_docs[run.scenario_run_id] = run_doc
        return tenant

    async def reserve_capacity(self, tenant_id: str, maximum: int) -> bool:
        container = self._get_container()
        if container is None:
            return _CAPACITY_LEDGER.reserve(self, tenant_id, maximum)

        from azure.core import MatchConditions
        from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosResourceNotFoundError

        for _ in range(5):
            try:
                document = await run_blocking(
                    container.read_item,
                    item="simulation-concurrency",
                    partition_key="simulation-capacity",
                )
            except CosmosResourceNotFoundError:
                document = {
                    "id": "simulation-concurrency",
                    "scenario_id": "simulation-capacity",
                    "document_type": "simulation_concurrency",
                    "reservations": [],
                }
                try:
                    await run_blocking(container.create_item, document)
                except CosmosResourceExistsError:
                    continue
            reservations = set(document.get("reservations", []))
            if tenant_id in reservations:
                return True
            if len(reservations) >= maximum:
                return False
            reservations.add(tenant_id)
            document["reservations"] = sorted(reservations)
            try:
                await run_blocking(
                    container.replace_item,
                    item=document["id"],
                    body=document,
                    etag=document.get("_etag"),
                    match_condition=MatchConditions.IfNotModified,
                )
                return True
            except Exception as exc:
                if exc.__class__.__name__ not in {"CosmosAccessConditionFailedError", "CosmosHttpResponseError"}:
                    raise
        raise RuntimeError("Simulation capacity reservation contention exceeded retry budget")

    async def release_capacity(self, tenant_id: str) -> None:
        container = self._get_container()
        if container is None:
            _CAPACITY_LEDGER.release(tenant_id)
            return
        from azure.core import MatchConditions
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        try:
            document = await run_blocking(
                container.read_item,
                item="simulation-concurrency",
                partition_key="simulation-capacity",
            )
        except CosmosResourceNotFoundError:
            return
        document["reservations"] = [value for value in document.get("reservations", []) if value != tenant_id]
        await run_blocking(
            container.replace_item,
            item=document["id"],
            body=document,
            etag=document.get("_etag"),
            match_condition=MatchConditions.IfNotModified,
        )

    async def reserve_budget(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> bool:
        if kind not in {"signal", "recommendation"}:
            raise ValueError(f"Unsupported simulation budget kind: {kind}")
        container = self._get_container()
        if container is not None:
            from azure.core import MatchConditions

            tenant = await self.get_by_tenant_id(tenant_id)
            if tenant is None:
                return False
            for _ in range(5):
                document = await run_blocking(
                    container.read_item,
                    item=tenant.id,
                    partition_key=tenant.scenario_id,
                )
                current = SimulationTenant.model_validate(document)
                if current.status not in {"Active", "Paused"}:
                    return False
                if current.current_sim_seconds > current.resource_limits.max_duration_hours * 3600:
                    return False
                consumption = current.resource_consumption.model_copy(deep=True)
                if kind == "signal":
                    if consumption.signal_count >= current.resource_limits.max_signals:
                        return False
                    consumption.signal_count += 1
                    consumption.storage_bytes += max(0, storage_bytes)
                else:
                    if consumption.recommendation_count >= current.resource_limits.max_recommendations:
                        return False
                    consumption.recommendation_count += 1
                document["resource_consumption"] = consumption.model_dump(mode="json")
                try:
                    await run_blocking(
                        container.replace_item,
                        item=document["id"],
                        body=document,
                        etag=document.get("_etag"),
                        match_condition=MatchConditions.IfNotModified,
                    )
                    return True
                except Exception as exc:
                    if exc.__class__.__name__ not in {
                        "CosmosAccessConditionFailedError",
                        "CosmosHttpResponseError",
                    }:
                        raise
            raise RuntimeError("Simulation budget reservation contention exceeded retry budget")

        async with self._reservation_lock:
            tenant = await self.get_by_tenant_id(tenant_id)
            if tenant is None or tenant.status not in {"Active", "Paused"}:
                return False
            if tenant.current_sim_seconds > tenant.resource_limits.max_duration_hours * 3600:
                return False
            consumption = tenant.resource_consumption.model_copy(deep=True)
            if kind == "signal":
                if consumption.signal_count >= tenant.resource_limits.max_signals:
                    return False
                consumption.signal_count += 1
                consumption.storage_bytes += max(0, storage_bytes)
            else:
                if consumption.recommendation_count >= tenant.resource_limits.max_recommendations:
                    return False
                consumption.recommendation_count += 1
            await self.update(tenant.model_copy(update={"resource_consumption": consumption}))
            return True

    async def release_budget(self, tenant_id: str, kind: str, storage_bytes: int = 0) -> None:
        container = self._get_container()
        if container is not None:
            from azure.core import MatchConditions

            tenant = await self.get_by_tenant_id(tenant_id)
            if tenant is None:
                return
            for _ in range(5):
                document = await run_blocking(
                    container.read_item,
                    item=tenant.id,
                    partition_key=tenant.scenario_id,
                )
                consumption = SimulationTenant.model_validate(document).resource_consumption.model_copy(deep=True)
                if kind == "signal":
                    consumption.signal_count = max(0, consumption.signal_count - 1)
                    consumption.storage_bytes = max(0, consumption.storage_bytes - max(0, storage_bytes))
                elif kind == "recommendation":
                    consumption.recommendation_count = max(0, consumption.recommendation_count - 1)
                document["resource_consumption"] = consumption.model_dump(mode="json")
                try:
                    await run_blocking(
                        container.replace_item,
                        item=document["id"],
                        body=document,
                        etag=document.get("_etag"),
                        match_condition=MatchConditions.IfNotModified,
                    )
                    return
                except Exception as exc:
                    if exc.__class__.__name__ not in {
                        "CosmosAccessConditionFailedError",
                        "CosmosHttpResponseError",
                    }:
                        raise
            raise RuntimeError("Simulation budget release contention exceeded retry budget")

        async with self._reservation_lock:
            tenant = await self.get_by_tenant_id(tenant_id)
            if tenant is None:
                return
            consumption = tenant.resource_consumption.model_copy(deep=True)
            if kind == "signal":
                consumption.signal_count = max(0, consumption.signal_count - 1)
                consumption.storage_bytes = max(0, consumption.storage_bytes - max(0, storage_bytes))
            elif kind == "recommendation":
                consumption.recommendation_count = max(0, consumption.recommendation_count - 1)
            await self.update(tenant.model_copy(update={"resource_consumption": consumption}))

    async def purge_tenant_documents(self, tenant_id: str) -> int:
        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return 0
        container = self._get_container()
        if container:
            query = (
                "SELECT c.id FROM c WHERE c.tenant_id = @tid "
                "AND c.document_type NOT IN ('simulation_tenant', @retained)"
            )
            documents = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[
                            {"name": "@tid", "value": tenant_id},
                            {"name": "@retained", "value": ARCHIVE_EVIDENCE_DOCUMENT_TYPE},
                        ],
                        enable_cross_partition_query=True,
                    )
                )
            )
            for document in documents:
                await run_blocking(
                    container.delete_item,
                    item=document["id"],
                    partition_key=tenant.scenario_id,
                )
            return len(documents)
        ids = [key for key, doc in self._in_memory_docs.items() if self._is_operational_document(doc, tenant_id)]
        for document_id in ids:
            self._in_memory_docs.pop(document_id, None)
        return len(ids)

    async def count_operational_documents(self, tenant_id: str) -> int:
        """Count tenant documents that a purge is required to remove."""
        container = self._get_container()
        if container:
            query = (
                "SELECT VALUE COUNT(1) FROM c WHERE c.tenant_id = @tid "
                "AND c.document_type NOT IN ('simulation_tenant', @retained)"
            )
            return (
                await run_blocking(
                    lambda: list(
                        container.query_items(
                            query,
                            parameters=[
                                {"name": "@tid", "value": tenant_id},
                                {"name": "@retained", "value": ARCHIVE_EVIDENCE_DOCUMENT_TYPE},
                            ],
                            enable_cross_partition_query=True,
                        )
                    )
                )
            )[0]
        return sum(
            1 for document in self._in_memory_docs.values() if self._is_operational_document(document, tenant_id)
        )

    @staticmethod
    def _is_operational_document(document: dict[str, Any], tenant_id: str) -> bool:
        if document.get("tenant_id") != tenant_id:
            return False
        return str(document.get("document_type", "")) not in _RETAINED_DOCUMENT_TYPES

    async def record_archive_evidence(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Persist the authorized lookup that outlives operational tenant deletion."""
        document = dict(evidence)
        document["document_type"] = ARCHIVE_EVIDENCE_DOCUMENT_TYPE
        return await self.upsert_document(document)

    async def get_archive_evidence(self, tenant_id: str) -> dict[str, Any] | None:
        return await self.get_document(
            document_type=ARCHIVE_EVIDENCE_DOCUMENT_TYPE,
            document_id=f"{tenant_id}:archive-evidence",
        )

    async def list_tenant_documents(self, tenant_id: str) -> list[dict[str, Any]]:
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.tenant_id = @tid"
            return await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@tid", "value": tenant_id}],
                        enable_cross_partition_query=True,
                    )
                )
            )
        return [dict(document) for document in self._in_memory_docs.values() if document.get("tenant_id") == tenant_id]

    async def delete(self, tenant_id: str) -> bool:
        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False
        container = self._get_container()
        if container:
            await run_blocking(
                container.delete_item,
                item=tenant.id,
                partition_key=tenant.scenario_id,
            )
        else:
            self._in_memory.pop(tenant_id, None)
        return True

    async def get_by_tenant_id(self, tenant_id: str) -> SimulationTenant | None:
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.tenant_id = @tid AND c.document_type = 'simulation_tenant'"
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@tid", "value": tenant_id}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            if items:
                return SimulationTenant.model_validate(items[0])
            return None
        return self._in_memory.get(tenant_id)

    async def get_by_report_id(self, report_id: str) -> SimulationTenant | None:
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.document_type = 'simulation_tenant' AND c.exercise_report_id = @reportId"
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@reportId", "value": report_id}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return SimulationTenant.model_validate(items[0]) if items else None
        return next(
            (tenant for tenant in self._in_memory.values() if tenant.exercise_report_id == report_id),
            None,
        )

    async def get_by_participant(self, user_oid: str) -> list[SimulationTenant]:
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE ARRAY_CONTAINS(c.participants, @oid) "
                "AND c.document_type = 'simulation_tenant' "
                "AND c.status IN ('Active', 'Paused')"
            )
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@oid", "value": user_oid}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return [SimulationTenant.model_validate(item) for item in items]
        return [t for t in self._in_memory.values() if user_oid in t.participants and t.status in ("Active", "Paused")]

    async def list_by_status(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
        participant_oid: str | None = None,
    ) -> tuple[list[SimulationTenant], int]:
        container = self._get_container()
        if container:
            where = "WHERE c.document_type = 'simulation_tenant'"
            params: list[dict[str, Any]] = []
            if status:
                where += " AND c.status = @status"
                params.append({"name": "@status", "value": status})
            if participant_oid:
                where += " AND (c.created_by = @participant OR ARRAY_CONTAINS(c.participants, @participant))"
                params.append({"name": "@participant", "value": participant_oid})
            count_query = f"SELECT VALUE COUNT(1) FROM c {where}"
            count_params = list(params)
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
            query = f"SELECT * FROM c {where} ORDER BY c.created_at DESC OFFSET @offset LIMIT @limit"
            params.extend(
                [
                    {"name": "@offset", "value": offset},
                    {"name": "@limit", "value": limit},
                ]
            )
            items = await run_blocking(
                lambda: list(container.query_items(query, parameters=params, enable_cross_partition_query=True))
            )
            return [SimulationTenant.model_validate(i) for i in items], total
        tenants = list(self._in_memory.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        if participant_oid:
            tenants = [
                tenant
                for tenant in tenants
                if tenant.created_by == participant_oid or participant_oid in tenant.participants
            ]
        total = len(tenants)
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        return tenants[offset : offset + limit], total

    async def count_active(self) -> int:
        container = self._get_container()
        if container:
            query = (
                "SELECT VALUE COUNT(1) FROM c "
                "WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('Provisioning', 'Active', 'Paused') "
                "AND (NOT IS_DEFINED(c.provisioning_failed_at) OR IS_NULL(c.provisioning_failed_at))"
            )
            return (await run_blocking(lambda: list(container.query_items(query, enable_cross_partition_query=True))))[
                0
            ]
        return sum(1 for t in self._in_memory.values() if t.occupies_capacity())

    async def list_active_tenants(self, limit: int = 100) -> list[SimulationTenant]:
        """Tenants that currently hold a concurrency slot (Provisioning/Active/Paused)."""
        container = self._get_container()
        if container:
            query = (
                "SELECT TOP @limit * FROM c "
                "WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('Provisioning', 'Active', 'Paused') "
                "AND (NOT IS_DEFINED(c.provisioning_failed_at) OR IS_NULL(c.provisioning_failed_at)) "
                "ORDER BY c.created_at DESC"
            )
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@limit", "value": limit}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return [SimulationTenant.model_validate(item) for item in items]
        tenants = _CAPACITY_LEDGER.active_tenants(self)
        tenants.sort(key=lambda tenant: tenant.created_at, reverse=True)
        return tenants[:limit]

    async def update(self, tenant: SimulationTenant) -> SimulationTenant:
        container = self._get_container()
        if container:
            doc = tenant.model_dump(mode="json")
            await run_blocking(container.upsert_item, doc)
        else:
            self._in_memory[tenant.tenant_id] = tenant
        return tenant

    async def is_participant(self, tenant_id: str, user_oid: str) -> bool:
        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False
        return user_oid in tenant.participants

    async def list_expired(self, now: datetime | None = None) -> list[SimulationTenant]:
        """Find active/paused tenants past their expires_at timestamp."""
        now = now or datetime.now(UTC)
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('Active', 'Paused') "
                "AND c.expires_at <= @now"
            )
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@now", "value": now.isoformat()}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return [SimulationTenant.model_validate(i) for i in items]
        return [
            t
            for t in self._in_memory.values()
            if t.status in ("Active", "Paused") and t.expires_at and t.expires_at <= now
        ]

    async def list_expiring(self, before: datetime) -> list[SimulationTenant]:
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c WHERE c.document_type = 'simulation_tenant' "
                "AND c.status IN ('Active', 'Paused') "
                "AND c.expires_at <= @before "
                "AND (NOT IS_DEFINED(c.expiry_notice_sent_at) OR IS_NULL(c.expiry_notice_sent_at))"
            )
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[{"name": "@before", "value": before.isoformat()}],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return [SimulationTenant.model_validate(item) for item in items]
        return [
            tenant
            for tenant in self._in_memory.values()
            if tenant.status in {"Active", "Paused"}
            and tenant.expires_at is not None
            and tenant.expires_at <= before
            and tenant.expiry_notice_sent_at is None
        ]

    async def touch_activity(self, tenant_id: str, at: datetime | None = None) -> SimulationTenant | None:
        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None or tenant.status not in {"Active", "Paused"}:
            return tenant
        activity_at = at or datetime.now(UTC)
        updated = tenant.model_copy(
            update={
                "last_activity_at": activity_at,
                "expires_at": activity_at + timedelta(hours=tenant.ttl_hours),
                "expiry_notice_sent_at": None,
            }
        )
        return await self.update(updated)

    async def claim_expiry(self, tenant_id: str, owner: str, now: datetime, lease_seconds: int = 300) -> bool:
        return await self._claim_lease(
            tenant_id,
            owner,
            now,
            lease_seconds,
            owner_field="expiry_lease_owner",
            until_field="expiry_lease_until",
            allowed_statuses={"Active", "Paused"},
        )

    async def claim_archive(self, tenant_id: str, owner: str, now: datetime, lease_seconds: int = 600) -> bool:
        return await self._claim_lease(
            tenant_id,
            owner,
            now,
            lease_seconds,
            owner_field="archive_lease_owner",
            until_field="archive_lease_until",
            allowed_statuses={"Active", "Paused", "Archiving"},
        )

    async def release_archive_claim(self, tenant_id: str, owner: str) -> None:
        await self._release_lease(
            tenant_id,
            owner,
            owner_field="archive_lease_owner",
            until_field="archive_lease_until",
        )

    async def _claim_lease(
        self,
        tenant_id: str,
        owner: str,
        now: datetime,
        lease_seconds: int,
        *,
        owner_field: str,
        until_field: str,
        allowed_statuses: set[str],
    ) -> bool:
        """Take a lease with a conditional write so only one replica proceeds."""
        container = self._get_container()
        if container is None:
            with _MEMORY_LEASE_LOCK:
                tenant = self._in_memory.get(tenant_id)
                if tenant is None or tenant.status not in allowed_statuses:
                    return False
                held_until = getattr(tenant, until_field)
                if held_until is not None and held_until > now:
                    return getattr(tenant, owner_field) == owner
                self._in_memory[tenant_id] = tenant.model_copy(
                    update={
                        owner_field: owner,
                        until_field: now + timedelta(seconds=lease_seconds),
                    }
                )
                return True

        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return False
        from azure.core import MatchConditions

        document = await run_blocking(
            container.read_item,
            item=tenant.id,
            partition_key=tenant.scenario_id,
        )
        current = SimulationTenant.model_validate(document)
        if current.status not in allowed_statuses:
            return False
        held_until = getattr(current, until_field)
        if held_until is not None and held_until > now:
            return getattr(current, owner_field) == owner
        document[owner_field] = owner
        document[until_field] = (now + timedelta(seconds=lease_seconds)).isoformat()
        try:
            await run_blocking(
                container.replace_item,
                item=document["id"],
                body=document,
                etag=document.get("_etag"),
                match_condition=MatchConditions.IfNotModified,
            )
        except Exception as exc:
            if exc.__class__.__name__ in {"CosmosAccessConditionFailedError", "CosmosHttpResponseError"}:
                return False
            raise
        return True

    async def _release_lease(self, tenant_id: str, owner: str, *, owner_field: str, until_field: str) -> None:
        container = self._get_container()
        if container is None:
            with _MEMORY_LEASE_LOCK:
                tenant = self._in_memory.get(tenant_id)
                if tenant is None or getattr(tenant, owner_field) != owner:
                    return
                self._in_memory[tenant_id] = tenant.model_copy(update={owner_field: None, until_field: None})
            return

        tenant = await self.get_by_tenant_id(tenant_id)
        if tenant is None:
            return
        from azure.core import MatchConditions

        document = await run_blocking(
            container.read_item,
            item=tenant.id,
            partition_key=tenant.scenario_id,
        )
        if document.get(owner_field) != owner:
            return
        document[owner_field] = None
        document[until_field] = None
        try:
            await run_blocking(
                container.replace_item,
                item=document["id"],
                body=document,
                etag=document.get("_etag"),
                match_condition=MatchConditions.IfNotModified,
            )
        except Exception as exc:
            if exc.__class__.__name__ not in {"CosmosAccessConditionFailedError", "CosmosHttpResponseError"}:
                raise

    async def upsert_document(self, document: dict[str, Any]) -> dict[str, Any]:
        doc_id = str(document.get("id") or document.get("scenario_id") or document.get("run_id") or "").strip()
        if not doc_id:
            raise ValueError("document must contain an id/scenario_id/run_id")
        document = dict(document)
        document["id"] = doc_id
        container = self._get_container()
        if container:
            await run_blocking(container.upsert_item, document)
        else:
            self._in_memory_docs[doc_id] = document
        return document

    async def get_document(
        self,
        *,
        document_type: str,
        document_id: str,
    ) -> dict[str, Any] | None:
        container = self._get_container()
        if container:
            query = "SELECT * FROM c WHERE c.document_type = @type AND c.id = @id"
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[
                            {"name": "@type", "value": document_type},
                            {"name": "@id", "value": document_id},
                        ],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return items[0] if items else None
        item = self._in_memory_docs.get(document_id)
        if item is None:
            return None
        if str(item.get("document_type")) != document_type:
            return None
        return item

    async def list_documents(
        self,
        *,
        document_type: str,
        owner_agency_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        container = self._get_container()
        if container:
            query = (
                "SELECT TOP @limit * FROM c "
                "WHERE c.document_type = @type AND c.owner_agency_id = @agency "
                "ORDER BY c.created_at DESC"
            )
            items = await run_blocking(
                lambda: list(
                    container.query_items(
                        query,
                        parameters=[
                            {"name": "@limit", "value": limit},
                            {"name": "@type", "value": document_type},
                            {"name": "@agency", "value": owner_agency_id},
                        ],
                        enable_cross_partition_query=True,
                    )
                )
            )
            return items
        rows = [
            value
            for value in self._in_memory_docs.values()
            if str(value.get("document_type")) == document_type
            and str(value.get("owner_agency_id", "")) == owner_agency_id
        ]
        rows.sort(key=lambda row: str(row.get("created_at", "")), reverse=True)
        return rows[:limit]
