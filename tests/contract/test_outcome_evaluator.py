"""Contract tests for spec 034 outcome-evaluator + audit-list (T181).

Covers ``contracts/outcome-evaluator.contract.md``:

  • Routable range (Pass 5 Q29): sc-001..sc-005 evaluate; sc-006..sc-011
    return 400 with ``ci_job`` payload naming the artefact owner.
  • Idempotency tuple (data-model §13): ``(sc_id, scenario_id, persona_id,
    correlation_id)`` returns the same audit_id on replay.
  • Persona resolvability (ASM-011): unknown persona_id → 422.
  • Scenario resolvability: unknown scenario_id → 404.
  • Audit-list cycle filter (Q22): ``cycle=current`` filters on
    bootstrap_seed_data().current_cycle_start.
  • Audit-list response shape: contract uses ``items`` (NOT ``entries``).

The test rebuilds the FastAPI app under both guards green
(``AMA_TEST_SUPPORT=1`` + ``AMA_ENVIRONMENT=dev``), then drives the routes
via TestClient. Each test resets the in-memory ledger via the service's
``reset_for_tests()`` so cases are independent.
"""

from __future__ import annotations

import importlib
import os
import uuid

import pytest
from fastapi.testclient import TestClient

# Map sc_id → seeded scenario_id. Each capstone outcome has exactly one
# matching scenario in ``hazard_scenarios_australia.json`` (1:1 by design).
SC_TO_SCENARIO: dict[str, str] = {
    "sc-001": "outcome-1-bushfire-extreme-heat",
    "sc-002": "outcome-2-bushfire-severe-storm",
    "sc-003": "outcome-3-tropical-cyclone-flood",
    "sc-004": "outcome-4-bushfire-cyclone-logistics",
    "sc-005": "outcome-5-flood-storm-economic",
}

# Canned metric_inputs that score "pass" against the seeded baselines.
# See data-model §13 + bootstrap.py CURRENT_CYCLE_START rationale.
PASS_METRIC_INPUTS: dict[str, dict[str, float]] = {
    "sc-001": {"lives_at_risk": 800.0},  # baseline 2000 → saved 1200 ≥ 1000
    "sc-002": {"signal_to_action_ms": 4500.0},  # baseline 10000 → 0.45× ≤ 0.5
    "sc-003": {"evac_lead_hours": 26.0},  # ≥ 24h
    "sc-004": {"logistics_clicks": 6.0},  # ≤ 7
    "sc-005": {"economic_loss_aud": 1_400_000_000.0},  # baseline 2e9 → 30% reduction
}


def _build_client(monkeypatch) -> TestClient:
    """Rebuild the FastAPI app with both dual-guards green."""

    monkeypatch.setenv("AMA_TEST_SUPPORT", "1")
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")

    import app.core.settings as settings_module

    importlib.reload(settings_module)
    settings_module.get_settings.cache_clear()

    import app.middleware.test_support_guard as guard_module

    importlib.reload(guard_module)

    import app.api.router as router_module

    importlib.reload(router_module)

    import app.main as main_module

    importlib.reload(main_module)

    return TestClient(main_module.create_app())


@pytest.fixture(autouse=True)
def _reset_evaluator_state():
    """Clear the in-memory ledger + idempotency cache between cases."""

    yield  # Setup happens in fixture body before yield is unnecessary; reset on entry+exit.
    try:
        from app.services.outcome_evaluator_service import reset_for_tests

        reset_for_tests()
    except ImportError:  # pragma: no cover - module is the SUT
        pass


@pytest.fixture(autouse=True)
def _restore_env():
    """Belt-and-braces: never leak AMA_TEST_SUPPORT between tests."""

    original = os.environ.get("AMA_TEST_SUPPORT")
    yield
    if original is None:
        os.environ.pop("AMA_TEST_SUPPORT", None)
    else:
        os.environ["AMA_TEST_SUPPORT"] = original


# ---------------------------------------------------------------------------
# Happy path: each routable sc_id returns status="pass" with a fresh audit_id.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sc_id", list(SC_TO_SCENARIO))
def test_evaluator_pass_for_each_routable_sc_id(monkeypatch, sc_id):
    client = _build_client(monkeypatch)
    body = {
        "scenario_id": SC_TO_SCENARIO[sc_id],
        "persona_id": "incident-commander",
        "correlation_id": str(uuid.uuid4()),
        "metric_inputs": PASS_METRIC_INPUTS[sc_id],
    }
    res = client.post(f"/api/outcomes/{sc_id}/evaluate", json=body)
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["status"] == "pass"
    assert "audit_id" in payload
    # audit_id is a UUID v4 string per the contract's response schema
    uuid.UUID(payload["audit_id"], version=4)
    assert any(ref.startswith("audit:") for ref in payload["evidence_refs"])


