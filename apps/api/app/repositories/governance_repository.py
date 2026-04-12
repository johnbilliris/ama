from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment
from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.functional_domain_precedence import (
    FunctionalDomainPrecedence,
)
from packages.domain.src.domain.models.governance_audit import GovernanceAuditEntry
from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition

logger = logging.getLogger(__name__)

_PRECEDENCE_PK = "_precedence"

_TYPE_SOURCE = "source"
_TYPE_ASSESSMENT = "assessment"
_TYPE_ASSIGNMENT = "assignment"
_TYPE_CHAIN = "chain"
_TYPE_PRECEDENCE = "precedence"
_TYPE_AUDIT = "audit"


class GovernanceRepository:
    """Cosmos DB-backed governance store.

    When ``COSMOS_ENDPOINT`` is set the repository talks to Cosmos DB.
    Otherwise it falls back to a fast in-memory dict store so that
    unit / contract tests keep working without infrastructure.
    """

    def __init__(self, container: Any | None = None) -> None:
        if container is not None:
            self._backend = _CosmosBackend(container)
        elif os.environ.get("COSMOS_ENDPOINT"):
            self._backend = _CosmosBackend(_build_container())
        else:
            self._backend = _InMemoryBackend()

    # ------------------------------------------------------------------
    # DataSource
    # ------------------------------------------------------------------

    def save_source(self, source: DataSource) -> DataSource:
        return self._backend.save_source(source)

    def get_source(self, data_source_id: str) -> DataSource | None:
        return self._backend.get_source(data_source_id)

    def list_sources(self, **filters: str | None) -> list[DataSource]:
        return self._backend.list_sources(**filters)

    # ------------------------------------------------------------------
    # ConstitutionalAssessment
    # ------------------------------------------------------------------

    def save_assessment(self, assessment: ConstitutionalAssessment) -> ConstitutionalAssessment:
        return self._backend.save_assessment(assessment)

    def get_assessments_for_source(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return self._backend.get_assessments_for_source(data_source_id)

    def get_current_assessments(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return self._backend.get_current_assessments(data_source_id)

    # ------------------------------------------------------------------
    # AgentGovernanceAssignment
    # ------------------------------------------------------------------

    def save_assignment(self, assignment: AgentGovernanceAssignment) -> AgentGovernanceAssignment:
        return self._backend.save_assignment(assignment)

    def get_assignments_for_source(self, data_source_id: str) -> list[AgentGovernanceAssignment]:
        return self._backend.get_assignments_for_source(data_source_id)

    # ------------------------------------------------------------------
    # HandoffChainDefinition
    # ------------------------------------------------------------------

    def save_chain(self, chain: HandoffChainDefinition) -> HandoffChainDefinition:
        return self._backend.save_chain(chain)

    def get_chain_for_source(self, data_source_id: str) -> HandoffChainDefinition | None:
        return self._backend.get_chain_for_source(data_source_id)

    # ------------------------------------------------------------------
    # FunctionalDomainPrecedence
    # ------------------------------------------------------------------

    def save_precedence(self, precedence: FunctionalDomainPrecedence) -> FunctionalDomainPrecedence:
        return self._backend.save_precedence(precedence)

    def list_precedence(
        self, hazard_type: str | None = None, jurisdiction_id: str | None = None,
    ) -> list[FunctionalDomainPrecedence]:
        return self._backend.list_precedence(hazard_type, jurisdiction_id)

    def resolve_precedence(
        self, hazard_type: str, jurisdiction_id: str | None = None,
    ) -> FunctionalDomainPrecedence | None:
        return self._backend.resolve_precedence(hazard_type, jurisdiction_id)

    # ------------------------------------------------------------------
    # GovernanceAuditEntry
    # ------------------------------------------------------------------

    def append_audit(self, entry: GovernanceAuditEntry) -> GovernanceAuditEntry:
        return self._backend.append_audit(entry)

    def get_audit_trail(
        self,
        data_source_id: str,
        action: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[GovernanceAuditEntry]:
        return self._backend.get_audit_trail(data_source_id, action, from_dt, to_dt)


# ======================================================================
# In-memory backend (tests / local dev without Cosmos)
# ======================================================================


class _InMemoryBackend:

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}
        self._assessments: dict[str, ConstitutionalAssessment] = {}
        self._assignments: dict[str, AgentGovernanceAssignment] = {}
        self._chains: dict[str, HandoffChainDefinition] = {}
        self._precedence: dict[str, FunctionalDomainPrecedence] = {}
        self._audit: list[GovernanceAuditEntry] = []

    def save_source(self, source: DataSource) -> DataSource:
        now = datetime.now(UTC)
        if source.data_source_id not in self._sources:
            source.created_at = source.created_at or now
        source.updated_at = now
        self._sources[source.data_source_id] = source
        return source

    def get_source(self, data_source_id: str) -> DataSource | None:
        source = self._sources.get(data_source_id)
        return source.model_copy() if source else None

    def list_sources(self, **filters: str | None) -> list[DataSource]:
        results = list(self._sources.values())
        for key, value in filters.items():
            if value is not None:
                results = [s for s in results if getattr(s, key, None) == value]
        return results

    def save_assessment(self, assessment: ConstitutionalAssessment) -> ConstitutionalAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    def get_assessments_for_source(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return [a for a in self._assessments.values() if a.data_source_id == data_source_id]

    def get_current_assessments(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return [a for a in self.get_assessments_for_source(data_source_id) if a.is_current]

    def save_assignment(self, assignment: AgentGovernanceAssignment) -> AgentGovernanceAssignment:
        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_assignments_for_source(self, data_source_id: str) -> list[AgentGovernanceAssignment]:
        return [
            a for a in self._assignments.values()
            if a.data_source_id == data_source_id and a.status == "active"
        ]

    def save_chain(self, chain: HandoffChainDefinition) -> HandoffChainDefinition:
        self._chains[chain.chain_id] = chain
        return chain

    def get_chain_for_source(self, data_source_id: str) -> HandoffChainDefinition | None:
        for chain in self._chains.values():
            if chain.data_source_id == data_source_id and chain.status == "active":
                return chain
        return None

    def save_precedence(self, precedence: FunctionalDomainPrecedence) -> FunctionalDomainPrecedence:
        self._precedence[precedence.precedence_id] = precedence
        return precedence

    def list_precedence(
        self, hazard_type: str | None = None, jurisdiction_id: str | None = None,
    ) -> list[FunctionalDomainPrecedence]:
        results = list(self._precedence.values())
        if hazard_type:
            results = [p for p in results if p.hazard_type == hazard_type]
        if jurisdiction_id is not None:
            results = [p for p in results if p.jurisdiction_id == jurisdiction_id]
        return results

    def resolve_precedence(
        self, hazard_type: str, jurisdiction_id: str | None = None,
    ) -> FunctionalDomainPrecedence | None:
        if jurisdiction_id:
            override = next(
                (p for p in self._precedence.values()
                 if p.hazard_type == hazard_type and p.jurisdiction_id == jurisdiction_id),
                None,
            )
            if override:
                return override
        return next(
            (p for p in self._precedence.values()
             if p.hazard_type == hazard_type and p.jurisdiction_id is None),
            None,
        )

    def append_audit(self, entry: GovernanceAuditEntry) -> GovernanceAuditEntry:
        self._audit.append(entry)
        return entry

    def get_audit_trail(
        self,
        data_source_id: str,
        action: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[GovernanceAuditEntry]:
        results = [e for e in self._audit if e.data_source_id == data_source_id]
        if action:
            results = [e for e in results if e.action == action]
        if from_dt:
            results = [e for e in results if e.timestamp >= from_dt]
        if to_dt:
            results = [e for e in results if e.timestamp <= to_dt]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)


# ======================================================================
# Cosmos DB backend (production)
# ======================================================================


def _build_container() -> Any:
    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    database = os.environ.get("COSMOS_DATABASE", "disaster-hub")
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    db = client.get_database_client(database)
    return db.get_container_client("governance")


class _CosmosBackend:

    def __init__(self, container: Any) -> None:
        self._container = container

    # helpers

    def _upsert(self, doc: dict[str, Any]) -> dict[str, Any]:
        return self._container.upsert_item(doc)

    def _point_read(self, item_id: str, partition_key: str) -> dict[str, Any] | None:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        try:
            return self._container.read_item(item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            return None

    def _query(
        self,
        query: str,
        parameters: list[dict[str, object]],
        partition_key: str | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {}
        if partition_key is not None:
            kwargs["partition_key"] = partition_key
        else:
            kwargs["enable_cross_partition_query"] = True
        return list(self._container.query_items(query=query, parameters=parameters, **kwargs))

    # DataSource

    def save_source(self, source: DataSource) -> DataSource:
        now = datetime.now(UTC)
        existing = self._point_read(source.data_source_id, source.data_source_id)
        if existing is None:
            source.created_at = source.created_at or now
        source.updated_at = now
        doc = source.model_dump(mode="json")
        doc["id"] = source.data_source_id
        doc["partitionKey"] = source.data_source_id
        doc["type"] = _TYPE_SOURCE
        self._upsert(doc)
        return source

    def get_source(self, data_source_id: str) -> DataSource | None:
        doc = self._point_read(data_source_id, data_source_id)
        if doc is None or doc.get("type") != _TYPE_SOURCE:
            return None
        return DataSource.model_validate(doc)

    def list_sources(self, **filters: str | None) -> list[DataSource]:
        clauses = ["c.type = @type"]
        params: list[dict[str, object]] = [{"name": "@type", "value": _TYPE_SOURCE}]
        idx = 0
        for key, value in filters.items():
            if value is not None:
                pname = f"@f{idx}"
                clauses.append(f"c.{key} = {pname}")
                params.append({"name": pname, "value": value})
                idx += 1
        sql = "SELECT * FROM c WHERE " + " AND ".join(clauses)
        docs = self._query(sql, params)
        return [DataSource.model_validate(d) for d in docs]

    # ConstitutionalAssessment

    def save_assessment(self, assessment: ConstitutionalAssessment) -> ConstitutionalAssessment:
        doc = assessment.model_dump(mode="json")
        doc["id"] = assessment.assessment_id
        doc["partitionKey"] = assessment.data_source_id
        doc["type"] = _TYPE_ASSESSMENT
        self._upsert(doc)
        return assessment

    def get_assessments_for_source(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        docs = self._query(
            "SELECT * FROM c WHERE c.type = @type AND c.data_source_id = @dsid",
            [{"name": "@type", "value": _TYPE_ASSESSMENT}, {"name": "@dsid", "value": data_source_id}],
            partition_key=data_source_id,
        )
        return [ConstitutionalAssessment.model_validate(d) for d in docs]

    def get_current_assessments(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        docs = self._query(
            "SELECT * FROM c WHERE c.type = @type AND c.data_source_id = @dsid AND c.is_current = true",
            [{"name": "@type", "value": _TYPE_ASSESSMENT}, {"name": "@dsid", "value": data_source_id}],
            partition_key=data_source_id,
        )
        return [ConstitutionalAssessment.model_validate(d) for d in docs]

    # AgentGovernanceAssignment

    def save_assignment(self, assignment: AgentGovernanceAssignment) -> AgentGovernanceAssignment:
        doc = assignment.model_dump(mode="json")
        doc["id"] = assignment.assignment_id
        doc["partitionKey"] = assignment.data_source_id
        doc["type"] = _TYPE_ASSIGNMENT
        self._upsert(doc)
        return assignment

    def get_assignments_for_source(self, data_source_id: str) -> list[AgentGovernanceAssignment]:
        docs = self._query(
            "SELECT * FROM c WHERE c.type = @type AND c.data_source_id = @dsid AND c.status = 'active'",
            [{"name": "@type", "value": _TYPE_ASSIGNMENT}, {"name": "@dsid", "value": data_source_id}],
            partition_key=data_source_id,
        )
        return [AgentGovernanceAssignment.model_validate(d) for d in docs]

    # HandoffChainDefinition

    def save_chain(self, chain: HandoffChainDefinition) -> HandoffChainDefinition:
        doc = chain.model_dump(mode="json")
        doc["id"] = chain.chain_id
        doc["partitionKey"] = chain.data_source_id
        doc["type"] = _TYPE_CHAIN
        self._upsert(doc)
        return chain

    def get_chain_for_source(self, data_source_id: str) -> HandoffChainDefinition | None:
        docs = self._query(
            "SELECT * FROM c WHERE c.type = @type AND c.data_source_id = @dsid AND c.status = 'active'",
            [{"name": "@type", "value": _TYPE_CHAIN}, {"name": "@dsid", "value": data_source_id}],
            partition_key=data_source_id,
        )
        return HandoffChainDefinition.model_validate(docs[0]) if docs else None

    # FunctionalDomainPrecedence

    def save_precedence(self, precedence: FunctionalDomainPrecedence) -> FunctionalDomainPrecedence:
        doc = precedence.model_dump(mode="json")
        doc["id"] = precedence.precedence_id
        doc["partitionKey"] = _PRECEDENCE_PK
        doc["type"] = _TYPE_PRECEDENCE
        self._upsert(doc)
        return precedence

    def list_precedence(
        self, hazard_type: str | None = None, jurisdiction_id: str | None = None,
    ) -> list[FunctionalDomainPrecedence]:
        clauses = ["c.type = @type"]
        params: list[dict[str, object]] = [{"name": "@type", "value": _TYPE_PRECEDENCE}]
        if hazard_type:
            clauses.append("c.hazard_type = @ht")
            params.append({"name": "@ht", "value": hazard_type})
        if jurisdiction_id is not None:
            clauses.append("c.jurisdiction_id = @jid")
            params.append({"name": "@jid", "value": jurisdiction_id})
        sql = "SELECT * FROM c WHERE " + " AND ".join(clauses)
        docs = self._query(sql, params, partition_key=_PRECEDENCE_PK)
        return [FunctionalDomainPrecedence.model_validate(d) for d in docs]

    def resolve_precedence(
        self, hazard_type: str, jurisdiction_id: str | None = None,
    ) -> FunctionalDomainPrecedence | None:
        if jurisdiction_id:
            docs = self._query(
                "SELECT * FROM c WHERE c.type = @type"
                " AND c.hazard_type = @ht AND c.jurisdiction_id = @jid",
                [
                    {"name": "@type", "value": _TYPE_PRECEDENCE},
                    {"name": "@ht", "value": hazard_type},
                    {"name": "@jid", "value": jurisdiction_id},
                ],
                partition_key=_PRECEDENCE_PK,
            )
            if docs:
                return FunctionalDomainPrecedence.model_validate(docs[0])
        docs = self._query(
            "SELECT * FROM c WHERE c.type = @type AND c.hazard_type = @ht AND NOT IS_DEFINED(c.jurisdiction_id)",
            [
                {"name": "@type", "value": _TYPE_PRECEDENCE},
                {"name": "@ht", "value": hazard_type},
            ],
            partition_key=_PRECEDENCE_PK,
        )
        if not docs:
            docs = self._query(
                "SELECT * FROM c WHERE c.type = @type AND c.hazard_type = @ht AND c.jurisdiction_id = null",
                [
                    {"name": "@type", "value": _TYPE_PRECEDENCE},
                    {"name": "@ht", "value": hazard_type},
                ],
                partition_key=_PRECEDENCE_PK,
            )
        return FunctionalDomainPrecedence.model_validate(docs[0]) if docs else None

    # GovernanceAuditEntry

    def append_audit(self, entry: GovernanceAuditEntry) -> GovernanceAuditEntry:
        doc = entry.model_dump(mode="json")
        doc["id"] = entry.audit_entry_id
        doc["partitionKey"] = entry.data_source_id
        doc["type"] = _TYPE_AUDIT
        self._upsert(doc)
        return entry

    def get_audit_trail(
        self,
        data_source_id: str,
        action: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[GovernanceAuditEntry]:
        clauses = ["c.type = @type", "c.data_source_id = @dsid"]
        params: list[dict[str, object]] = [
            {"name": "@type", "value": _TYPE_AUDIT},
            {"name": "@dsid", "value": data_source_id},
        ]
        if action:
            clauses.append("c.action = @action")
            params.append({"name": "@action", "value": action})
        if from_dt:
            clauses.append("c.timestamp >= @from_dt")
            params.append({"name": "@from_dt", "value": from_dt.isoformat()})
        if to_dt:
            clauses.append("c.timestamp <= @to_dt")
            params.append({"name": "@to_dt", "value": to_dt.isoformat()})
        sql = "SELECT * FROM c WHERE " + " AND ".join(clauses) + " ORDER BY c.timestamp DESC"
        docs = self._query(sql, params, partition_key=data_source_id)
        return [GovernanceAuditEntry.model_validate(d) for d in docs]
