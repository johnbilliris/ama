"""Wave A / T-AA07 — OpenAPI v0.3.0 BREAKING bump contract test.

Asserts that:

1. ``contracts/openapi-simulation.yaml`` ``info.version == 0.3.0`` (bumped
   from 0.2.0 by Cycle 2 Amendment A2-01 / FR-067).
2. ``TelemetryInjectionAck.degraded_dispatch`` is required (pass 2 Q2).
3. ``TelemetryInjectionAck.triggered_sub_agents`` items reference the new
   ``TriggeredSubAgent`` schema.
4. ``TriggeredSubAgent`` declares ``additionalProperties: false`` (CHK135
   byte-equality invariant), the 9-name PascalCase ``sub_agent`` enum
   (Amendment A2-07 / FR-070), and the 3-value ``dispatch_status`` enum
   (pass 2 Q1).
5. ``SignalPipelineDispatchFailedAuditDetails`` exists and required-set
   matches audit-envelope.md §3.25.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = (
    REPO_ROOT
    / "specs"
    / "036-sim-agent-extend"
    / "contracts"
    / "openapi-simulation.yaml"
)


@pytest.fixture(scope="module")
def openapi_doc() -> dict:
    with OPENAPI_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_v030_version_bump(openapi_doc: dict) -> None:
    """Cycle 2 / Amendment A2-01 — BREAKING bump from 0.2.0 to 0.3.0."""

    assert openapi_doc["info"]["version"] == "0.3.0", (
        "openapi-simulation.yaml info.version MUST be 0.3.0 (Cycle 2 / "
        "Amendment A2-01 / FR-067 BREAKING bump)."
    )


def test_v030_telemetry_injection_ack_required_includes_degraded_dispatch(
    openapi_doc: dict,
) -> None:
    """Pass 2 Q2 — degraded_dispatch is always present."""

    ack = openapi_doc["components"]["schemas"]["TelemetryInjectionAck"]
    assert "degraded_dispatch" in ack["required"], (
        "TelemetryInjectionAck.required MUST include `degraded_dispatch` "
        "(Cycle 2 pass 2 Q2)."
    )


def test_v030_triggered_sub_agents_references_new_schema(
    openapi_doc: dict,
) -> None:
    """Cycle 2 / Amendment A2-01 — items use the TriggeredSubAgent component."""

    ack = openapi_doc["components"]["schemas"]["TelemetryInjectionAck"]
    items = ack["properties"]["triggered_sub_agents"]["items"]
    assert items == {"$ref": "#/components/schemas/TriggeredSubAgent"}, (
        "TelemetryInjectionAck.triggered_sub_agents.items MUST $ref "
        "#/components/schemas/TriggeredSubAgent (Cycle 2 BREAKING reshape)."
    )


def test_v030_triggered_sub_agent_schema_invariants(openapi_doc: dict) -> None:
    """CHK135 + Amendment A2-07 / FR-070 + pass 2 Q1 — schema invariants."""

    tsa = openapi_doc["components"]["schemas"]["TriggeredSubAgent"]
    assert tsa["additionalProperties"] is False, (
        "TriggeredSubAgent MUST set additionalProperties: false to enforce "
        "the CHK135 byte-equality invariant."
    )
    assert set(tsa["required"]) == {
        "sub_agent",
        "trigger_source",
        "correlation_id",
        "dispatch_status",
    }, "TriggeredSubAgent.required MUST be the four field-canonical set."
    assert sorted(tsa["properties"]["sub_agent"]["enum"]) == [
        "Comms",
        "Evac",
        "Health",
        "Intel",
        "Logistics",
        "Operations",
        "Planning",
        "Resource",
        "Risk",
    ], "sub_agent enum MUST be the 9-name PascalCase set (Amendment A2-07)."
    assert sorted(tsa["properties"]["dispatch_status"]["enum"]) == [
        "acknowledged",
        "failed",
        "timed_out",
    ], "dispatch_status enum MUST be the 3-value set (pass 2 Q1)."


def test_v030_signal_pipeline_dispatch_failed_audit_details_schema(
    openapi_doc: dict,
) -> None:
    """Cycle 2 / Amendment A2-04 — entry-25 audit-envelope component schema."""

    spdf = openapi_doc["components"]["schemas"][
        "SignalPipelineDispatchFailedAuditDetails"
    ]
    expected_required = {
        "injection_correlation_id",
        "exception_class",
        "exception_message",
        "triggered_sub_agents",
        "partial_successful_subset",
        "failed_subscriber_list",
        "prompt_hash",
        "prompt_hash_source",
        "degraded_dispatch_flag",
        "dispatch_ack_timeout_seconds",
        "request_correlation_id",
    }
    assert set(spdf["required"]) == expected_required, (
        "SignalPipelineDispatchFailedAuditDetails.required MUST match "
        "audit-envelope.md §3.25 (Cycle 2 entry-25 contract)."
    )
    assert spdf["properties"]["degraded_dispatch_flag"]["enum"] == [True], (
        "degraded_dispatch_flag MUST be const true (pass 2 Q2 invariant)."
    )
    assert spdf["properties"]["dispatch_ack_timeout_seconds"]["enum"] == [5.0], (
        "dispatch_ack_timeout_seconds MUST be const 5.0 (pass 2 Q1 invariant)."
    )
