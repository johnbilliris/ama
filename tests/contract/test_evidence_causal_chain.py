"""Spec-038 / T-D01 — Causal Chain contract test."""

from __future__ import annotations

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.impact import router as impact_router

    impact_router._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_causal_chain_for_known_capability(client):
    r = client.get("/api/v1/evidence/causal-chains/resource-allocation-agent")
    assert r.status_code == 200
    body = r.json()
    assert body["capability_id"] == "resource-allocation-agent"
    assert len(body["kpis_moved"]) >= 1
    assert len(body["assumptions"]) >= 1
    assert len(body["threats_to_validity"]) >= 1
    assert body["originating_spec_path"].startswith("specs/")
    assert body["originating_requirement"].startswith("FR-")
    assert body["magnitude_status"] == "hypothesis"
    assert body["expected_magnitude_value"] is None
    for assumption in body["assumptions"]:
        assert assumption["id"]
        assert assumption["validation_method"]
        assert assumption["evidence_required"]
        assert assumption["owner_role"]
        assert assumption["review_state"] == "pending"


def test_causal_chain_404(client):
    r = client.get("/api/v1/evidence/causal-chains/no-such-capability")
    assert r.status_code == 404


def test_publish_rejects_missing_source_requirement():
    from app.services.evidence.impact.repository import publish
    from app.services.evidence.impact.seed import seed_chains

    invalid = seed_chains()[0].model_copy(update={"originating_requirement": "FR-999"})

    with pytest.raises(ValueError, match="FR-999 not found"):
        publish(invalid)