# ---------------------------------------------------------------------------
# Idempotency: same tuple → same audit_id and the audit list does NOT
# duplicate. (data-model §13 invariant.)
# ---------------------------------------------------------------------------


def test_evaluator_idempotent_on_repeat(monkeypatch):
    client = _build_client(monkeypatch)
    correlation = str(uuid.uuid4())
    body = {
        "scenario_id": SC_TO_SCENARIO["sc-001"],
        "persona_id": "incident-commander",
        "correlation_id": correlation,
        "metric_inputs": PASS_METRIC_INPUTS["sc-001"],
    }
    first = client.post("/api/outcomes/sc-001/evaluate", json=body).json()
    second = client.post("/api/outcomes/sc-001/evaluate", json=body).json()
    assert first["audit_id"] == second["audit_id"]

    listing = client.get(
        "/api/audit/list",
        params={"correlation_id": correlation, "cycle": "current"},
    ).json()
    assert listing["count"] == 1, "idempotent replay must not duplicate the audit row"
    assert listing["items"][0]["audit_id"] == first["audit_id"]


# ---------------------------------------------------------------------------
# Out-of-range sc_id (Q29) — must 400 + name the CI artefact owner so the
# Playwright suite can surface the routing failure to the operator.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sc_id, ci_job",
    [
        ("sc-006", "web-coverage-gate"),
        ("sc-007", "web-coverage-gate"),
        ("sc-008", "web-coverage-gate"),
        ("sc-009", "gap-register-validate"),
        ("sc-010", "verify-trace-determinism"),
        ("sc-011", "web-coverage-shard"),
    ],
)
def test_evaluator_400_for_non_routable_sc_id(monkeypatch, sc_id, ci_job):
    client = _build_client(monkeypatch)
    body = {
        "scenario_id": SC_TO_SCENARIO["sc-001"],
        "persona_id": "incident-commander",
        "correlation_id": str(uuid.uuid4()),
        "metric_inputs": {"lives_at_risk": 800},
    }
    res = client.post(f"/api/outcomes/{sc_id}/evaluate", json=body)
    assert res.status_code == 400, res.text
    payload = res.json()
    assert payload["error"] == "evaluator_not_routable"
    assert payload["ci_job"] == ci_job


# ---------------------------------------------------------------------------
# Unknown scenario_id → 404.
# ---------------------------------------------------------------------------


def test_evaluator_404_when_scenario_unknown(monkeypatch):
    client = _build_client(monkeypatch)
    body = {
        "scenario_id": "outcome-99-nonexistent",
        "persona_id": "incident-commander",
        "correlation_id": str(uuid.uuid4()),
        "metric_inputs": PASS_METRIC_INPUTS["sc-001"],
    }
    res = client.post("/api/outcomes/sc-001/evaluate", json=body)
    assert res.status_code == 404
    assert res.json()["error"] == "scenario_not_found"


# ---------------------------------------------------------------------------
# ASM-011: persona_id MUST resolve in bootstrap_seed_data().identities.
# ---------------------------------------------------------------------------


def test_evaluator_422_when_persona_unknown(monkeypatch):
    client = _build_client(monkeypatch)
    body = {
        "scenario_id": SC_TO_SCENARIO["sc-001"],
        "persona_id": "no-such-persona",
        "correlation_id": str(uuid.uuid4()),
        "metric_inputs": PASS_METRIC_INPUTS["sc-001"],
    }
    res = client.post("/api/outcomes/sc-001/evaluate", json=body)
    assert res.status_code == 422
    assert res.json()["error"] == "persona_not_resolvable"


# ---------------------------------------------------------------------------
# metric_inputs validation — wrong field for the sc_id → 422.
# ---------------------------------------------------------------------------


def test_evaluator_422_when_metric_inputs_missing_required_field(monkeypatch):
    client = _build_client(monkeypatch)
    body = {
        "scenario_id": SC_TO_SCENARIO["sc-001"],
        "persona_id": "incident-commander",
        "correlation_id": str(uuid.uuid4()),
        "metric_inputs": {"wrong_field": 1},  # missing lives_at_risk
    }
    res = client.post("/api/outcomes/sc-001/evaluate", json=body)
    assert res.status_code == 422
    assert res.json()["error"] == "metric_inputs_invalid"


# ---------------------------------------------------------------------------
# Audit-list response shape — MUST use the ``items`` field per contract,
# NOT ``entries`` (caught during cycle-1 contract re-read).
# ---------------------------------------------------------------------------


