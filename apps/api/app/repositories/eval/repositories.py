"""Cosmos-backed repositories for the LLM Evaluation Framework.

Pattern mirrors `apps/api/app/repositories/governance_repository.py`:
auto-Cosmos when `COSMOS_ENDPOINT` is set, otherwise in-memory fallback for
tests. Each repo is single-responsibility — datasets, runs, metrics, audit.

Container layout (all under DB `disaster-hub`):
- `eval-datasets`   pk=/datasetId       — dataset versions, cases, manifests
- `eval-runs`       pk=/runId           — runs, scorecards, traces, infra
- `eval-metrics`    pk=/metricId        — metric defs, judges, baselines
- `eval-audit`      pk=/runId-or-default — append-only audit ledger (FR-022)
"""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from typing import Any

from ama_eval_core.audit import AuditAction, AuditEmitter, make_event
from ama_eval_core.models import (
    AuditEvent,
    Baseline,
    EvaluationCase,
    EvaluationDatasetVersion,
    EvaluationRun,
    JudgeModelVersion,
    MetricDefinitionVersion,
    Scorecard,
)

logger = logging.getLogger(__name__)


# Cosmos system properties returned with every read/query result. They are not
# part of any AMA model (which use ``extra="forbid"``) and must be stripped
# before deserialisation.
_COSMOS_SYSTEM_FIELDS: tuple[str, ...] = ("_rid", "_self", "_etag", "_attachments", "_ts")


def _strip_system_fields(d: dict[str, Any], *extra: str) -> dict[str, Any]:
    """Remove Cosmos and AMA-internal system fields from a fetched document.

    AMA repos add ``id``/``kind`` (and sometimes ``metricId``) at write time and
    Cosmos echoes back ``_rid``, ``_self``, ``_etag``, ``_attachments``, ``_ts``
    on every read. None of those belong on the strict pydantic models. Any
    ``extra`` AMA-internal keys (e.g. ``metricId``) can be passed positionally.
    """

    for k in _COSMOS_SYSTEM_FIELDS:
        d.pop(k, None)
    d.pop("id", None)
    d.pop("kind", None)
    for k in extra:
        d.pop(k, None)
    return d


# ---------------------------------------------------------------------------
# Cosmos helpers
# ---------------------------------------------------------------------------


def _build_container(name: str) -> Any:
    from app.core.cosmos import create_cosmos_client as CosmosClient
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_ENDPOINT"]
    database = os.environ.get("COSMOS_DATABASE", "disaster-hub")
    credential = DefaultAzureCredential()
    client = CosmosClient(endpoint, credential=credential)
    return client.get_database_client(database).get_container_client(name)


