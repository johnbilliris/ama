from datetime import UTC, datetime, timedelta

import pytest
from app.api.routes import incidents as incidents_route
from app.services.state_store import INCIDENTS, reset_state

from packages.domain.src.domain.models.incident import Incident
from packages.domain.src.domain.models.signal import Signal


class _FakeSignalRepository:
    def __init__(self, signals, update_behaviour=None):
        self._signals = signals
        self._update_behaviour = update_behaviour or {}
        self.last_scope = None

    async def query_unassociated(self, jurisdiction_id, since=None, *, scope, **kwargs):
        self.last_scope = scope
        cutoff = since or datetime.min.replace(tzinfo=UTC)
        results = []
        for signal in self._signals:
            if signal.incident_id is not None:
                continue
            if signal.occurred_at < cutoff:
                continue
            if jurisdiction_id != "national" and (signal.jurisdiction_id or "").lower() != jurisdiction_id.lower():
                continue
            results.append(signal)
        return results

    async def update_incident_id(self, signal_id, incident_id, *, scope, expected_incident_id=None):
        behaviour = self._update_behaviour.get(signal_id, "update")
        if behaviour == "raise":
            raise RuntimeError("update failed")
        if behaviour == "false":
            return False
        for signal in self._signals:
            if signal.signal_id == signal_id and signal.incident_id == expected_incident_id:
                signal.incident_id = incident_id
                return True
        return False


def _make_signal(signal_id: str, *, jurisdiction_id: str, hours_ago: int, lon: float, lat: float, incident_id=None):
    now = datetime.now(UTC)
    occurred = now - timedelta(hours=hours_ago)
    return Signal(
        signal_id=signal_id,
        incident_id=incident_id,
        data_source_id="bom-warnings",
        category="weather",
        occurred_at=occurred,
        received_at=occurred + timedelta(seconds=30),
        jurisdiction_id=jurisdiction_id,
        location={"type": "Point", "coordinates": [lon, lat], "precisionMeters": 100},
        payload={},
        owning_agency_id="agency-1",
        source_name="BoM",
        source_kind="authoritative",
        trust_tier="tier_1_authoritative_government",
        source_timestamp=occurred,
        raw_payload_uri="raw-payloads/x.json",
        classification="official",
        pii_fields=[],
        retention_until=now + timedelta(days=1),
        confidence_score=0.9,
        freshness_score=0.9,
        validation_status="validated",
        provenance={"collectionMethod": "api_pull", "sourceUri": "https://example.test"},
    )


@pytest.fixture(autouse=True)
def _clean_state():
    reset_state()
    incidents_route._declaration_results.clear()
    yield
    reset_state()
    incidents_route._declaration_results.clear()


@pytest.mark.asyncio
async def test_declaration_path_associates_matching_scope_and_footprint(monkeypatch):
    incident = Incident(
        incident_id="inc-1",
        title="Flood",
        incident_type="flood",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["nsw"],
        location={
            "type": "Polygon",
            "coordinates": [[[151.0, -34.0], [151.5, -34.0], [151.5, -33.5], [151.0, -33.5], [151.0, -34.0]]],
        },
    )
    INCIDENTS.bucket_for("live")[incident.incident_id] = incident

    signals = [
        _make_signal("sig-in", jurisdiction_id="nsw", hours_ago=1, lon=151.2, lat=-33.8),
        _make_signal("sig-out", jurisdiction_id="nsw", hours_ago=1, lon=149.0, lat=-35.0),
    ]
    fake_repo = _FakeSignalRepository(signals)
    monkeypatch.setattr(incidents_route, "_signal_repository", fake_repo)

    result = await incidents_route._run_retrospective_association(
        incidents_route.DeclareIncidentRequest(
            incident_id="inc-1",
            jurisdiction_id="nsw",
            lookback_hours=24,
            declaration_event_id="evt-1",
            tenant_id="live",
        )
    )

    assert result["signals_associated"] == 1
    assert result["signals_skipped"] == 1
    assert fake_repo.last_scope == "live"


@pytest.mark.asyncio
async def test_declaration_respects_lookback_window(monkeypatch):
    incident = Incident(
        incident_id="inc-2",
        title="Storm",
        incident_type="storm",
        status="active",
        severity="watch",
        affected_jurisdiction_ids=["nsw"],
        location=None,
    )
    INCIDENTS.bucket_for("live")[incident.incident_id] = incident

    signals = [
        _make_signal("sig-recent", jurisdiction_id="nsw", hours_ago=1, lon=151.2, lat=-33.8),
        _make_signal("sig-old", jurisdiction_id="nsw", hours_ago=30, lon=151.2, lat=-33.8),
    ]
    fake_repo = _FakeSignalRepository(signals)
    monkeypatch.setattr(incidents_route, "_signal_repository", fake_repo)

    result = await incidents_route._run_retrospective_association(
        incidents_route.DeclareIncidentRequest(
            incident_id="inc-2",
            jurisdiction_id="nsw",
            lookback_hours=24,
            declaration_event_id="evt-2",
            tenant_id="live",
        )
    )

    assert result["signals_considered"] == 1
    assert result["signals_associated"] == 1


@pytest.mark.asyncio
async def test_declaration_idempotent_replay_and_partial_failures(monkeypatch):
    incident = Incident(
        incident_id="inc-3",
        title="Fire",
        incident_type="bushfire",
        status="active",
        severity="emergency",
        affected_jurisdiction_ids=["nsw"],
        location=None,
    )
    INCIDENTS.bucket_for("sim-a")[incident.incident_id] = incident

    signals = [
        _make_signal("sig-ok", jurisdiction_id="nsw", hours_ago=1, lon=151.2, lat=-33.8),
        _make_signal("sig-race", jurisdiction_id="nsw", hours_ago=1, lon=151.2, lat=-33.8),
        _make_signal("sig-fail", jurisdiction_id="nsw", hours_ago=1, lon=151.2, lat=-33.8),
    ]
    fake_repo = _FakeSignalRepository(signals, {"sig-race": "false", "sig-fail": "raise"})
    monkeypatch.setattr(incidents_route, "_signal_repository", fake_repo)

    request = incidents_route.DeclareIncidentRequest(
        incident_id="inc-3",
        jurisdiction_id="nsw",
        lookback_hours=24,
        declaration_event_id="evt-3",
        tenant_id="sim-a",
    )

    first = await incidents_route._run_retrospective_association(request)
    second = await incidents_route._run_retrospective_association(request)

    assert first["signals_associated"] == 1
    assert first["signals_skipped"] == 1
    assert first["signals_failed"] == 1
    assert first["tenant_id"] == "sim-a"
    assert second["replayed"] is True
