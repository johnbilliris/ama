"""Externalised LLM budget tracker (spec 032 FR-P02, ADR addresses Rubric 2.2).

Replaces the in-memory per-instance counter in ``llm_mixin.py`` so that
process restarts don't reset the monthly budget. Stored in Cosmos container
``llm_budgets`` (PK ``/scope``); falls back to an in-memory implementation
when Cosmos isn't configured (dev / unit tests).

Public API:
  - ``BudgetTracker`` (Protocol-shaped) — what call sites consume.
  - ``InMemoryBudgetTracker`` — fallback used when COSMOS_ENDPOINT isn't set.
  - ``CosmosBudgetTracker`` — production implementation; auto-selected via
    ``build_budget_tracker()`` when COSMOS_ENDPOINT is set.

Telemetry: emits ``llm.cost.aud_micros`` counter and ``llm.budget.warning``
counter via the metrics module. AUD micros are kept as ``int`` to avoid
floating-point drift in the cumulative counter.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

logger = logging.getLogger(__name__)

# 1 AUD = 1_000_000 micros. We track in micros to avoid floating-point loss.
MICROS_PER_AUD = 1_000_000


@dataclass
class BudgetSnapshot:
    """Snapshot of a budget scope at a point in time."""

    scope: str
    period_yyyymm: str
    total_aud_micros: int
    monthly_budget_aud: float
    last_updated: datetime

    @property
    def total_aud(self) -> float:
        return self.total_aud_micros / MICROS_PER_AUD

    @property
    def remaining_aud(self) -> float:
        return max(self.monthly_budget_aud - self.total_aud, 0.0)

    @property
    def burn_fraction(self) -> float:
        if self.monthly_budget_aud <= 0:
            return 1.0
        return self.total_aud / self.monthly_budget_aud


class BudgetTracker(Protocol):
    """Persistent counter of cumulative LLM cost for a budget scope."""

    def add(
        self,
        scope: str,
        aud_micros: int,
        *,
        monthly_budget_aud: float,
        rehearsal_run_id: str | None = None,
        monitored_day: str | None = None,
    ) -> BudgetSnapshot:
        """Add cost; return the post-increment snapshot."""
        ...

    def get(self, scope: str) -> BudgetSnapshot | None:
        """Read the current snapshot for a scope (None if no record)."""
        ...


def _current_period() -> str:
    now = datetime.now(UTC)
    return f"{now.year:04d}{now.month:02d}"


class InMemoryBudgetTracker:
    """Process-local budget tracker (test/dev fallback)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._snapshots: dict[tuple[str, str], BudgetSnapshot] = {}

    def add(
        self,
        scope: str,
        aud_micros: int,
        *,
        monthly_budget_aud: float,
        rehearsal_run_id: str | None = None,
        monitored_day: str | None = None,
    ) -> BudgetSnapshot:
        period = _current_period()
        with self._lock:
            key = (scope, period)
            existing = self._snapshots.get(key)
            new_total = (existing.total_aud_micros if existing else 0) + max(aud_micros, 0)
            snap = BudgetSnapshot(
                scope=scope,
                period_yyyymm=period,
                total_aud_micros=new_total,
                monthly_budget_aud=monthly_budget_aud,
                last_updated=datetime.now(UTC),
            )
            self._snapshots[key] = snap
        _emit_metrics(
            snap,
            aud_micros,
            rehearsal_run_id=rehearsal_run_id,
            monitored_day=monitored_day,
        )
        return snap

    def get(self, scope: str) -> BudgetSnapshot | None:
        with self._lock:
            return self._snapshots.get((scope, _current_period()))


