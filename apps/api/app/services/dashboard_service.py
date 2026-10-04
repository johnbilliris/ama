import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.middleware.resilience import retry_transient_dependency_call
from app.services.degraded_mode_service import DegradedModeService
from app.services.operational_store import OperationalStore
from app.services.organisation_intelligence_service import OrganisationIntelligenceService
from app.services.recommendation_guardrails import apply_recommendation_guardrails
from app.services.seed_service import SeedService
from app.services.state_store import HANDOFF_EVENTS

logger = logging.getLogger(__name__)


def _query_cosmos_incident(container: Any, incident_id: str) -> list[dict[str, Any]]:
    return list(
        container.query_items(
            query="SELECT * FROM c WHERE c.id = @id AND c.kind = 'disaster'",
            parameters=[{"name": "@id", "value": incident_id}],
            enable_cross_partition_query=True,
        )
    )


_query_cosmos_incident_with_retry = retry_transient_dependency_call(_query_cosmos_incident)


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
        items = _query_cosmos_incident_with_retry(container, incident_id)
        return items[0] if items else None
    except Exception:
        logger.warning("Cosmos DB lookup failed for %s", incident_id, exc_info=True)
        return None


class DashboardService:
    _ALERT_APPROVER_ROLES = {"incident-commander", "public-information-officer"}

    def __init__(self) -> None:
        self._org_service = OrganisationIntelligenceService()
        self._seed_service = SeedService()

    @staticmethod
    def _handoff_projection(incident_id: str) -> dict[str, object]:
        handoffs = HANDOFF_EVENTS.get(incident_id, [])
        status_counts: dict[str, int] = {}
        for handoff in handoffs:
            status = str(handoff.get("status", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1

        recent = [
            {
                "handoffId": handoff.get("handoffId"),
                "sourceAgent": handoff.get("sourceAgent"),
                "targetAgent": handoff.get("targetAgent"),
                "status": handoff.get("status"),
                "attemptCount": handoff.get("attemptCount"),
                "retryCount": handoff.get("retryCount"),
                "timelineEventId": handoff.get("timelineEventId"),
                "deadLetterEntryId": handoff.get("deadLetterEntryId"),
                "payloadSummary": handoff.get("payloadSummary"),
            }
            for handoff in handoffs[-5:]
        ]
        return {
            "total": len(handoffs),
            "statusCounts": status_counts,
            "recent": recent,
        }

    @staticmethod
    def _is_authoritative_signal(signal: Any) -> bool:
        trust_tier = str(
            getattr(signal, "trust_tier", None)
            or signal.provenance.get("trustTier")
            or signal.provenance.get("derivedTrustTier", "")
        )
        if trust_tier in {
            "tier_1_authoritative_government",
            "tier_2_verified_institutional",
            "tier_3_operational_sensor",
        }:
            return True
        source_kind = str(
            getattr(signal, "source_kind", None)
            or signal.provenance.get("sourceKind")
            or signal.provenance.get("derivedSourceKind", "")
        )
        return source_kind in {"authoritative", "sensor", "iot", "field_report"}

    @staticmethod
    def _is_community_signal(signal: Any) -> bool:
        source_kind = str(
            getattr(signal, "source_kind", None)
            or signal.provenance.get("sourceKind")
            or signal.provenance.get("derivedSourceKind", "")
        )
        return source_kind in {"community", "social"}

    def get_dashboard(
        self, incident_id: str, *, actor_roles: tuple[str, ...] = (), actor_persona_id: str | None = None
    ) -> dict[str, object]:
        store = OperationalStore.current()
        # Try in-memory store first (simulation incidents)
        incident = store.incidents.get(incident_id)
        if incident is not None:
            return self._build_from_model(
                incident,
                incident_id,
                store,
                actor_roles=actor_roles,
                actor_persona_id=actor_persona_id,
            )

        # Fall back to Cosmos DB seed data (historical AIDR disasters)
        doc = _lookup_cosmos_incident(incident_id)
        if doc is not None:
            return self._build_from_cosmos(doc)

        raise KeyError(incident_id)

    def _framework_context(self, framework_ids: list[str]) -> list[dict[str, Any]]:
        if not framework_ids:
            return []
        seeds = self._seed_service.load_default()
        framework_rows = {row.get("framework_id"): row for row in seeds.get("frameworks", [])}
        context: list[dict[str, Any]] = []
        for framework_id in framework_ids:
            row = framework_rows.get(framework_id)
            if row:
                context.append(
                    {
                        "frameworkId": row.get("framework_id"),
                        "name": row.get("name", ""),
                        "frameworkType": row.get("framework_type", "other"),
                        "principles": row.get("principles", []),
                        "status": row.get("status", "active"),
                    }
                )
        return context

    def _incident_geometry(self, incident: Any) -> dict[str, Any] | None:
        location = incident.location
        if isinstance(location, dict):
            return location
        seeds = self._seed_service.load_default()
        jurisdictions = {row.get("jurisdiction_id"): row for row in seeds.get("jurisdictions", [])}
        for jurisdiction_id in incident.affected_jurisdiction_ids:
            row = jurisdictions.get(jurisdiction_id)
            boundary = row.get("geospatial_boundary") if row else None
            if isinstance(boundary, dict):
                return boundary
        return None

    def _source_status_index(self, signals: list[Any]) -> dict[str, str | dict[str, str]]:
        now = datetime.now(UTC)
        status_index: dict[str, str | dict[str, str]] = {}
        for signal in signals:
            source_id = str(signal.data_source_id)
            state = str(signal.provenance.get("sourceStatus", "available"))
            reason = str(signal.provenance.get("sourceReason", state))
            received_at = signal.received_at
            age_seconds = (now - received_at).total_seconds()
            freshness_window = int(signal.provenance.get("expectedUpdateSeconds", 600))
            if age_seconds > freshness_window:
                state = "stale"
                reason = "stale_signal_window"
            status_index[source_id] = {
                "status": state,
                "reason": reason,
                "since": received_at.isoformat(),
            }
        return status_index

    def _resolve_participating_organisations(self, incident: Any) -> list[dict[str, Any]]:
        organisations = self._org_service.list_organisations(incident.affected_jurisdiction_ids)
        by_id = {org.organisation_id: org for org in organisations}
        resolved: list[dict[str, Any]] = []
        for org_id in incident.participating_organisation_ids:
            org = by_id.get(org_id)
            if org is None:
                continue
            resolved.append(
                {
                    "organisationId": org.organisation_id,
                    "name": org.name,
                    "category": org.category,
                    "jurisdictionIds": org.jurisdiction_ids,
                    "operatingRole": org.operating_role,
                    "status": org.status,
                }
            )
        return resolved

    def _build_from_model(
        self,
        incident: Any,
        incident_id: str,
        store: OperationalStore,
        *,
        actor_roles: tuple[str, ...],
        actor_persona_id: str | None,
    ) -> dict[str, object]:
        active_signals = [signal for signal in store.signals.values() if signal.incident_id == incident_id]
        source_status = self._source_status_index(active_signals)
        degraded_mode = DegradedModeService().evaluate(source_status)
        signal_source_by_id = {signal.signal_id: str(signal.data_source_id) for signal in active_signals}
        can_approve_alerts = bool(actor_persona_id) and bool(self._ALERT_APPROVER_ROLES.intersection(actor_roles))

        active_recommendations: list[dict[str, Any]] = []
        for recommendation in store.recommendations.values():
            if recommendation.incident_id != incident_id:
                continue
            guarded = apply_recommendation_guardrails(
                recommendation.model_dump(mode="json"),
                degraded_mode,
                signal_source_by_id=signal_source_by_id,
            )
            if guarded.get("status") == "suppressed":
                continue
            guarded["approvalAction"] = {
                "allowed": can_approve_alerts,
                "requiresPersona": True,
            }
            active_recommendations.append(guarded)

        active_tasks = [
            task.model_dump(mode="json")
            for task in store.tasks.values()
            if getattr(task, "incident_id", "") == incident_id
        ]

        return {
            "incident": {
                "incidentId": incident.incident_id,
                "title": incident.title,
                "incidentType": incident.incident_type,
                "status": incident.status,
                "severity": incident.severity,
                "actorPersonaId": actor_persona_id,
                "frameworkContext": self._framework_context(incident.owning_framework_ids),
                "geometry": self._incident_geometry(incident),
            },
            "participatingOrganisations": self._resolve_participating_organisations(incident),
            "activeRecommendations": active_recommendations,
            "activeTasks": active_tasks,
            "handoffSummary": self._handoff_projection(incident_id),
            "signalSummary": {
                "authoritativeCount": sum(1 for signal in active_signals if self._is_authoritative_signal(signal)),
                "communityCount": sum(1 for signal in active_signals if self._is_community_signal(signal)),
                "contradictedCount": sum(1 for signal in active_signals if signal.validation_status == "contradicted"),
                "degradedSources": list(degraded_mode.degraded_source_details),
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
            "handoffSummary": {
                "total": 0,
                "statusCounts": {},
                "recent": [],
            },
            "signalSummary": {
                "authoritativeCount": 0,
                "communityCount": 0,
                "contradictedCount": 0,
            },
        }