class _MemBackend:
    """Thread-safe in-memory key-value store keyed by (partition, id)."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def upsert(self, partition: str, item_id: str, doc: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._store[(partition, item_id)] = dict(doc)
            return dict(doc)

    def get(self, partition: str, item_id: str) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._store[(partition, item_id)]) if (partition, item_id) in self._store else None

    def query(self, predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(d) for d in self._store.values() if predicate(d)]

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(d) for d in self._store.values()]


def _coerce(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True)


# ---------------------------------------------------------------------------
# DatasetRepository
# ---------------------------------------------------------------------------


class DatasetRepository:
    def __init__(self, container: Any | None = None) -> None:
        if container is not None:
            self._cosmos = container
            self._mem = None
        elif os.environ.get("COSMOS_ENDPOINT"):
            self._cosmos = _build_container("eval_datasets")
            self._mem = None
        else:
            self._cosmos = None
            self._mem = _MemBackend()

    def _put(self, doc: dict[str, Any]) -> None:
        if self._cosmos is not None:
            self._cosmos.upsert_item(doc)
        else:
            assert self._mem is not None
            self._mem.upsert(doc["datasetId"], doc["id"], doc)

    def _get(self, dataset_id: str, item_id: str) -> dict[str, Any] | None:
        if self._cosmos is not None:
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                return self._cosmos.read_item(item=item_id, partition_key=dataset_id)
            except CosmosResourceNotFoundError:
                return None
        assert self._mem is not None
        return self._mem.get(dataset_id, item_id)

    def save_version(self, version: EvaluationDatasetVersion) -> EvaluationDatasetVersion:
        doc = {**_coerce(version), "id": f"version:{version.version}", "kind": "version"}
        self._put(doc)
        return version

    def get_version(self, dataset_id: str, version: str) -> EvaluationDatasetVersion | None:
        d = self._get(dataset_id, f"version:{version}")
        if not d:
            return None
        _strip_system_fields(d)
        return EvaluationDatasetVersion(**d)

    def save_case(self, case: EvaluationCase) -> EvaluationCase:
        doc = {**_coerce(case), "id": f"case:{case.caseId}:{case.version}", "kind": "case"}
        self._put(doc)
        return case

    def list_cases(self, dataset_id: str, version: str | None = None) -> list[EvaluationCase]:
        if self._mem is not None:
            docs = self._mem.query(lambda d: d.get("kind") == "case" and d.get("datasetId") == dataset_id)
        else:
            assert self._cosmos is not None
            query = "SELECT * FROM c WHERE c.kind='case' AND c.datasetId=@d"
            params = [{"name": "@d", "value": dataset_id}]
            if version:
                query += " AND c.version=@v"
                params.append({"name": "@v", "value": version})
            docs = list(self._cosmos.query_items(query=query, parameters=params, enable_cross_partition_query=False))
        if version:
            docs = [d for d in docs if d.get("version") == version]
        for d in docs:
            _strip_system_fields(d)
        return [EvaluationCase(**d) for d in docs]


# ---------------------------------------------------------------------------
# RunRepository
# ---------------------------------------------------------------------------


class RunRepository:
    def __init__(self, container: Any | None = None) -> None:
        if container is not None:
            self._cosmos = container
            self._mem = None
        elif os.environ.get("COSMOS_ENDPOINT"):
            self._cosmos = _build_container("eval_runs")
            self._mem = None
        else:
            self._cosmos = None
            self._mem = _MemBackend()

    def _put(self, doc: dict[str, Any]) -> None:
        if self._cosmos is not None:
            self._cosmos.upsert_item(doc)
        else:
            assert self._mem is not None
            self._mem.upsert(doc["runId"], doc["id"], doc)

    def save_run(self, run: EvaluationRun) -> EvaluationRun:
        doc = {**_coerce(run), "id": f"run:{run.runId}", "kind": "run"}
        self._put(doc)
        return run

    def get_run(self, run_id: str) -> EvaluationRun | None:
        if self._mem is not None:
            d = self._mem.get(run_id, f"run:{run_id}")
        else:
            assert self._cosmos is not None
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                d = self._cosmos.read_item(item=f"run:{run_id}", partition_key=run_id)
            except CosmosResourceNotFoundError:
                d = None
        if not d:
            return None
        _strip_system_fields(d)
        return EvaluationRun(**d)

    def list_runs(self, *, status: str | None = None, mode: str | None = None, limit: int = 50) -> list[EvaluationRun]:
        if self._mem is not None:
            docs = self._mem.query(lambda d: d.get("kind") == "run")
        else:
            assert self._cosmos is not None
            docs = list(
                self._cosmos.query_items(
                    query="SELECT * FROM c WHERE c.kind='run'",
                    enable_cross_partition_query=True,
                )
            )
        if status:
            docs = [d for d in docs if d.get("status") == status]
        if mode:
            docs = [d for d in docs if d.get("mode") == mode]
        docs.sort(key=lambda d: d.get("createdAt", ""), reverse=True)
        for d in docs:
            _strip_system_fields(d)
        return [EvaluationRun(**d) for d in docs[:limit]]

    def save_scorecard(self, scorecard: Scorecard) -> Scorecard:
        doc = {
            **_coerce(scorecard),
            "id": f"scorecard:{scorecard.runId}",
            "kind": "scorecard",
            "runId": scorecard.runId,
        }
        self._put(doc)
        return scorecard

    def get_scorecard(self, run_id: str) -> Scorecard | None:
        if self._mem is not None:
            d = self._mem.get(run_id, f"scorecard:{run_id}")
        else:
            assert self._cosmos is not None
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                d = self._cosmos.read_item(item=f"scorecard:{run_id}", partition_key=run_id)
            except CosmosResourceNotFoundError:
                d = None
        if not d:
            return None
        _strip_system_fields(d)
        return Scorecard(**d)


# ---------------------------------------------------------------------------
# MetricRepository
# ---------------------------------------------------------------------------


class MetricRepository:
    def __init__(self, container: Any | None = None) -> None:
        if container is not None:
            self._cosmos = container
            self._mem = None
        elif os.environ.get("COSMOS_ENDPOINT"):
            self._cosmos = _build_container("eval_metric_definitions")
            self._mem = None
        else:
            self._cosmos = None
            self._mem = _MemBackend()

    def save_metric(self, metric: MetricDefinitionVersion) -> MetricDefinitionVersion:
        doc = {**_coerce(metric), "id": f"metric:{metric.metricId}:{metric.version}", "kind": "metric"}
        self._put(doc, metric.metricId)
        return metric

    def save_judge(self, judge: JudgeModelVersion) -> JudgeModelVersion:
        doc = {
            **_coerce(judge),
            "id": f"judge:{judge.judgeId}:{judge.version}",
            "kind": "judge",
            "metricId": judge.judgeId,
        }
        self._put(doc, judge.judgeId)
        return judge

    def save_baseline(self, baseline: Baseline) -> Baseline:
        doc = {
            **_coerce(baseline),
            "id": f"baseline:{baseline.datasetId}:{baseline.modelTier}:{baseline.environment}",
            "kind": "baseline",
            "metricId": f"{baseline.datasetId}-{baseline.modelTier}-{baseline.environment}",
        }
        self._put(doc, doc["metricId"])
        return baseline

    def get_baseline(self, dataset_id: str, model_tier: str, environment: str) -> Baseline | None:
        partition = f"{dataset_id}-{model_tier}-{environment}"
        item_id = f"baseline:{dataset_id}:{model_tier}:{environment}"
        if self._mem is not None:
            d = self._mem.get(partition, item_id)
        else:
            assert self._cosmos is not None
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            try:
                d = self._cosmos.read_item(item=item_id, partition_key=partition)
            except CosmosResourceNotFoundError:
                d = None
        if not d:
            return None
        _strip_system_fields(d, "metricId")
        return Baseline(**d)

    def list_metrics(self) -> list[MetricDefinitionVersion]:
        if self._mem is not None:
            docs = self._mem.query(lambda d: d.get("kind") == "metric")
        else:
            assert self._cosmos is not None
            docs = list(
                self._cosmos.query_items(
                    query="SELECT * FROM c WHERE c.kind='metric'",
                    enable_cross_partition_query=True,
                )
            )
        for d in docs:
            _strip_system_fields(d)
        return [MetricDefinitionVersion(**d) for d in docs]

    def _put(self, doc: dict[str, Any], partition: str) -> None:
        if self._cosmos is not None:
            self._cosmos.upsert_item(doc)
        else:
            assert self._mem is not None
            self._mem.upsert(partition, doc["id"], doc)


# ---------------------------------------------------------------------------
# AuditRepository — append-only ledger (FR-022)
# ---------------------------------------------------------------------------


class AuditRepository(AuditEmitter):
    """Append-only audit ledger. Implements `AuditEmitter` Protocol from eval-core."""

    def __init__(self, container: Any | None = None) -> None:
        if container is not None:
            self._cosmos = container
            self._mem = None
        elif os.environ.get("COSMOS_ENDPOINT"):
            self._cosmos = _build_container("eval_audit")
            self._mem = None
        else:
            self._cosmos = None
            self._mem = _MemBackend()

    def emit(self, event: AuditEvent) -> AuditEvent:
        doc = {**_coerce(event), "id": event.auditId, "kind": "audit"}
        partition = event.runId or "default"
        if "runId" not in doc or doc["runId"] is None:
            doc["runId"] = partition
        if self._cosmos is not None:
            self._cosmos.create_item(doc)  # append-only
        else:
            assert self._mem is not None
            self._mem.upsert(partition, event.auditId, doc)
        return event

    def emit_action(
        self,
        *,
        action: AuditAction | str,
        principal: str,
        subject_type: str,
        subject_id: str,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        return self.emit(
            make_event(
                action=action,
                principal=principal,
                subject_type=subject_type,
                subject_id=subject_id,
                run_id=run_id,
                metadata=metadata,
            )
        )

    def list_for_run(self, run_id: str) -> list[AuditEvent]:
        if self._mem is not None:
            docs = self._mem.query(lambda d: d.get("kind") == "audit" and d.get("runId") == run_id)
        else:
            assert self._cosmos is not None
            docs = list(
                self._cosmos.query_items(
                    query="SELECT * FROM c WHERE c.kind='audit' AND c.runId=@r",
                    parameters=[{"name": "@r", "value": run_id}],
                    partition_key=run_id,
                )
            )
        for d in docs:
            _strip_system_fields(d)
        docs.sort(key=lambda d: d.get("timestamp", ""))
        return [AuditEvent(**d) for d in docs]


__all__ = [
    "AuditRepository",
    "DatasetRepository",
    "MetricRepository",
    "RunRepository",
]
