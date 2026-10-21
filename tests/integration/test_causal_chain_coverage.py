"""Spec-038 / T-D02 — Causal chain coverage (SC-006).

Every named capability has ≥1 published chain with valid originating_spec_path.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.main import create_app
from app.services.evidence._clients import reset_registry
from fastapi.testclient import TestClient

CAPABILITY_IDS = [
    "risk-assessment-agent",
    "evacuation-agent",
    "communication-agent",
    "resource-allocation-agent",
    "monitoring-agent",
    "foundry-rag-client",
    "telemetry-injection-agent",
]


@pytest.fixture()
def client():
    reset_registry()
    from app.services.evidence.impact import router as ir

    ir._SEEDED = False
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("cap_id", CAPABILITY_IDS)
def test_every_capability_has_chain(client, cap_id):
    r = client.get(f"/api/v1/evidence/causal-chains/{cap_id}")
    assert r.status_code == 200, f"{cap_id} missing causal chain"
    body = r.json()
    assert body["originating_spec_path"].startswith("specs/")
    assert len(body["kpis_moved"]) >= 1
    assert len(body["assumptions"]) >= 1
    assert len(body["threats_to_validity"]) >= 1
    source = Path(body["originating_spec_path"])
    assert source.is_file()
    assert f"**{body['originating_requirement']}**" in source.read_text(encoding="utf-8")
    assert all(assumption["resolved"] is False for assumption in body["assumptions"])
