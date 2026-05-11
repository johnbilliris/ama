"""T014 — contract: GET /api/governance/evidence-pack/artefacts.

Citations: FR-001, FR-021, CHK070.
"""

from __future__ import annotations


def test_list_artefacts_returns_five_summaries(api_client):
    resp = api_client.get("/api/governance/evidence-pack/artefacts")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 5
    artefact_ids = {a["artefact_id"] for a in body}
    assert artefact_ids == {
        "risk_register",
        "adoption_roadmap",
        "executive_kpi_surface",
        "rai_register",
        "feature_value_ledger",
    }
    for a in body:
        assert 0.0 <= a["manual_row_ratio"] <= 1.0
        assert "publication_id" in a
        assert "published_at_utc" in a
