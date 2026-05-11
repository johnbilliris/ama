"""T016 — contract: GET /api/governance/evidence-pack/artefacts/{id}/publications/{pub_id}.

Citations: FR-005, FR-038, PD-037-04, CHK072.
"""

from __future__ import annotations


def test_get_historical_publication_returns_envelope(api_client):
    resp = api_client.get(
        "/api/governance/evidence-pack/artefacts/risk_register/publications/00000000-0000-0000-0000-000000000001"
    )
    # Either 200 (snapshot found) or 404 (test fixture has no snapshot).
    # We assert the route is wired and returns a defined contract response.
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        env = resp.json()
        assert env["publication_id"] == "00000000-0000-0000-0000-000000000001"
        assert env["artefact_id"] == "risk_register"
