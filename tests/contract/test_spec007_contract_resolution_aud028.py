from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec007_isolation


def test_spec007_contract_decisions_are_complete_and_resolved() -> None:
    path = Path("specs/007-simulation-tenant-isolation/contracts/contract-resolution.v2.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["contractVersion"] == 2
    decisions = {row["id"]: row for row in payload["decisions"]}
    assert set(decisions) == {
        "SIM-STATUS-CASING",
        "SIM-REPORT-MISSING",
        "SIM-ARCHIVE-ASYNC",
        "SIM-TTL-IDLE",
        "SIM-COUNTERS",
    }
    assert all(row["status"] == "RESOLVED" for row in decisions.values())
    assert all(row["owner"] and row["decision"] and row["acceptanceImpact"] for row in decisions.values())


def test_simulation_api_contract_uses_resolved_wire_values() -> None:
    text = Path("specs/007-simulation-tenant-isolation/contracts/simulation-api.md").read_text(encoding="utf-8")
    assert '"status": "Active"' in text
    assert '"status": "Archiving"' in text
    assert "GET /api/simulations/reports/{reportId}" in text
    assert '"signals_scheduled": 25' in text
    assert "start_from" not in text
    assert "reads never generate a report" in text.split("### GET /api/simulations/reports/{reportId}", 1)[1]


def _middleware_contract() -> str:
    return Path("specs/007-simulation-tenant-isolation/contracts/tenant-middleware.md").read_text(encoding="utf-8")


def test_tenant_middleware_contract_declares_version_two_and_retires_v1_status_gate() -> None:
    text = _middleware_contract()

    assert "**Contract version**: 2" in text
    assert "does **not** gate on lifecycle status" in text
    # The v1 rule rejected any tenant outside active/paused, which would have blocked
    # SIM-ARCHIVE-ASYNC polling and SIM-REPORT-MISSING reads.
    assert "| Simulation tenant not in `active` or `paused` status | 409 Conflict |" not in text
    assert "`Archiving` and `Archived` tenants stay addressable" in text


def test_tenant_middleware_contract_matches_implementation_constants() -> None:
    from app.middleware import tenant_middleware

    text = _middleware_contract()
    source = Path(tenant_middleware.__file__).read_text(encoding="utf-8")

    for path in tenant_middleware.UNAUTHENTICATED_PATHS:
        assert f"`{path}`" in text, f"undocumented unauthenticated path: {path}"
    assert f"`{tenant_middleware.SIMULATION_MANAGEMENT_PREFIX}`" in text

    for symbol in ("X-Tenant-Id", "touch_activity", "get_by_participant", "annotate_current_span"):
        assert symbol in source, f"contract references a symbol the middleware no longer uses: {symbol}"
        assert symbol in text, f"middleware behaviour not documented: {symbol}"

    for status in ("403", "404", "503", "409"):
        assert f"`{status}" in text, f"resolution status {status} is not documented"


def test_tenant_middleware_contract_documents_context_and_offload_contract() -> None:
    from app.core import tenant_context

    text = _middleware_contract()

    assert "def set_current_tenant(ctx: TenantContext) -> Token[TenantContext]:" in text
    assert "def reset_current_tenant(token: Token[TenantContext]) -> None:" in text
    assert hasattr(tenant_context, "reset_current_tenant")
    assert "run_blocking" in text


def _quickstart() -> str:
    return Path("specs/007-simulation-tenant-isolation/quickstart.md").read_text(encoding="utf-8")


def _quickstart_examples() -> str:
    """Only the fenced command blocks — prose may name superseded fields."""
    import re

    return "\n".join(re.findall(r"```[a-z]*\n(.*?)```", _quickstart(), re.DOTALL))


def test_quickstart_seed_and_replay_bodies_match_request_models() -> None:
    from app.api.routes.simulations import SeedReplayRequest, SeedTemplateRequest

    examples = _quickstart_examples()

    assert set(SeedTemplateRequest.model_fields) == {"template_id"}
    assert set(SeedReplayRequest.model_fields) == {"incident_id", "start", "end", "time_compression"}
    for field in SeedReplayRequest.model_fields:
        assert f'"{field}"' in examples, f"replay field missing from quickstart: {field}"
    # Superseded v1 replay wire names must not reappear in runnable examples.
    for retired in ("start_from", "end_at", "replay_mode", "persona_assignments", "participant_oid"):
        assert retired not in examples, f"quickstart still documents retired field: {retired}"


def test_quickstart_participants_body_matches_assignment_model() -> None:
    from app.api.routes.simulations import AddParticipantsRequest, ParticipantAssignmentInput

    examples = _quickstart_examples()

    assert set(AddParticipantsRequest.model_fields) == {"participants"}
    assert set(ParticipantAssignmentInput.model_fields) == {
        "oid",
        "persona_id",
        "organisation_id",
        "jurisdiction_id",
        "role",
    }
    # ``persona_id`` is populated by the ``persona`` alias on the wire.
    assert ParticipantAssignmentInput.model_fields["persona_id"].alias == "persona"
    for wire_name in ("oid", "persona", "organisation_id", "jurisdiction_id", "role"):
        assert f'"{wire_name}"' in examples, f"participant field missing from quickstart: {wire_name}"


def test_quickstart_participant_examples_resolve_in_the_persona_catalogue() -> None:
    import json as _json
    import re

    from app.repositories.persona_registry_repository import get_persona_registry_repository

    block = re.search(r'"participants": \[\s*\{.*?\n    \]\n', _quickstart(), re.DOTALL)
    assert block is not None, "quickstart participants example block not found"
    registry = get_persona_registry_repository()

    entries = list(re.finditer(r'\{\s*"oid".*?\}', block.group(0), re.DOTALL))
    assert entries, "quickstart participants example has no assignment objects"
    for match in entries:
        entry = _json.loads(match.group(0))
        persona = registry.find_by_id(entry["persona"])
        assert persona is not None, f"quickstart persona is not in the catalogue: {entry['persona']}"
        assert persona.organisation_id == entry["organisation_id"]
        assert persona.jurisdiction_id == entry["jurisdiction_id"]


def test_quickstart_blob_container_and_isolation_test_names_are_real() -> None:
    import ast

    from app.services import exercise_report_service

    text = _quickstart()

    report_source = Path(exercise_report_service.__file__).read_text(encoding="utf-8")
    assert 'get_container_client("simulation")' in report_source
    assert "--container-name simulation" in text
    assert "--container-name reports" not in text

    isolation_path = Path("tests/integration/test_tenant_isolation.py")
    tree = ast.parse(isolation_path.read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_")
    }
    documented = {line.removeprefix("# - ").strip() for line in text.splitlines() if line.startswith("# - test_")}
    assert documented, "quickstart no longer lists isolation test names"
    assert documented <= defined, f"quickstart names tests that do not exist: {sorted(documented - defined)}"
