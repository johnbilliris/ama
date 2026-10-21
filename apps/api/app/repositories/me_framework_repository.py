"""Cosmos DB repository for the ``recovery-programmes`` container.

Partition key: ``/incident_id``

Stores M&E frameworks, program-logic models, and evaluation reports
used by the monitoring agent.

FRs: FR-029, FR-030 | Research: R-008
"""

import logging
import os
from typing import Any, TypedDict


class MEFrameworkDocument(TypedDict, total=False):
    id: str
    framework_id: str
    model_id: str
    report_id: str
    incident_id: str
    document_type: str
    program_name: str
    affected_community_definition: str
    status: str
    created_at: str
    created_by: str
    updated_at: str | None
    selected_outcomes: list[dict[str, object]]
    program_logic_id: str | None
    active_evaluation_domains: list[str]
    standards_of_success: list[dict[str, object]]
    indicator_collection_schedule: list[dict[str, object]]
    evaluation_reports: list[dict[str, object]]
    model_type: str
    resources_inputs: list[dict[str, object]]
    activities: list[dict[str, object]]
    outputs: list[dict[str, object]]
    intermediate_outcomes: list[dict[str, object]]
    final_outcomes: list[dict[str, object]]
    outcome_chain_links: list[dict[str, object]]
    timeline_months: int | None
    evaluation_period_start: str
    evaluation_period_end: str
    generated_by: str
    domain_findings: dict[str, dict[str, object]]
    summary: str


logger = logging.getLogger(__name__)


def _build_cosmos_client() -> Any:
    """Build a CosmosClient from the ``COSMOS_ENDPOINT`` env var."""
    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    credential = DefaultAzureCredential()
    return CosmosClient(endpoint, credential=credential)


class MEFrameworkRepository:
    """Read/write operations against the ``recovery-programmes`` Cosmos DB container.

    When ``COSMOS_ENDPOINT`` is set the repository talks to Cosmos DB.
    Otherwise it falls back to an in-memory dict so that unit / contract
    tests keep working without infrastructure.
    """

    def __init__(self, cosmos_client: Any = None, database_name: str = "disaster-hub"):
        self._db_name = database_name
        self._container_name = "recovery-programmes"
        self._in_memory: dict[str, MEFrameworkDocument] = {}

        if cosmos_client is not None:
            self._client = cosmos_client
        elif os.environ.get("COSMOS_ENDPOINT"):
            try:
                self._client = _build_cosmos_client()
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "MEFrameworkRepository: Cosmos init failed (%s); falling back to in-memory store",
                    exc,
                )
                self._client = None
        else:
            self._client = None

    def _get_container(self) -> Any:
        if self._client is None:
            return None
        db = self._client.get_database_client(self._db_name)
        return db.get_container_client(self._container_name)

    # ------------------------------------------------------------------
    # M&E Framework CRUD
    # ------------------------------------------------------------------

    async def create_framework(self, framework_doc: MEFrameworkDocument) -> MEFrameworkDocument:
        """Upsert an M&E framework document."""
        container = self._get_container()
        if container:
            framework_doc.setdefault("id", framework_doc.get("framework_id", ""))
            container.upsert_item(framework_doc)
        else:
            key = framework_doc.get("framework_id", framework_doc.get("id", ""))
            self._in_memory[key] = framework_doc
        return framework_doc

    async def get_framework(self, framework_id: str, incident_id: str) -> MEFrameworkDocument | None:
        """Read a single framework by id with partition key ``incident_id``."""
        container = self._get_container()
        if container:
            try:
                return container.read_item(framework_id, partition_key=incident_id)
            except Exception:
                return None
        return self._in_memory.get(framework_id)

    async def update_framework(self, framework_doc: MEFrameworkDocument) -> MEFrameworkDocument:
        """Upsert an updated framework document."""
        return await self.create_framework(framework_doc)

    async def list_frameworks(
        self,
        incident_id: str | None = None,
        status: str | None = None,
    ) -> list[MEFrameworkDocument]:
        """Query frameworks with optional incident and status filters."""
        container = self._get_container()
        if container:
            clauses = ["c.document_type = 'me_framework'"]
            params: list[dict[str, object]] = []
            if incident_id is not None:
                clauses.append("c.incident_id = @incident_id")
                params.append({"name": "@incident_id", "value": incident_id})
            if status is not None:
                clauses.append("c.status = @status")
                params.append({"name": "@status", "value": status})
            query = "SELECT * FROM c WHERE " + " AND ".join(clauses) + " ORDER BY c._ts DESC"
            return list(
                container.query_items(
                    query,
                    parameters=params,
                    enable_cross_partition_query=(incident_id is None),
                )
            )
        # In-memory fallback
        results = [d for d in self._in_memory.values() if d.get("document_type") == "me_framework"]
        if incident_id is not None:
            results = [d for d in results if d.get("incident_id") == incident_id]
        if status is not None:
            results = [d for d in results if d.get("status") == status]
        return results

    # ------------------------------------------------------------------
    # Program Logic
    # ------------------------------------------------------------------

    async def create_program_logic(self, logic_doc: MEFrameworkDocument) -> MEFrameworkDocument:
        """Upsert a program-logic model document."""
        container = self._get_container()
        if container:
            logic_doc.setdefault("id", logic_doc.get("model_id", ""))
            logic_doc.setdefault("document_type", "program_logic")
            container.upsert_item(logic_doc)
        else:
            key = logic_doc.get("model_id", logic_doc.get("id", ""))
            self._in_memory[key] = logic_doc
        return logic_doc

    async def get_program_logic(self, model_id: str, incident_id: str) -> MEFrameworkDocument | None:
        """Read a program-logic model by id with partition key ``incident_id``."""
        container = self._get_container()
        if container:
            try:
                return container.read_item(model_id, partition_key=incident_id)
            except Exception:
                return None
        return self._in_memory.get(model_id)

    # ------------------------------------------------------------------
    # Evaluation Reports
    # ------------------------------------------------------------------

    async def create_evaluation_report(self, report_doc: MEFrameworkDocument) -> MEFrameworkDocument:
        """Upsert an evaluation report document."""
        container = self._get_container()
        if container:
            report_doc.setdefault("id", report_doc.get("report_id", ""))
            report_doc.setdefault("document_type", "evaluation_report")
            container.upsert_item(report_doc)
        else:
            key = report_doc.get("report_id", report_doc.get("id", ""))
            self._in_memory[key] = report_doc
        return report_doc

    async def get_evaluation_report(self, report_id: str, incident_id: str) -> MEFrameworkDocument | None:
        """Read an evaluation report by id with partition key ``incident_id``."""
        container = self._get_container()
        if container:
            try:
                return container.read_item(report_id, partition_key=incident_id)
            except Exception:
                return None
        return self._in_memory.get(report_id)

    async def list_evaluation_reports(
        self,
        framework_id: str,
        incident_id: str,
    ) -> list[MEFrameworkDocument]:
        """List evaluation reports for a given framework within an incident."""
        container = self._get_container()
        if container:
            query = (
                "SELECT * FROM c "
                "WHERE c.document_type = 'evaluation_report' "
                "AND c.framework_id = @framework_id "
                "ORDER BY c._ts DESC"
            )
            params: list[dict[str, object]] = [
                {"name": "@framework_id", "value": framework_id},
            ]
            return list(
                container.query_items(
                    query,
                    parameters=params,
                    partition_key=incident_id,
                )
            )
        # In-memory fallback
        return [
            d
            for d in self._in_memory.values()
            if d.get("document_type") == "evaluation_report"
            and d.get("framework_id") == framework_id
            and d.get("incident_id") == incident_id
        ]
