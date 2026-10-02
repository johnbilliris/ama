"""Contract tests for warning/alert API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from xml.etree.ElementTree import fromstring

import pytest
from app.main import create_app
from app.services.state_store import ALERTS, INCIDENTS, reset_state
from fastapi.testclient import TestClient

from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.public_alert import PublicAlert


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_state()


def _seed_incident(incident_id: str = "inc-1") -> Incident:
    inc = Incident(
        incident_id=incident_id,
        title="Bushfire Alpha",
        incident_type="bushfire",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["jur-1"],
    )
    INCIDENTS[incident_id] = inc
    return inc


def _seed_alert(
    alert_id: str = "alert-1",
    incident_id: str = "inc-1",
    *,
    warning_tier: str | None = "emergency_warning",
    is_all_clear: bool = False,
    superseded_warning_id: str | None = None,
    published: bool = True,
) -> PublicAlert:
    kwargs: dict = {
        "alert_id": alert_id,
        "incident_id": incident_id,
        "status": "published" if published else "draft",
        "content_blocks": {
            "headline": f"Test alert {alert_id}",
            "body": "Primary body",
            "areas": "Region A",
            "geography": "Region A; Region B",
            "approvedAt": "2025-01-15T09:58:00+00:00",
            "headline:zh-Hans": "测试告警",
            "body:zh-Hans": "请按指示撤离",
        },
        "audience_segments": ["community-north"],
        "languages": ["en-AU", "zh-Hans"],
        "is_all_clear": is_all_clear,
        "superseded_warning_id": superseded_warning_id,
    }
    if warning_tier and not is_all_clear:
        kwargs["warning_tier"] = warning_tier
        kwargs["action_statement"] = "Take shelter immediately"
    if published:
        kwargs["published_at"] = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
    alert = PublicAlert(**kwargs)
    ALERTS[alert_id] = alert
    return alert


# ---- GET /api/alerts/{alert_id}/chain ----


def test_get_warning_chain_returns_ordered_chain(client):
    _seed_incident()
    _seed_alert("alert-1", superseded_warning_id=None, warning_tier="advice")
    _seed_alert("alert-2", superseded_warning_id="alert-1", warning_tier="watch_and_act")
    _seed_alert("alert-3", superseded_warning_id="alert-2", warning_tier="emergency_warning")

    resp = client.get("/api/alerts/alert-3/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert len(chain) >= 2
    assert chain[-1]["alert_id"] == "alert-3"


def test_get_warning_chain_not_found(client):
    resp = client.get("/api/alerts/nonexistent/chain")
    assert resp.status_code == 404


# ---- GET /api/alerts/{alert_id}/cap ----


def test_get_cap_xml_returns_valid_xml(client):
    _seed_incident()
    _seed_alert("alert-cap")

    resp = client.get("/api/alerts/alert-cap/cap")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")

    root = fromstring(resp.text)
    ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
    assert root.find("cap:identifier", ns).text == "alert-cap"
    assert root.find("cap:info/cap:headline", ns).text == "Test alert alert-cap"
    infos = root.findall("cap:info", ns)
    assert len(infos) == 2


def test_get_cap_xml_escapes_special_characters(client):
    _seed_incident()
    alert = _seed_alert("alert-cap-special")
    alert.content_blocks["headline"] = 'Fire & smoke <near> "town"'
    alert.content_blocks["body"] = "Evacuate > now"

    resp = client.get("/api/alerts/alert-cap-special/cap")
    assert resp.status_code == 200
    root = fromstring(resp.text)
    ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
    headline = root.find("cap:info/cap:headline", ns)
    assert headline is not None
    assert headline.text == 'Fire & smoke <near> "town"'


def test_get_cap_xml_not_found(client):
    resp = client.get("/api/alerts/missing/cap")
    assert resp.status_code == 404


# ---- POST /api/alerts/{alert_id}/validate-compliance ----


def test_validate_compliance_returns_result(client):
    _seed_incident()
    _seed_alert("alert-v")

    resp = client.post("/api/alerts/alert-v/validate-compliance")
    assert resp.status_code == 200
    body = resp.json()
    assert body["alert_id"] == "alert-v"
    assert "is_compliant" in body
    assert "errors" in body


def test_validate_compliance_not_found(client):
    resp = client.post("/api/alerts/missing/validate-compliance")
    assert resp.status_code == 404


# ---- GET /api/alerts/{alert_id}/edxl ----


def test_get_edxl_returns_valid_xml(client):
    _seed_incident()
    _seed_alert("alert-edxl")

    resp = client.get("/api/alerts/alert-edxl/edxl")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")

    root = fromstring(resp.text)
    ns = {"edxl": "urn:oasis:names:tc:emergency:EDXL:DE:2.0"}
    dist_id = root.find("edxl:distributionID", ns)
    assert dist_id is not None and dist_id.text == "alert-edxl"
    sender = root.find("edxl:senderID", ns)
    assert sender is not None and sender.text == "disaster-response-hub"
    embedded_cap = root.find("edxl:contentObject/edxl:xmlContent/edxl:embeddedXMLContent", ns)
    assert embedded_cap is not None


def test_get_edxl_not_found(client):
    resp = client.get("/api/alerts/missing/edxl")
    assert resp.status_code == 404
