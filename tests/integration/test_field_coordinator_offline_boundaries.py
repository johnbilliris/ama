"""T158 — Integration test: Field-Coordinator offline-decision boundaries
(FR-RAG-LS-02 ext; ADR-14; Plan §F-A5.4).

Asserts:

* (a) resource-allocation-local        → offline-safe
* (b) safety-escalation-local          → offline-safe
* (c) evacuation-centre-setup          → offline-safe
* (d) public-warning                   → REJECTED (queued for IC review)
* (e) cross-jurisdiction-mutual-aid    → REJECTED
* (f) state-escalation                 → REJECTED
* On reconnect, queued decisions emit ``approval_workflow_state == "pending"``
  via the audit-record builder.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# `common` is the apps/agents/common package; root is in sys.path via conftest.
common = pytest.importorskip("common.offline_cache")
audit = pytest.importorskip("common.audit")


def test_resource_allocation_local_offline_safe() -> None:
    assert common.is_decision_offline_safe("resource-allocation-local") is True


def test_safety_escalation_local_offline_safe() -> None:
    assert common.is_decision_offline_safe("safety-escalation-local") is True


def test_evacuation_centre_setup_offline_safe() -> None:
    assert common.is_decision_offline_safe("evacuation-centre-setup") is True


def test_public_warning_rejected_offline() -> None:
    assert common.is_decision_offline_safe("public-warning") is False


def test_cross_jurisdiction_mutual_aid_rejected_offline() -> None:
    assert common.is_decision_offline_safe("cross-jurisdiction-mutual-aid") is False


def test_state_escalation_rejected_offline() -> None:
    assert common.is_decision_offline_safe("state-escalation") is False


def test_unknown_decision_type_fails_closed() -> None:
    """Unknown decision types are queued for IC review (Constitution Principle I
    — fail-closed for unclassified actions)."""
    assert common.is_decision_offline_safe("some-future-decision") is False
    assert common.is_decision_offline_safe("") is False


def test_queue_offline_decision_emits_pending_audit() -> None:
    """On reconnect, the queued offline decision becomes an audit record with
    approval_workflow_state == 'pending' and field_coordinator_offline_decision
    populated."""
    queued = common.queue_offline_decision_for_review(
        decision_type="public-warning",
        decision_summary="Issue evacuation order for Bega Valley LGA",
        field_coordinator_id="fc-nsw-bega-1@ama.local",
    )
    assert queued.decision_type == "public-warning"
    assert queued.decision_summary.startswith("Issue evacuation order")
    assert queued.field_coordinator_id == "fc-nsw-bega-1@ama.local"
    assert isinstance(queued.queued_at, datetime)
    assert queued.queued_at.tzinfo == UTC

    # Build an audit record honouring the F-A5 wiring at audit.py.
    record = audit.make_inference_record(
        agent_name="EvacuationAgent",
        prompt_sha="9" * 64,
        model_id="gpt-4o-mini",
        model_version="2024-07-18",
        deployment_alias="ama-prod-gpt-4o-mini-v1",
        output_text_hash="0" * 64,
        output_tokens=42,
        tenant_id="agency-nsw-rfs",
        correlation_id="cor-fc-1",
        rag_used=False,
        rag_optout_reason="scenario-execution",
        adr_pointer="docs/decisions/036-foundry-rag-grounding/06-rag-optout-scenario-execution.md",
        field_coordinator_offline_decision=queued.decision_summary,
    )
    assert record["field_coordinator_offline_decision"].startswith("Issue evacuation order")
    # ADR-14 invariant 8: offline decision auto-sets approval_workflow_state = "pending".
    assert record["approval_workflow_state"] == "pending"


def test_offline_safe_decision_must_not_be_queued() -> None:
    with pytest.raises(ValueError, match=r"is offline-safe"):
        common.queue_offline_decision_for_review(
            decision_type="resource-allocation-local",
            decision_summary="Allocate Heli-1 to Bega Valley",
            field_coordinator_id="fc-nsw-bega-1@ama.local",
        )