class CosmosBudgetTracker:
    """Cosmos-backed tracker: container ``llm_budgets``, PK ``/scope``.

    Documents are keyed by ``f"{scope}:{period_yyyymm}"`` so monthly periods
    don't collide. Uses an optimistic-concurrency upsert via patch operations
    (``_etag``) so concurrent agent processes don't lose increments.
    """

    def __init__(self, container: object | None = None, *, max_conflict_retries: int = 3) -> None:
        self._container = container or self._build_container()
        self._max_conflict_retries = max(0, max_conflict_retries)

    @staticmethod
    def _build_container() -> object | None:
        endpoint = os.getenv("COSMOS_ENDPOINT")
        database = os.getenv("COSMOS_DATABASE", "ama")
        if not endpoint:
            return None
        try:
            from azure.cosmos import CosmosClient  # type: ignore[import-untyped]
            from azure.identity import DefaultAzureCredential

            client = CosmosClient(endpoint, credential=DefaultAzureCredential())
            db = client.get_database_client(database)
            return db.get_container_client("llm_budgets")
        except Exception:  # noqa: BLE001
            logger.exception("Cosmos llm_budgets container init failed; falling back to in-memory")
            return None

    def add(
        self,
        scope: str,
        aud_micros: int,
        *,
        monthly_budget_aud: float,
        rehearsal_run_id: str | None = None,
        monitored_day: str | None = None,
    ) -> BudgetSnapshot:
        if self._container is None:
            return _fallback_tracker().add(
                scope,
                aud_micros,
                monthly_budget_aud=monthly_budget_aud,
                rehearsal_run_id=rehearsal_run_id,
                monitored_day=monitored_day,
            )

        period = _current_period()
        doc_id = f"{scope}:{period}"
        last_conflict: Exception | None = None
        doc: dict[str, object] | None = None
        for _attempt in range(self._max_conflict_retries + 1):
            try:
                existing = self._container.read_item(item=doc_id, partition_key=scope)
            except Exception as exc:  # noqa: BLE001
                if _is_not_found(exc):
                    doc = {
                        "id": doc_id,
                        "scope": scope,
                        "period_yyyymm": period,
                        "total_aud_micros": max(aud_micros, 0),
                        "monthly_budget_aud": monthly_budget_aud,
                        "last_updated": datetime.now(UTC).isoformat(),
                    }
                    self._container.upsert_item(doc)
                    break
                logger.warning("Cosmos read failed for budget scope=%s period=%s", scope, period, exc_info=True)
                return _fallback_tracker().add(
                    scope,
                    aud_micros,
                    monthly_budget_aud=monthly_budget_aud,
                    rehearsal_run_id=rehearsal_run_id,
                    monitored_day=monitored_day,
                )

            new_total = int(existing.get("total_aud_micros", 0)) + max(aud_micros, 0)
            doc = {
                **existing,
                "total_aud_micros": new_total,
                "monthly_budget_aud": monthly_budget_aud,
                "last_updated": datetime.now(UTC).isoformat(),
            }
            try:
                self._container.replace_item(
                    item=doc_id,
                    body=doc,
                    etag=existing.get("_etag"),
                    match_condition="IfMatch",
                )
                break
            except Exception as exc:  # noqa: BLE001
                if _is_conflict(exc):
                    last_conflict = exc
                    continue
                logger.warning("Cosmos replace failed for budget scope=%s period=%s", scope, period, exc_info=True)
                return _fallback_tracker().add(
                    scope,
                    aud_micros,
                    monthly_budget_aud=monthly_budget_aud,
                    rehearsal_run_id=rehearsal_run_id,
                    monitored_day=monitored_day,
                )
        else:
            if last_conflict is not None:
                raise RuntimeError("Budget update conflict after bounded retries") from last_conflict

        if doc is None:
            return _fallback_tracker().add(
                scope,
                aud_micros,
                monthly_budget_aud=monthly_budget_aud,
                rehearsal_run_id=rehearsal_run_id,
                monitored_day=monitored_day,
            )

        snap = BudgetSnapshot(
            scope=scope,
            period_yyyymm=period,
            total_aud_micros=int(doc["total_aud_micros"]),
            monthly_budget_aud=monthly_budget_aud,
            last_updated=datetime.now(UTC),
        )
        _emit_metrics(
            snap,
            aud_micros,
            rehearsal_run_id=rehearsal_run_id,
            monitored_day=monitored_day,
        )
        return snap

    def get(self, scope: str) -> BudgetSnapshot | None:
        if self._container is None:
            return None
        period = _current_period()
        doc_id = f"{scope}:{period}"
        try:
            doc = self._container.read_item(item=doc_id, partition_key=scope)
            return BudgetSnapshot(
                scope=scope,
                period_yyyymm=period,
                total_aud_micros=int(doc.get("total_aud_micros", 0)),
                monthly_budget_aud=float(doc.get("monthly_budget_aud", 0.0)),
                last_updated=datetime.fromisoformat(doc["last_updated"]),
            )
        except Exception:  # noqa: BLE001
            return None


def build_budget_tracker() -> BudgetTracker:
    """Pick the right backend based on environment."""
    if os.getenv("COSMOS_ENDPOINT"):
        return CosmosBudgetTracker()
    return _fallback_tracker()


_FALLBACK_TRACKER: InMemoryBudgetTracker | None = None


def _fallback_tracker() -> InMemoryBudgetTracker:
    global _FALLBACK_TRACKER
    if _FALLBACK_TRACKER is None:
        _FALLBACK_TRACKER = InMemoryBudgetTracker()
    return _FALLBACK_TRACKER


def _is_not_found(exc: Exception) -> bool:
    text = str(exc)
    return "NotFound" in text or "404" in text


def _is_conflict(exc: Exception) -> bool:
    text = str(exc)
    return "PreconditionFailed" in text or "412" in text or "409" in text


def _emit_metrics(
    snap: BudgetSnapshot,
    delta_micros: int,
    *,
    rehearsal_run_id: str | None = None,
    monitored_day: str | None = None,
) -> None:
    """Emit cost + warning customMetrics (FR-O03)."""
    try:
        from apps.api.app.observability.metrics import emit_counter

        emit_counter(
            "llm.cost.aud_micros",
            delta_micros,
            {
                "scope": snap.scope,
                "period": snap.period_yyyymm,
                "rehearsal_run_id": rehearsal_run_id or "",
                "monitored_day": monitored_day or "",
            },
            unit="uAUD",
        )
        if snap.burn_fraction >= 0.8:
            emit_counter("llm.budget.warning_total", 1, {"scope": snap.scope})
    except Exception:  # noqa: BLE001
        logger.debug("budget metrics emit failed", exc_info=True)
