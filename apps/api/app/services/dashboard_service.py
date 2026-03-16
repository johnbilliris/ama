from app.services.state_store import INCIDENTS, RECOMMENDATIONS, SIGNALS


class DashboardService:
    def get_dashboard(self, incident_id: str) -> dict[str, object]:
        incident = INCIDENTS[incident_id]
        active_recommendations = [
            recommendation.model_dump(mode="json")
            for recommendation in RECOMMENDATIONS.values()
            if recommendation.incident_id == incident_id
        ]
        active_signals = [signal for signal in SIGNALS.values() if signal.incident_id == incident_id]
        return {
            "incident": {
                "incidentId": incident.incident_id,
                "title": incident.title,
                "incidentType": incident.incident_type,
                "status": incident.status,
                "severity": incident.severity,
            },
            "participatingOrganisations": [
                {"organisationId": org_id, "name": org_id, "category": "emergency_service", "jurisdictionIds": incident.affected_jurisdiction_ids, "operatingRole": "response", "status": "active"}
                for org_id in incident.participating_organisation_ids
            ],
            "activeRecommendations": active_recommendations,
            "activeTasks": [],
            "signalSummary": {
                "authoritativeCount": sum(1 for signal in active_signals if signal.provenance.get("sourceKind") == "authoritative"),
                "communityCount": sum(1 for signal in active_signals if signal.provenance.get("sourceKind") in {"community", "social"}),
                "contradictedCount": sum(1 for signal in active_signals if signal.validation_status == "contradicted"),
            },
        }
