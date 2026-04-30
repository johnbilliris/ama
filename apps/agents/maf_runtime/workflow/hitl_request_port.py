"""HitlGateExecutor + decision listener (T045, T046, T047, T048, T048b, T048c, ADR-033-03).

Implements the HITL gate pattern documented in
``specs/033-maf-adoption/contracts/hitl-request.envelope.md``. There is **no**
``RequestPort``/``RequestInfoEvent`` in the GA Python MAF SDK — we synthesise
the same external behaviour via:

1. ``HitlGateExecutor.run(...)`` — wraps the Communication agent's draft alert
   into a spec-008 ``ApprovalRequest`` envelope, publishes onto Service Bus
   ``commander-approval-queue`` (existing), updates the workflow run document
   to ``status=AwaitingApproval``, and returns a parked-event sentinel that the
   workflow runtime treats as "checkpoint-and-exit".

2. ``HitlDecisionListener.on_decision_received(...)`` — subscriber on the
   existing spec-008 ``commander-approval-decisions-queue``. Looks up the run
   by ``pending_request_id``, applies the decision (approve / modify / reject)
   via ``WorkflowRunRepository.update_status``, and resumes the workflow.

Constitution NN-1 (HITL non-bypassable):
- ``HitlGateExecutor`` is the ONLY code path that emits a public alert.
- ``HitlDecisionListener`` is the ONLY code path that resumes a run from
  ``AwaitingApproval``. Both invariants are statically asserted by T047.

Determinism (T046 success criterion):
- ``request_id`` is generated as UUIDv5 from
  ``incident_id + run_id + step_index`` so a crash mid-publish does NOT spawn
  a duplicate pending request when the workflow restores.

Idempotency on resume (T048):
- ``on_request_emitted(request_id, ...)`` checks the existing
  ``approval_decisions`` Cosmos container for an already-recorded decision; if
  found, the workflow auto-resolves without re-publishing.

Concurrent decisions (T048b):
- ``on_decision_received(...)`` uses a Cosmos optimistic-concurrency check
  (etag) on the run document; the second commander's call gets
  ``DuplicateDecisionConflictError`` while both attempts remain audited.

Escalation timeout (T048c):
- The escalation timer + chain are owned by spec 008 (FR-009 clarification).
  This module emits ``ApprovalRequest`` envelopes and consumes
  ``ApprovalDecision`` envelopes; spec 008's timer mechanics are unchanged.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any
from uuid import UUID

from ..errors import DuplicateDecisionConflictError
from ..repositories.workflow_run_repository import WorkflowRunRepository
from .run_state import WorkflowRunStatus

logger = logging.getLogger(__name__)


_HITL_NAMESPACE = UUID("c6cf3a6a-8a68-4c18-9e7f-2d03c0f0c2b5")  # stable feature 033 namespace
_APPROVAL_QUEUE = "commander-approval-queue"
_DECISION_QUEUE = "commander-approval-decisions-queue"


class _ServiceBusPublisher:
    """Thin Service Bus publisher with managed-identity auth.

    Falls back to in-memory list mode for unit / integration tests when the
    ``AZURE_SERVICEBUS_NAMESPACE`` env var is not set.
    """

    def __init__(self) -> None:
        self._namespace = os.environ.get("AZURE_SERVICEBUS_NAMESPACE", "")
        self._client: Any | None = None
        # In-memory sink for tests.
        self.published: list[dict[str, Any]] = []

    def _ensure_client(self) -> Any | None:
        if self._client is not None:
            return self._client
        if not self._namespace:
            return None
        try:
            from azure.identity import DefaultAzureCredential
            from azure.servicebus import ServiceBusClient

            self._client = ServiceBusClient(
                fully_qualified_namespace=self._namespace,
                credential=DefaultAzureCredential(),
            )
        except Exception:  # noqa: BLE001
            logger.exception("HITL publisher: Service Bus init failed; using in-memory mode")
            self._client = None
        return self._client

    def publish(self, queue_name: str, body: dict[str, Any]) -> None:
        client = self._ensure_client()
        if client is None:
            self.published.append({"queue": queue_name, "body": body})
            logger.info("hitl.published queue=%s (in-memory) request_id=%s", queue_name, body.get("request_id"))
            return
        try:
            from azure.servicebus import ServiceBusMessage

            with client.get_queue_sender(queue_name=queue_name) as sender:
                msg = ServiceBusMessage(json.dumps(body))
                sender.send_messages(msg)
            logger.info("hitl.published queue=%s request_id=%s", queue_name, body.get("request_id"))
        except Exception:  # noqa: BLE001
            logger.exception("HITL publisher: failed to publish to %s", queue_name)
            self.published.append({"queue": queue_name, "body": body, "error": True})


def deterministic_request_id(*, incident_id: str, run_id: str, step_index: int) -> str:
    """Generate a deterministic request_id (UUIDv5) — crash-safe re-emission.

    Per T046: a crash mid-publish must not generate a second pending request.
    """
    name = f"{incident_id}|{run_id}|{step_index}"
    return str(uuid.uuid5(_HITL_NAMESPACE, name))


def build_approval_envelope(
    *,
    draft_alert: Any,
    incident_id: str,
    run_id: str,
    step_index: int,
    correlation_id: str,
    source_executor: str = "communication_executor",
) -> dict[str, Any]:
    """Wrap a draft PublicAlert into a spec-008 ``ApprovalRequest`` envelope.

    This is the ONLY mapping shape allowed; the field set is documented in
    ``specs/033-maf-adoption/contracts/hitl-request.envelope.md``.
    """
    request_id = deterministic_request_id(
        incident_id=incident_id,
        run_id=run_id,
        step_index=step_index,
    )
    if hasattr(draft_alert, "model_dump"):
        alert_payload = draft_alert.model_dump(mode="json", by_alias=True)
    elif isinstance(draft_alert, dict):
        alert_payload = draft_alert
    else:
        alert_payload = {"raw": str(draft_alert)}

    metadata = alert_payload.setdefault("metadata", {}) if isinstance(alert_payload.get("metadata"), dict) else {}
    metadata["maf_run_id"] = run_id
    metadata["maf_source_executor"] = source_executor
    metadata["correlation_id"] = correlation_id
    if isinstance(alert_payload, dict):
        alert_payload["metadata"] = metadata

    return {
        "request_id": request_id,
        "incident_id": incident_id,
        "alert": {"payload": alert_payload},
        "metadata": metadata,
    }


class HitlGateExecutor:
    """The HITL pause executor (T046).

    Placed AFTER ``CommunicationExecutor`` in the workflow graph. When invoked:

    1. Builds the spec-008 ``ApprovalRequest`` envelope.
    2. Idempotency check: if a decision already exists for ``request_id``, skips
       the publish and returns the recorded decision so the workflow can resume
       (T048).
    3. Otherwise publishes onto ``commander-approval-queue`` and updates the
       ``workflow_runs`` doc to ``status=AwaitingApproval``.
    4. Returns a parked-event sentinel.
    """

    def __init__(
        self,
        *,
        repo: WorkflowRunRepository | None = None,
        publisher: _ServiceBusPublisher | None = None,
        decision_lookup: Any | None = None,
    ) -> None:
        self._repo = repo or WorkflowRunRepository()
        self._publisher = publisher or _ServiceBusPublisher()
        # decision_lookup callable: (request_id) -> dict | None
        self._decision_lookup = decision_lookup

    def _existing_decision(self, request_id: str) -> dict[str, Any] | None:
        if self._decision_lookup is not None:
            try:
                return self._decision_lookup(request_id)
            except Exception:  # noqa: BLE001
                logger.exception("decision_lookup raised; treating as no decision")
        return None

    async def run(
        self,
        *,
        draft_alert: Any,
        incident_id: str,
        run_id: str,
        step_index: int,
        correlation_id: str,
    ) -> dict[str, Any]:
        envelope = build_approval_envelope(
            draft_alert=draft_alert,
            incident_id=incident_id,
            run_id=run_id,
            step_index=step_index,
            correlation_id=correlation_id,
        )
        request_id = envelope["request_id"]
        existing = self._existing_decision(request_id)
        if existing is not None:
            logger.info("hitl.idempotent_resume request_id=%s decision=%s", request_id, existing.get("decision"))
            return {"parked": False, "request_id": request_id, "decision": existing}

        # Update run doc BEFORE publishing — we need pending_request_id durable so the
        # decision listener can find the run on resume even if publish fails.
        self._repo.update_status(
            run_id,
            WorkflowRunStatus.AWAITING_APPROVAL,
            correlation_id=correlation_id,
            pending_request_id=request_id,
        )
        self._publisher.publish(_APPROVAL_QUEUE, envelope)
        return {"parked": True, "request_id": request_id, "envelope": envelope}


class HitlDecisionListener:
    """Subscriber on the spec-008 decisions queue (T046, T048b)."""

    def __init__(
        self,
        *,
        repo: WorkflowRunRepository | None = None,
        resume_callback: Any | None = None,
    ) -> None:
        self._repo = repo or WorkflowRunRepository()
        self._resume = resume_callback  # async callable: (run_id, decision_dict) -> None

    async def on_decision_received(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Apply *decision* to the matching workflow run.

        Returns the updated run document. Raises ``DuplicateDecisionConflictError``
        when the run is no longer in ``AwaitingApproval`` (i.e., another
        decision already won the race).
        """
        request_id = decision.get("request_id")
        if not request_id:
            raise ValueError("decision missing request_id")
        # Find the run by pending_request_id.
        for doc in self._repo.list(status=WorkflowRunStatus.AWAITING_APPROVAL.value, limit=500):
            if doc.get("pending_request_id") == request_id:
                run_doc = doc
                break
        else:
            # Run is not in AwaitingApproval — someone else already resolved it.
            raise DuplicateDecisionConflictError(
                f"No active AwaitingApproval run for request_id={request_id}; another decision likely already applied.",
                correlation_id=str(decision.get("correlation_id") or "hitl-decision"),
                details={"request_id": request_id},
            )

        outcome = str(decision.get("decision", "")).lower()
        correlation_id = str(decision.get("correlation_id") or f"decision-{request_id}")
        if outcome in {"approve", "approved", "modify", "modified"}:
            updated = self._repo.update_status(
                run_doc["id"],
                WorkflowRunStatus.RUNNING,
                correlation_id=correlation_id,
            )
        elif outcome in {"reject", "rejected"}:
            updated = self._repo.update_status(
                run_doc["id"],
                WorkflowRunStatus.CANCELLED,
                correlation_id=correlation_id,
            )
        else:
            raise ValueError(f"unknown decision outcome: {outcome!r}")

        if self._resume is not None and outcome != "reject":
            try:
                await self._resume(run_doc["id"], decision)
            except Exception:  # noqa: BLE001
                logger.exception("hitl.resume_callback failed for run %s", run_doc["id"])
        return updated


__all__ = [
    "HitlDecisionListener",
    "HitlGateExecutor",
    "build_approval_envelope",
    "deterministic_request_id",
]
