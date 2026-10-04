import logging
from datetime import UTC, datetime
from typing import Any

from packages.domain.src.domain.models.signal import Signal
from packages.domain.src.domain.repositories.signal_wire import to_signal_document

logger = logging.getLogger(__name__)

SIGNALS_STORE: dict[tuple[str, str], Signal] = {}


class SignalRepository:
    """Cosmos DB signal persistence with hierarchical partition key.

    Partition key: /scope/jurisdictionId/dataSourceId
    - scope: 'live' for operational, 'sim_{runId}' for simulation
    - jurisdictionId: 'national', 'nsw', 'vic', etc.
    - dataSourceId: from seed catalogue

    National signals create fan-out reference records in each affected
    jurisdiction partition.
    """

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._cosmos = cosmos_client
        self._database_name = database_name
        self._container_name = "signals"

    def _memory_key(self, scope: str, signal_id: str) -> tuple[str, str]:
        return (scope, signal_id)

    async def _take_limited(self, items: Any, limit: int) -> list[Signal]:
        bounded: list[Signal] = []
        async for item in items:
            bounded.append(Signal(**item))
            if len(bounded) >= limit:
                break
        return bounded

    async def save(self, signal: Signal, scope: str = "live") -> None:
        doc = to_signal_document(signal, scope)

        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            await container.upsert_item(doc)
        else:
            SIGNALS_STORE[self._memory_key(scope, signal.signal_id)] = signal

    async def get_by_hpk(
        self,
        *,
        signal_id: str,
        scope: str,
        jurisdiction_id: str,
        data_source_id: str,
    ) -> Signal | None:
        if self._cosmos:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            try:
                doc = container.read_item(
                    item=signal_id,
                    partition_key=[scope, jurisdiction_id, data_source_id],
                )
            except CosmosResourceNotFoundError:
                return None
            return Signal(**doc)

        signal = SIGNALS_STORE.get(self._memory_key(scope, signal_id))
        if signal is None:
            return None
        if (signal.jurisdiction_id or "national") != jurisdiction_id:
            return None
        if signal.data_source_id != data_source_id:
            return None
        return signal

    async def save_with_fanout(
        self,
        signal: Signal,
        affected_jurisdiction_ids: list[str],
        scope: str = "live",
    ) -> None:
        await self.save(signal, scope)
        for jid in affected_jurisdiction_ids:
            if jid != (signal.jurisdiction_id or "national"):
                ref = signal.model_copy(
                    update={
                        "signal_id": f"{signal.signal_id}:ref:{jid}",
                        "jurisdiction_id": jid,
                        "provenance": {
                            **signal.provenance,
                            "referenceSignalId": signal.signal_id,
                        },
                    }
                )
                if self._cosmos:
                    await self.save(ref, scope)
                else:
                    SIGNALS_STORE[self._memory_key(scope, ref.signal_id)] = ref

    async def query_by_incident(
        self,
        incident_id: str,
        *,
        scope: str,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            conditions = ["c.incident_id = @incidentId", "c.scope = @scope"]
            params: list[dict[str, Any]] = [
                {"name": "@incidentId", "value": incident_id},
                {"name": "@scope", "value": scope},
            ]
            if owning_agency_id:
                conditions.append("c.owningAgencyId = @owningAgencyId")
                params.append({"name": "@owningAgencyId", "value": owning_agency_id})
            if allowed_jurisdictions:
                conditions.append("ARRAY_CONTAINS(@allowedJurisdictions, c.jurisdictionId)")
                params.append({"name": "@allowedJurisdictions", "value": sorted(allowed_jurisdictions)})
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.occurred_at DESC, c.id DESC"
            items = container.query_items(query=query, parameters=params, max_item_count=limit)
            return await self._take_limited(items, limit)
        results = [
            s
            for (stored_scope, _signal_id), s in SIGNALS_STORE.items()
            if s.incident_id == incident_id
            and stored_scope == scope
            and (owning_agency_id is None or s.owning_agency_id == owning_agency_id)
            and (allowed_jurisdictions is None or (s.jurisdiction_id or "") in allowed_jurisdictions)
        ]
        results.sort(key=lambda s: (s.occurred_at, s.signal_id), reverse=True)
        return results[:limit]

    async def query_by_jurisdiction(
        self,
        jurisdiction_id: str,
        *,
        scope: str,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        category: str | None = None,
        since: datetime | None = None,
        include_all_jurisdictions: bool = False,
        limit: int = 100,
    ) -> list[Signal]:
        if self._cosmos:
            conditions = ["c.scope = @scope"]
            params: list[dict[str, Any]] = [{"name": "@scope", "value": scope}]
            if category:
                conditions.append("c.category = @category")
                params.append({"name": "@category", "value": category})
            if since:
                conditions.append("c.occurred_at >= @since")
                params.append({"name": "@since", "value": since.isoformat()})
            if owning_agency_id:
                conditions.append("c.owningAgencyId = @owningAgencyId")
                params.append({"name": "@owningAgencyId", "value": owning_agency_id})
            if allowed_jurisdictions:
                conditions.append("ARRAY_CONTAINS(@allowedJurisdictions, c.jurisdictionId)")
                params.append({"name": "@allowedJurisdictions", "value": sorted(allowed_jurisdictions)})

            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.occurred_at DESC"
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            items = container.query_items(
                query=query,
                parameters=params,
                partition_key=[scope, jurisdiction_id],
                max_item_count=limit,
            )
            return await self._take_limited(items, limit)
        results = [
            s
            for (stored_scope, _signal_id), s in SIGNALS_STORE.items()
            if stored_scope == scope
            and (s.jurisdiction_id == jurisdiction_id or (jurisdiction_id == "national" and include_all_jurisdictions))
            and (owning_agency_id is None or s.owning_agency_id == owning_agency_id)
            and (allowed_jurisdictions is None or (s.jurisdiction_id or "") in allowed_jurisdictions)
            and (category is None or s.category == category)
            and (since is None or s.occurred_at >= since)
        ]
        results.sort(key=lambda s: s.occurred_at, reverse=True)
        return results[:limit]

    async def query_unassociated(
        self,
        jurisdiction_id: str,
        since: datetime | None = None,
        *,
        scope: str,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        include_all_jurisdictions: bool = False,
        limit: int = 100,
    ) -> list[Signal]:
        if self._cosmos:
            conditions = ["c.incident_id = null", "c.scope = @scope", "c.occurred_at >= @since"]
            params: list[dict[str, Any]] = [
                {"name": "@scope", "value": scope},
                {"name": "@since", "value": (since or datetime.now(UTC)).isoformat()},
            ]
            if owning_agency_id:
                conditions.append("c.owningAgencyId = @owningAgencyId")
                params.append({"name": "@owningAgencyId", "value": owning_agency_id})
            if allowed_jurisdictions:
                conditions.append("ARRAY_CONTAINS(@allowedJurisdictions, c.jurisdictionId)")
                params.append({"name": "@allowedJurisdictions", "value": sorted(allowed_jurisdictions)})

            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)} ORDER BY c.occurred_at DESC, c.id DESC"
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            items = container.query_items(
                query=query,
                parameters=params,
                partition_key=[scope, jurisdiction_id],
                max_item_count=limit,
            )
            return await self._take_limited(items, limit)
        cutoff = since or datetime.min.replace(tzinfo=UTC)
        results = [
            s
            for (stored_scope, _signal_id), s in SIGNALS_STORE.items()
            if s.incident_id is None
            and stored_scope == scope
            and (owning_agency_id is None or s.owning_agency_id == owning_agency_id)
            and (allowed_jurisdictions is None or (s.jurisdiction_id or "") in allowed_jurisdictions)
            and (s.jurisdiction_id == jurisdiction_id or (jurisdiction_id == "national" and include_all_jurisdictions))
            and s.occurred_at >= cutoff
        ]
        results.sort(key=lambda s: (s.occurred_at, s.signal_id), reverse=True)
        return results[:limit]

    async def update_incident_id(
        self,
        signal_id: str,
        incident_id: str,
        *,
        scope: str,
        expected_incident_id: str | None = None,
    ) -> bool:
        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            conditions = ["c.id = @id", "c.scope = @scope"]
            params = [
                {"name": "@id", "value": signal_id},
                {"name": "@scope", "value": scope},
            ]
            if expected_incident_id is None:
                conditions.append("c.incident_id = null")
            else:
                conditions.append("c.incident_id = @expectedIncidentId")
                params.append({"name": "@expectedIncidentId", "value": expected_incident_id})
            query = f"SELECT * FROM c WHERE {' AND '.join(conditions)}"
            items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
            if not items:
                return False
            doc = items[0]
            doc["incident_id"] = incident_id
            replace_kwargs: dict[str, Any] = {}
            if doc.get("_etag"):
                replace_kwargs["etag"] = doc.get("_etag")
                replace_kwargs["match_condition"] = "IfNotModified"
            try:
                container.replace_item(item=doc["id"], body=doc, **replace_kwargs)
            except TypeError:
                container.replace_item(item=doc["id"], body=doc)
            return True

        key = self._memory_key(scope, signal_id)
        if key not in SIGNALS_STORE:
            return False
        sig = SIGNALS_STORE[key]
        if sig.incident_id != expected_incident_id:
            return False
        SIGNALS_STORE[key] = sig.model_copy(update={"incident_id": incident_id})
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
        if self._cosmos:
            container = self._cosmos.get_database_client(self._database_name).get_container_client(self._container_name)
            query = "SELECT * FROM c WHERE c.id = @id AND c.scope = @scope"
            params = [
                {"name": "@id", "value": signal_id},
                {"name": "@scope", "value": scope},
            ]
            docs = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
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

            replace_kwargs: dict[str, Any] = {}
            if doc.get("_etag"):
                replace_kwargs["etag"] = doc.get("_etag")
                replace_kwargs["match_condition"] = "IfNotModified"
            try:
                container.replace_item(item=doc["id"], body=doc, **replace_kwargs)
            except TypeError:
                container.replace_item(item=doc["id"], body=doc)
            return True

        key = self._memory_key(scope, signal_id)
        if key not in SIGNALS_STORE:
            return False
        sig = SIGNALS_STORE[key]
        new_provenance = {
            **sig.provenance,
            "tier2DecisionId": decision_id,
            "tier2Decision": decision,
            "tier2Rationale": rationale,
        }
        SIGNALS_STORE[key] = sig.model_copy(
            update={
                "validation_status": validation_status,
                "provenance": new_provenance,
            }
        )
        return True
