"""Wave B / T-AA15 / CHK135 — JCS byte-equality body↔audit contract test.

The single highest-risk Cycle 2 invariant. Asserts that for every
``signal_pipeline.dispatch_failed`` envelope written, the ``triggered_sub_agents``
array on the audit envelope is byte-equal (after RFC 8785 JCS
canonicalisation) to the array on the corresponding HTTP 202 response
body.

Pass-1 Q1 ruling (spec.md L248-277):

    json.dumps(body['triggered_sub_agents'], sort_keys=True)
    == json.dumps(audit['details']['triggered_sub_agents'], sort_keys=True)

The shared :func:`canonicalise_triggered_sub_agents` helper enforces this
via:

* lex-sort by ``sub_agent`` PascalCase (pass-1 Q4);
* JCS-canonical key order ``{correlation_id, dispatch_status, sub_agent, trigger_source}``;
* round-trip through :func:`rfc8785.dumps`.

This test exercises the helper end-to-end with permuted inputs to prove
canonicalisation is order-invariant.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import asyncio
import itertools
import json
from uuid import UUID

from apps.api.app.services.simulation.audit_writer import (
    AuditWriter,
    canonicalise_triggered_sub_agents,
    reset_audit_writer_for_tests,
    write_dispatch_failed,
)
from apps.api.app.services.simulation.dispatch_status import TriggeredSubAgent


def _build_entries() -> list[TriggeredSubAgent]:
    return [
        TriggeredSubAgent(
            sub_agent="Resource",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000010"),
            dispatch_status="acknowledged",
        ),
        TriggeredSubAgent(
            sub_agent="Comms",
            trigger_source="primary",
            correlation_id=UUID("00000000-0000-0000-0000-000000000011"),
            dispatch_status="failed",
        ),
        TriggeredSubAgent(
            sub_agent="Evac",
            trigger_source="cascade",
            correlation_id=UUID("00000000-0000-0000-0000-000000000012"),
            dispatch_status="timed_out",
        ),
    ]


def test_canonicaliser_is_input_order_invariant() -> None:
    """Permuted input lists produce byte-equal canonical output."""

    base = _build_entries()
    canonical_base = canonicalise_triggered_sub_agents(base)
    base_bytes = json.dumps(canonical_base, sort_keys=True)

    for permuted in itertools.permutations(base):
        canonical = canonicalise_triggered_sub_agents(list(permuted))
        permuted_bytes = json.dumps(canonical, sort_keys=True)
        assert permuted_bytes == base_bytes, (
            "canonicalise_triggered_sub_agents MUST be input-order invariant "
            "to honour CHK135 byte-equality."
        )


def test_canonicaliser_lex_sorts_by_sub_agent() -> None:
    """Output array is lex-sorted by ``sub_agent`` PascalCase (pass-1 Q4)."""

    canonical = canonicalise_triggered_sub_agents(_build_entries())
    sub_agents = [item["sub_agent"] for item in canonical]
    assert sub_agents == sorted(sub_agents) == ["Comms", "Evac", "Resource"]


def test_canonicaliser_key_order_matches_jcs() -> None:
    """Each entry's keys are alphabetic per RFC 8785 JCS default."""

    canonical = canonicalise_triggered_sub_agents(_build_entries())
    expected_keys = ["correlation_id", "dispatch_status", "sub_agent", "trigger_source"]
    for item in canonical:
        assert list(item.keys()) == expected_keys


def test_dispatch_failed_body_audit_byte_equality_round_trip() -> None:
    """End-to-end CHK135 — body→canonicalise→audit-emit→read-back byte-equal."""

    reset_audit_writer_for_tests()
    audit = AuditWriter(cosmos_container=None)
    body_entries = _build_entries()
    body_canonical = canonicalise_triggered_sub_agents(body_entries)
    body_bytes = json.dumps(body_canonical, sort_keys=True)

    envelope = asyncio.run(
        write_dispatch_failed(
            audit,
            simulation_id="sim-jcs",
            injection_correlation_id="00000000-0000-0000-0000-000000000001",
            exception_class="OrchestratorTimeout",
            exception_message="dispatch failed",
            triggered_sub_agents=body_entries,
            prompt_hash="d" * 64,
            prompt_hash_source="raw_user_input",
            idempotency_key=None,
            request_correlation_id="00000000-0000-0000-0000-000000000002",
        )
    )

    audit_canonical = envelope.details["triggered_sub_agents"]
    audit_bytes = json.dumps(audit_canonical, sort_keys=True)
    assert body_bytes == audit_bytes, (
        "CHK135 — HTTP 202 body's triggered_sub_agents array MUST be "
        "byte-equal (after RFC 8785 JCS canonicalisation) to the audit "
        "envelope's array (Cycle 2 pass-1 Q1)."
    )


def test_idempotency_replay_preserves_canonical_form() -> None:
    """Replaying with same inputs produces byte-equal canonical output."""

    body_entries = _build_entries()
    first = canonicalise_triggered_sub_agents(body_entries)
    second = canonicalise_triggered_sub_agents(body_entries)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
