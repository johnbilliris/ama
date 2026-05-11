"""T015 — contract: GET /api/governance/evidence-pack/artefacts/{artefact_id}.

Citations: FR-021, FR-029, CHK071.
"""

from __future__ import annotations


def test_get_artefact_envelope(api_client):
    resp = api_client.get("/api/governance/evidence-pack/artefacts/risk_register")
    assert resp.status_code == 200
    env = resp.json()
    assert env["artefact_id"] == "risk_register"
    assert "rows" in env
    assert "metadata" in env
    assert "publication_id" in env


def test_get_artefact_unknown_id_404(api_client):
    resp = api_client.get("/api/governance/evidence-pack/artefacts/does_not_exist")
    assert resp.status_code in (404, 422)