def test_audit_list_response_uses_items_field(monkeypatch):
    client = _build_client(monkeypatch)
    correlation = str(uuid.uuid4())
    client.post(
        "/api/outcomes/sc-001/evaluate",
        json={
            "scenario_id": SC_TO_SCENARIO["sc-001"],
            "persona_id": "incident-commander",
            "correlation_id": correlation,
            "metric_inputs": PASS_METRIC_INPUTS["sc-001"],
        },
    )
    res = client.get("/api/audit/list", params={"correlation_id": correlation})
    assert res.status_code == 200, res.text
    body = res.json()
    assert "items" in body, "contract requires 'items' (not 'entries')"
    assert "entries" not in body
    assert "count" in body
    assert "cycle" in body
    item = body["items"][0]
    for key in (
        "audit_id",
        "audit_timestamp",
        "correlation_id",
        "operator_identity",
        "rationale",
        "confidence",
        "source_refs",
        "outcome",
    ):
        assert key in item, f"audit-list item missing required field {key}"
    assert item["operator_identity"]["persona_id"] == "incident-commander"


# ---------------------------------------------------------------------------
# Audit-list cycle filter (Q22) — cycle=current excludes rows older than
# CURRENT_CYCLE_START. We can't easily backdate ledger rows from outside
# the service, but we CAN assert that cycle=all matches the same number
# as cycle=current when all rows are inside the current cycle (the common
# case under test).
# ---------------------------------------------------------------------------


def test_audit_list_cycle_all_includes_current_rows(monkeypatch):
    client = _build_client(monkeypatch)
    client.post(
        "/api/outcomes/sc-002/evaluate",
        json={
            "scenario_id": SC_TO_SCENARIO["sc-002"],
            "persona_id": "incident-commander",
            "correlation_id": str(uuid.uuid4()),
            "metric_inputs": PASS_METRIC_INPUTS["sc-002"],
        },
    )
    current_count = client.get(
        "/api/audit/list",
        params={"cycle": "current"},
    ).json()["count"]
    all_count = client.get(
        "/api/audit/list",
        params={"cycle": "all"},
    ).json()["count"]
    assert current_count == all_count == 1


# ---------------------------------------------------------------------------
# Audit-list pagination (limit guard).
# ---------------------------------------------------------------------------


def test_audit_list_rejects_limit_above_500(monkeypatch):
    client = _build_client(monkeypatch)
    res = client.get("/api/audit/list", params={"limit": 501})
    # FastAPI's Query(le=500) returns a 422 for the validation failure.
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Dual-guard: when AMA_TEST_SUPPORT is unset the canonical cycle-1 evaluator
# routes (with the strict ``^[0-9]{3}$`` sc_id pattern, ``extra="forbid"``
# request schema, and Cosmos-backed audit chain) MUST NOT mount. (We cannot
# toggle env mid-process and reload only this router; we delegate the broader
# guard verification to test_test_support_router.py.)
#
# Spec-035 follow-up: a workspace-shaped fallback bridge is mounted on the
# same paths so the IC Approval Card workspace panel does not 404. The bridge
# accepts a different body shape (``rationale``/``sources``/``confidence``/
# ``approver_identity``) and returns ``status="approved"`` rather than
# ``status="pass"``. This test verifies the gated cycle-1 evaluator is gone
# (no ``evidence_refs`` / ``metric_value`` / ``threshold`` in the response,
# and the strict 422 sc_id pattern is no longer enforced for non-numeric
# sc_ids).
# ---------------------------------------------------------------------------


def test_routes_404_when_test_support_disabled(monkeypatch):
    monkeypatch.delenv("AMA_TEST_SUPPORT", raising=False)
    monkeypatch.setenv("AMA_ENVIRONMENT", "dev")

    import app.core.settings as settings_module

    importlib.reload(settings_module)
    settings_module.get_settings.cache_clear()

    import app.middleware.test_support_guard as guard_module

    importlib.reload(guard_module)

    import app.api.router as router_module

    importlib.reload(router_module)

    import app.main as main_module

    importlib.reload(main_module)

    client = TestClient(main_module.create_app())

    # Gated cycle-1 evaluator no longer mounts: a non-numeric sc_id that the
    # gated route would have rejected with 422 (path pattern violation) is
    # now happily accepted by the workspace bridge with status=approved.
    bridge_response = client.post(
        "/api/outcomes/sc-task-not-numeric/evaluate",
        json={
            "rationale": "test",
            "sources": [],
            "confidence": 0.5,
            "approver_identity": "tester",
        },
    )
    assert bridge_response.status_code == 200, bridge_response.text
    bridge_body = bridge_response.json()
    assert bridge_body["status"] == "approved"
    assert "audit_id" in bridge_body
    assert "correlation_id" in bridge_body
    # Gated-route fields are absent on the bridge response.
    assert "evidence_refs" not in bridge_body
    assert "metric_value" not in bridge_body
    assert "threshold" not in bridge_body

    # Audit list bridge accepts unfiltered queries and returns the bridge
    # envelope (``rows`` + ``count``). The gated audit-list returns a
    # different envelope (``items`` + opaque cursor) per FR-029.
    list_response = client.get("/api/audit/list")
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert "rows" in list_body
    assert "count" in list_body
    assert "items" not in list_body
