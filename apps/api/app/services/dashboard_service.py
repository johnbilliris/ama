import logging
import os
from typing import Any

from app.services.state_store import INCIDENTS, RECOMMENDATIONS, SIGNALS

logger = logging.getLogger(__name__)


def _lookup_cosmos_incident(incident_id: str) -> dict[str, Any] | None:
    """Look up a disaster record from the Cosmos DB seed container."""
    endpoint = os.environ.get("COSMOS_ENDPOINT")
    if not endpoint:
        return None
    try:
        from azure.cosmos import CosmosClient
        from azure.identity import DefaultAzureCredential

        database = os.environ.get("COSMOS_DATABASE", "disaster-hub")
        client = CosmosClient(endpoint, credential=DefaultAzureCredential())
        container = client.get_database_client(database).get_container_client("seed")
        items = list(
            container.query_items(
                query="SELECT * FROM c WHERE c.id = @id AND c.kind = 'disaster'",
                parameters=[{"name": "@id", "value": incident_id}],
                enable_cross_partition_query=True,
            )
        )
        return items[0] if items else None
    except Exception:
        logger.warning("Cosmos DB lookup failed for %s", incident_id, exc_info=True)
        return None


class DashboardService:
    def get_dashboard(self, incident_id: str) -> dict[str, object]:
        # Try in-memory store first (simulation incidents)
        incident = INCIDENTS.get(incident_id)
        if incident is not None:
            return self._build_from_model(incident, incident_id)

        # Fall back to Cosmos DB seed data (historical AIDR disasters)
        doc = _lookup_cosmos_incident(incident_id)
        if doc is not None:
            return self._build_from_cosmos(doc)

        raise KeyError(incident_id)

    def _build_from_model(self, incident: Any, incident_id: str) -> dict[str, object]:
        active_recommendations = [
            recommendation.model_dump(mode="json")
            for recommendation in RECOMMENDATIONS.values()
            if recommendation.incident_id == incident_id
        ]
        active_signals = [
            signal for signal in SIGNALS.values() if signal.incident_id == incident_id
        ]
        return {
            "incident": {
                "incidentId": incident.incident_id,
                "title": incident.title,
                "incidentType": incident.incident_type,
                "status": incident.status,
                "severity": incident.severity,
            },
            "participatingOrganisations": [
                {
                    "organisationId": org_id,
                    "name": org_id,
                    "category": "emergency_service",
                    "jurisdictionIds": incident.affected_jurisdiction_ids,
                    "operatingRole": "response",
                    "status": "active",
                }
                for org_id in incident.participating_organisation_ids
            ],
            "activeRecommendations": active_recommendations,
            "activeTasks": [],
            "signalSummary": {
                "authoritativeCount": sum(
                    1 for signal in active_signals
                    if signal.provenance.get("sourceKind") == "authoritative"
                ),
                "communityCount": sum(
                    1 for signal in active_signals
                    if signal.provenance.get("sourceKind") in {"community", "social"}
                ),
                "contradictedCount": sum(
                    1 for signal in active_signals
                    if signal.validation_status == "contradicted"
                ),
            },
        }

    @staticmethod
    def _build_from_cosmos(doc: dict[str, Any]) -> dict[str, object]:
        """Build a dashboard response from a Cosmos DB seed disaster document."""
        impact = doc.get("impact", {}) or {}
        location = doc.get("location", {}) or {}
        coords = location.get("coordinates", [])

        return {
            "incident": {
                "incidentId": doc.get("id", ""),
                "title": doc.get("name", doc.get("title", "Unknown Incident")),
                "incidentType": doc.get("incident_type", doc.get("category", "other")),
                "status": doc.get("status", "closed"),
                "severity": doc.get("severity", "unknown"),
                "region": doc.get("region", ""),
                "startedAt": doc.get("started_at", ""),
                "introduction": doc.get("introduction", ""),
                "sourceUrl": doc.get("source_url", ""),
                "location": {
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "latitude": coords[1] if len(coords) > 1 else None,
                },
                "impact": {
                    "deaths": impact.get("deaths"),
                    "injuries": impact.get("injuries"),
                    "homesDestroyed": impact.get("homes_destroyed"),
                    "businessesDestroyed": impact.get("businesses_destroyed"),
                    "insuranceCostAud": impact.get("insurance_cost_aud"),
                    "insuranceCostFormatted": impact.get("insurance_cost_formatted"),
                },
            },
            "participatingOrganisations": [],
            "activeRecommendations": [],
            "activeTasks": [],
            "signalSummary": {
                "authoritativeCount": 0,
                "communityCount": 0,
                "contradictedCount": 0,
            },
        }
