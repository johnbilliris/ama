import asyncio
from datetime import UTC, datetime

import pytest

from app.services.ingestion.incident_association import IncidentAssociationService
from app.services.state_store import INCIDENTS, reset_state
from packages.domain.src.domain.models.incident import Incident


@pytest.fixture(autouse=True)
def clean_state():
    reset_state()
    yield
    reset_state()


@pytest.fixture
def service():
    return IncidentAssociationService()


@pytest.fixture
def nsw_incident():
    incident = Incident(
        incident_id="inc-nsw-001",
        title="Blue Mountains Bushfire",
        incident_type="bushfire",
        status="active",
        severity="emergency",
        affected_jurisdiction_ids=["nsw"],
    )
    INCIDENTS["inc-nsw-001"] = incident
    return incident


@pytest.fixture
def vic_incident():
    incident = Incident(
        incident_id="inc-vic-001",
        title="Gippsland Flood",
        incident_type="flood",
        status="active",
        severity="warning",
        affected_jurisdiction_ids=["vic"],
    )
    INCIDENTS["inc-vic-001"] = incident
    return incident


class TestIncidentAssociation:
    @pytest.mark.asyncio
    async def test_signal_in_active_incident_gets_incident_id(self, service, nsw_incident):
        envelope = {
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        }
        result = await service.associate(envelope)
        assert result["incidentId"] == "inc-nsw-001"

    @pytest.mark.asyncio
    async def test_signal_outside_any_incident_gets_null(self, service):
        envelope = {
            "jurisdictionId": "wa",
            "location": {"type": "Point", "coordinates": [115.8, -31.9], "precisionMeters": 100},
        }
        result = await service.associate(envelope)
        assert result["incidentId"] is None

    @pytest.mark.asyncio
    async def test_national_signal_matches_by_jurisdiction(self, service, nsw_incident, vic_incident):
        envelope = {
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        }
        results = await service.associate_multi(envelope)
        incident_ids = [r["incidentId"] for r in results]
        assert "inc-nsw-001" in incident_ids

    @pytest.mark.asyncio
    async def test_multi_incident_overlap_creates_multiple_records(self, service):
        INCIDENTS["inc-a"] = Incident(
            incident_id="inc-a", title="A", incident_type="flood",
            status="active", severity="warning", affected_jurisdiction_ids=["nsw"],
        )
        INCIDENTS["inc-b"] = Incident(
            incident_id="inc-b", title="B", incident_type="bushfire",
            status="active", severity="emergency", affected_jurisdiction_ids=["nsw"],
        )
        envelope = {
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        }
        results = await service.associate_multi(envelope)
        assert len(results) == 2
        ids = {r["incidentId"] for r in results}
        assert ids == {"inc-a", "inc-b"}

    @pytest.mark.asyncio
    async def test_closed_incident_not_matched(self, service):
        INCIDENTS["inc-closed"] = Incident(
            incident_id="inc-closed", title="Closed", incident_type="flood",
            status="closed", severity="advisory", affected_jurisdiction_ids=["nsw"],
        )
        envelope = {
            "jurisdictionId": "nsw",
            "location": {"type": "Point", "coordinates": [151.2, -33.8], "precisionMeters": 100},
        }
        result = await service.associate(envelope)
        assert result["incidentId"] is None
