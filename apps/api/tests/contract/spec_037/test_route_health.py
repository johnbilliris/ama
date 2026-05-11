"""T017 — contract: GET /api/governance/evidence-pack/health.

Citations: FR-023 graceful-degradation, CHK073.
"""

from __future__ import annotations


def test_health_returns_summary(api_client):
    resp = api_client.get("/api/governance/evidence-pack/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_status"] in ("healthy", "degraded", "unhealthy")
    assert isinstance(body["artefacts"], list)
    for a in body["artefacts"]:
        assert a["gate_status"] in ("passed", "failed", "pending")
        assert 0.0 <= a["manual_row_ratio"] <= 1.0
