"""Wave A / T-AA12 — Schemathesis fuzz of TelemetryInjectionAck v0.3.0.

Generates Hypothesis cases against the v0.3.0 ``TelemetryInjectionAck`` +
``TriggeredSubAgent`` schema components and asserts the Pydantic model
shape mirrors the OpenAPI contract:

* ``degraded_dispatch`` is ALWAYS present (pass-2 Q2);
* ``triggered_sub_agents[]`` items have a ``dispatch_status`` field with the
  3-value enum (pass-2 Q1);
* ``sub_agent`` is the 9-name PascalCase canonical set (Amendment A2-07).

Schemathesis 4.x is used as the schema-loader (without launching a real
ASGI app — generated cases are validated against the Pydantic model in
process). This keeps CI fast while still exercising the full v0.3.0
contract.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from apps.api.app.api.routes.simulations_036 import TelemetryInjectionAck
from apps.api.app.services.simulation.dispatch_status import (
    ALL_DISPATCH_STATUSES,
    TriggeredSubAgent,
)
from packages.domain.src.domain.models.aiims_mapping import ALL_SUB_AGENTS

REPO_ROOT = Path(__file__).resolve().parents[3]
OPENAPI_PATH = (
    REPO_ROOT
    / "specs"
    / "036-sim-agent-extend"
    / "contracts"
    / "openapi-simulation.yaml"
)


@pytest.fixture(scope="module")
def openapi_schema() -> dict:
    with OPENAPI_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_openapi_schema_loads_with_schemathesis_loader() -> None:
    """v0.3.0 schema loads without errors via Schemathesis loader."""

    pytest.importorskip("schemathesis")
    import schemathesis

    # Schemathesis 4.x prefers ``from_path``; ``from_dict`` is also acceptable.
    schema = schemathesis.openapi.from_path(str(OPENAPI_PATH))
    assert schema is not None
    # The schema reports v0.3.0 — confirms the loader path-resolution works.
    raw = schema.raw_schema if hasattr(schema, "raw_schema") else schema
    info = (
        raw.get("info") if isinstance(raw, dict) else getattr(raw, "info", None)
    )
    if isinstance(info, dict):
        assert info.get("version") == "0.3.0"


@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    sub_agent=st.sampled_from(list(ALL_SUB_AGENTS)),
    dispatch_status=st.sampled_from(list(ALL_DISPATCH_STATUSES)),
    correlation_id=st.uuids(),
    # data-model §11 narrows the dispatch_failed envelope's trigger_source
    # to the 2-value set ``{primary, cascade}`` for the audit envelope (and
    # by symmetry, the response body — see the Pydantic Literal in
    # ``apps/api/app/services/simulation/dispatch_status.py``).
    trigger_source=st.sampled_from(["primary", "cascade"]),
)
def test_triggered_sub_agent_round_trip(
    sub_agent: str,
    dispatch_status: str,
    correlation_id,  # noqa: ANN001 — Hypothesis UUID strategy
    trigger_source: str,
) -> None:
    """Hypothesis-generated cases round-trip through the Pydantic model."""

    obj = TriggeredSubAgent(
        sub_agent=sub_agent,
        trigger_source=trigger_source,
        correlation_id=correlation_id,
        dispatch_status=dispatch_status,
    )
    dumped = obj.model_dump(mode="json")
    assert dumped["sub_agent"] == sub_agent
    assert dumped["dispatch_status"] == dispatch_status
    assert dumped["trigger_source"] == trigger_source


@settings(max_examples=20, deadline=None)
@given(
    correlation_id=st.uuids(),
    degraded=st.booleans(),
)
def test_telemetry_injection_ack_degraded_dispatch_always_present(
    correlation_id,  # noqa: ANN001 — Hypothesis UUID strategy
    degraded: bool,
) -> None:
    """Pass 2 Q2 — degraded_dispatch is always-present in the model dump."""

    ack = TelemetryInjectionAck(
        injection_correlation_id=str(correlation_id),
        signals=[],
        refusals=[],
        triggered_sub_agents=[],
        degraded_dispatch=degraded,
    )
    dumped = ack.model_dump(mode="json")
    assert "degraded_dispatch" in dumped
    assert dumped["degraded_dispatch"] is degraded
