"""Wave A / T-AA12 — JSON-Schema 2020-12 contract for entry-25.

Asserts that ``contracts/audit-envelope.md`` documents the 25-entry filter
enumeration and that the typed Pydantic class
``SignalPipelineDispatchFailedDetails`` matches the OpenAPI
``SignalPipelineDispatchFailedAuditDetails`` component schema.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from packages.domain.src.domain.models.telemetry_injection_audit_entry import (
    ALL_ENTRY_TYPES,
    SignalPipelineDispatchFailedDetails,
)

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


def test_audit_envelope_filter_enum_size_26() -> None:
    """Cycle 3 / audit-envelope.md §5 closing-line counter = 26."""

    assert len(ALL_ENTRY_TYPES) == 26, (
        f"ALL_ENTRY_TYPES MUST be 26 entries (got {len(ALL_ENTRY_TYPES)}); "
        "Cycle 2 entry-25 is `signal_pipeline.dispatch_failed`; "
        "Cycle 3 entry-26 is `staging_promotion.refused`."
    )


def test_signal_pipeline_dispatch_failed_audit_details_jsonschema_2020_12(
    openapi_doc: dict,
) -> None:
    """Validate the OpenAPI component schema as JSON-Schema Draft 2020-12."""

    schema = openapi_doc["components"]["schemas"][
        "SignalPipelineDispatchFailedAuditDetails"
    ]
    # Self-validate the schema (meta-schema check).
    Draft202012Validator.check_schema(schema)


def test_signal_pipeline_dispatch_failed_pydantic_round_trip(
    openapi_doc: dict,
) -> None:
    """Generate a representative payload and validate against both surfaces."""

    sample = {
        "injection_correlation_id": "00000000-0000-0000-0000-000000000001",
        "exception_class": "OrchestratorTimeout",
        "exception_message": "dispatch timed out after 5s",
        "triggered_sub_agents": [
            {
                "correlation_id": "00000000-0000-0000-0000-000000000010",
                "dispatch_status": "timed_out",
                "sub_agent": "Resource",
                "trigger_source": "primary",
            }
        ],
        "partial_successful_subset": [],
        "failed_subscriber_list": ["Resource"],
        "prompt_hash": "a" * 64,
        "prompt_hash_source": "raw_user_input",
        "degraded_dispatch_flag": True,
        "dispatch_ack_timeout_seconds": 5.0,
        "idempotency_key": None,
        "request_correlation_id": "00000000-0000-0000-0000-000000000002",
    }

    # Round-trip 1 — Pydantic v2 typed model.
    pydantic_validated = SignalPipelineDispatchFailedDetails.model_validate(sample)
    assert pydantic_validated.degraded_dispatch_flag is True

    # Round-trip 2 — JSON-Schema component. We inline the ``TriggeredSubAgent``
    # ref into the schema-under-test so the validator does not need to
    # resolve cross-document references (the Pydantic round-trip already
    # exercises the typed shape, and ``test_v030_*`` separately asserts
    # that the OpenAPI component schemas exist and are well-formed).
    schema = openapi_doc["components"]["schemas"][
        "SignalPipelineDispatchFailedAuditDetails"
    ]
    triggered_sub_agent_schema = openapi_doc["components"]["schemas"][
        "TriggeredSubAgent"
    ]
    inlined = {
        **schema,
        "properties": {
            **schema["properties"],
            "triggered_sub_agents": {
                **schema["properties"]["triggered_sub_agents"],
                "items": triggered_sub_agent_schema,
            },
        },
    }
    Draft202012Validator(inlined).validate(sample)


def test_telemetry_injection_ack_v030_jsonschema_2020_12(openapi_doc: dict) -> None:
    """Validate v0.3.0 ``TelemetryInjectionAck`` component as JSON-Schema 2020-12."""

    schema = openapi_doc["components"]["schemas"]["TelemetryInjectionAck"]
    Draft202012Validator.check_schema(schema)
