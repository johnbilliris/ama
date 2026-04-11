"""AllocationProcessingPipeline — 9-stage orchestrator for resource allocation.

Stage 1: Handoff intake (validation, dedup, target check)
Stage 2: Recommendation/assessment retrieval
Stage 3: Demand identification (extract demands, normalise priorities)
Stage 4: Resource inventory query (load, filter eligible)
Stage 5: Resource-demand matching (greedy scoring, shortfalls)
Stage 6: Cross-incident analysis (contention, trade-offs)
Stage 7: Plan generation (version, confidence, LLM/template summary)
Stage 8: Plan persistence (Cosmos DB write, supersede previous)
Stage 9: Audit finalisation (comprehensive audit records)
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Callable
from uuid import uuid4

from common.handoffs import AgentHandoffEvent

from resource_allocation.audit import AuditWriter
from resource_allocation.config import ResourceAllocationConfig
from resource_allocation.dedup import HandoffDeduplicator
from resource_allocation.inventory import ResourceInventoryManager
from resource_allocation.matcher import ResourceMatcher
from resource_allocation.models import (
    AllocationDecisionRecord,
    ConfidenceLevel,
    DecisionType,
    DeploymentTimeline,
    InputSnapshot,
    PlanStatus,
    PriorityTier,
    ResourceAssignment,
    ResourceDemand,
    ResourceDeploymentPlan,
    ResourceType,
    ShortfallDetail,
    Traceability,
    TradeOffAnalysis,
    UrgencyLevel,
    confidence_to_level,
)
from resource_allocation.priority import (
    DemandQueue,
    classify_priority_tier,
    normalise_urgency,
)
from resource_allocation.templates import (
    generate_plan_summary,
    generate_transport_dispatch_summary,
)
from resource_allocation.versioning import VersionCounter

logger = logging.getLogger(__name__)


class AllocationProcessingPipeline:
    """9-stage orchestrator for resource allocation processing."""

    def __init__(
        self,
        config: ResourceAllocationConfig | None = None,
        dedup: HandoffDeduplicator | None = None,
        inventory: ResourceInventoryManager | None = None,
        matcher: ResourceMatcher | None = None,
        version_counter: VersionCounter | None = None,
        audit_writer: AuditWriter | None = None,
        llm_generate_fn: Callable[..., dict] | None = None,
        cosmos_plans_container: Any = None,
        cosmos_assessments_container: Any = None,
    ) -> None:
        self._config = config or ResourceAllocationConfig()
        self._dedup = dedup or HandoffDeduplicator(
            window_minutes=self._config.handoff_dedup_window_minutes
        )
        self._inventory = inventory or ResourceInventoryManager(config=self._config)
        self._matcher = matcher or ResourceMatcher(config=self._config)
        self._version_counter = version_counter or VersionCounter()
        self._audit = audit_writer or AuditWriter(config=self._config)
        self._llm_generate_fn = llm_generate_fn
        self._cosmos_plans = cosmos_plans_container
        self._cosmos_assessments = cosmos_assessments_container

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def process_handoff(self, handoff: AgentHandoffEvent) -> ResourceDeploymentPlan | None:
        """Process a handoff event through all 9 pipeline stages.

        Returns the generated ResourceDeploymentPlan, or None if rejected.
        """
        start_time = time.monotonic()
        config_hash = self._config.compute_config_hash()
        incident_scope_key = f"{handoff.tenant_id}:{handoff.incident_id}"

        # Stage 1: Handoff intake
        if not self._stage1_validate_handoff(handoff, config_hash, incident_scope_key):
            return None

        # Stage 2: Retrieve recommendation/assessment data
        recommendation_data, assessment_data = self._stage2_retrieve_data(
            handoff, config_hash, incident_scope_key
        )

        # Stage 3: Demand identification
        demands = self._stage3_identify_demands(
            handoff, recommendation_data, assessment_data, config_hash, incident_scope_key
        )
        if not demands:
            logger.warning("No demands extracted from handoff %s", handoff.handoff_id)
            return None

        # Stage 4: Resource inventory query
        eligible_resources = self._stage4_query_inventory(
            demands, config_hash, incident_scope_key
        )

        # Stage 5: Resource-demand matching
        assignments, shortfalls = self._stage5_match_resources(
            demands, eligible_resources, handoff, config_hash, incident_scope_key
        )

        # Stage 6: Cross-incident analysis
        trade_off = self._stage6_cross_incident_analysis(
            demands, eligible_resources, handoff, config_hash, incident_scope_key
        )

        # Stage 7: Plan generation
        plan = self._stage7_generate_plan(
            handoff=handoff,
            demands=demands,
            assignments=assignments,
            shortfalls=shortfalls,
            trade_off=trade_off,
            config_hash=config_hash,
            incident_scope_key=incident_scope_key,
        )

        # Stage 8: Plan persistence
        self._stage8_persist_plan(plan, config_hash, incident_scope_key)

        # Stage 9: Audit finalisation
        duration_ms = (time.monotonic() - start_time) * 1000
        self._stage9_audit_finalise(
            handoff, plan, duration_ms, config_hash, incident_scope_key
        )

        logger.info(
            "Plan %s generated in %.1fms (v%d, confidence=%.2f, %d assignments, %d shortfalls)",
            plan.plan_id, duration_ms, plan.version,
            plan.confidence_score, len(assignments), len(shortfalls),
        )

        return plan

    # ------------------------------------------------------------------
    # Stage 1: Handoff intake
    # ------------------------------------------------------------------

    def _stage1_validate_handoff(
        self,
        handoff: AgentHandoffEvent,
        config_hash: str,
        incident_scope_key: str,
    ) -> bool:
        """Validate handoff: target check, dedup, incident existence."""
        # Target agent check
        if handoff.target_agent != "resource_allocation":
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.handoff_rejected,
                rationale=f"Wrong target agent: {handoff.target_agent}",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
            )
            return False

        # Source agent check
        if handoff.source_agent not in ("risk_assessment", "evacuation"):
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.handoff_rejected,
                rationale=f"Unknown source agent: {handoff.source_agent}",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
            )
            return False

        # Dedup check
        if self._dedup.is_duplicate(handoff.handoff_id):
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.duplicate_discarded,
                rationale=f"Duplicate handoff within dedup window",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
            )
            return False

        # Incident existence check (basic — incident_id must be present)
        if not handoff.incident_id:
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.handoff_rejected,
                rationale="Missing incident_id",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
            )
            return False

        # Valid handoff — audit receipt
        self._write_audit(
            handoff_id=handoff.handoff_id,
            decision_type=DecisionType.handoff_received,
            rationale=f"Valid handoff from {handoff.source_agent}",
            config_hash=config_hash,
            incident_scope_key=incident_scope_key,
            tenant_id=handoff.tenant_id,
        )
        return True

    # ------------------------------------------------------------------
    # Stage 2: Recommendation/assessment retrieval
    # ------------------------------------------------------------------

    def _stage2_retrieve_data(
        self,
        handoff: AgentHandoffEvent,
        config_hash: str,
        incident_scope_key: str,
    ) -> tuple[dict | None, dict | None]:
        """Retrieve recommendation and assessment data from Cosmos DB or payload."""
        payload = handoff.payload or {}

        if handoff.source_agent == "risk_assessment":
            recommendation_id = payload.get("recommendationId")
            assessment_id = payload.get("assessmentId")
            summary = payload.get("summary", "")

            recommendation_data = {
                "recommendationId": recommendation_id,
                "summary": summary,
                "assessmentId": assessment_id,
            }

            # Try to retrieve full assessment from Cosmos
            assessment_data = None
            if self._cosmos_assessments and assessment_id:
                try:
                    assessment_data = self._cosmos_assessments.read_item(
                        item=assessment_id,
                        partition_key=incident_scope_key,
                    )
                except Exception:
                    logger.warning("Could not retrieve assessment %s", assessment_id)

            return recommendation_data, assessment_data

        elif handoff.source_agent == "evacuation":
            # Evacuation handoffs have transport requirements in payload
            return payload, None

        return None, None

    # ------------------------------------------------------------------
    # Stage 3: Demand identification
    # ------------------------------------------------------------------

    def _stage3_identify_demands(
        self,
        handoff: AgentHandoffEvent,
        recommendation_data: dict | None,
        assessment_data: dict | None,
        config_hash: str,
        incident_scope_key: str,
    ) -> list[ResourceDemand]:
        """Extract resource demands from handoff data and normalise priorities."""
        demands = []
        queue = DemandQueue()

        if handoff.source_agent == "evacuation":
            # Transport dispatch path
            demands = self._extract_transport_demands(handoff, incident_scope_key)
        else:
            # Risk assessment coordination task path
            demands = self._extract_coordination_demands(
                handoff, recommendation_data, assessment_data, incident_scope_key
            )

        # Insert into priority queue
        for demand in demands:
            queue.insert(demand)
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.demand_identified,
                rationale=f"Demand {demand.demand_id}: {demand.resource_sub_type} x{demand.quantity}",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
                demand_id=demand.demand_id,
                priority_tier=demand.priority_tier.value,
                urgency=demand.urgency.value,
            )

        return queue.to_list()

    def _extract_transport_demands(
        self,
        handoff: AgentHandoffEvent,
        incident_scope_key: str,
    ) -> list[ResourceDemand]:
        """Extract demands from evacuation transport requirements."""
        payload = handoff.payload or {}
        requirements = payload.get("transportRequirements", [])
        evacuation_plan_id = payload.get("evacuationPlanId", "")
        demands = []

        for req in requirements:
            raw_priority = req.get("priority", "high")
            urgency = normalise_urgency(raw_priority, "evacuation")

            demand = ResourceDemand(
                demand_id=f"dem-{uuid4().hex[:12]}",
                incident_id=handoff.incident_id,
                source_id=req.get("requirementId", f"tr-{uuid4().hex[:8]}"),
                source_type="transport_requirement",
                resource_type=ResourceType.vehicle,
                resource_sub_type=req.get("vehicleType", "bus"),
                required_capabilities=self._infer_transport_capabilities(req.get("vehicleType", "")),
                quantity=req.get("quantity", 1),
                location=req.get("pickupLocation", {}),
                priority_tier=PriorityTier.tier_1_life_safety,
                urgency=urgency,
                urgency_raw=raw_priority,
                fulfilment_status="pending",
                handoff_id=handoff.handoff_id,
                incident_scope_key=incident_scope_key,
            )
            demands.append(demand)

        return demands

    def _extract_coordination_demands(
        self,
        handoff: AgentHandoffEvent,
        recommendation_data: dict | None,
        assessment_data: dict | None,
        incident_scope_key: str,
    ) -> list[ResourceDemand]:
        """Extract demands from risk assessment coordination tasks."""
        payload = handoff.payload or {}
        summary = payload.get("summary", "")
        demands = []

        # Parse summary and assessment data to identify resource needs
        # This uses keyword-based extraction from the coordination task summary
        resource_needs = self._parse_resource_needs(summary, assessment_data)

        for i, need in enumerate(resource_needs):
            raw_priority = need.get("priority", "moderate")
            urgency = normalise_urgency(raw_priority, "risk_assessment")
            tier_context = {
                "source_type": "coordination_task",
                "resource_sub_type": need.get("sub_type", ""),
                "demand_type": need.get("type", ""),
            }
            priority_tier = classify_priority_tier(tier_context)

            demand = ResourceDemand(
                demand_id=f"dem-{uuid4().hex[:12]}",
                incident_id=handoff.incident_id,
                source_id=payload.get("recommendationId", f"rec-{uuid4().hex[:8]}"),
                source_type="coordination_task",
                resource_type=ResourceType(need.get("type", "vehicle")),
                resource_sub_type=need.get("sub_type", ""),
                required_capabilities=need.get("capabilities", []),
                quantity=need.get("quantity", 1),
                location=need.get("location", {"lat": -33.8688, "lon": 151.2093}),
                priority_tier=priority_tier,
                urgency=urgency,
                urgency_raw=raw_priority,
                fulfilment_status="pending",
                handoff_id=handoff.handoff_id,
                incident_scope_key=incident_scope_key,
            )
            demands.append(demand)

        # If no explicit needs found, create a generic demand from summary
        if not demands and summary:
            demands.append(ResourceDemand(
                demand_id=f"dem-{uuid4().hex[:12]}",
                incident_id=handoff.incident_id,
                source_id=payload.get("recommendationId", f"rec-{uuid4().hex[:8]}"),
                source_type="coordination_task",
                resource_type=ResourceType.personnel,
                resource_sub_type="emergency_responder",
                required_capabilities=[],
                quantity=1,
                location={"lat": -33.8688, "lon": 151.2093},
                priority_tier=PriorityTier.tier_2_property,
                urgency=UrgencyLevel.moderate,
                urgency_raw="moderate",
                fulfilment_status="pending",
                handoff_id=handoff.handoff_id,
                incident_scope_key=incident_scope_key,
            ))

        return demands

    def _parse_resource_needs(
        self,
        summary: str,
        assessment_data: dict | None,
    ) -> list[dict]:
        """Parse summary text and assessment data to identify resource needs."""
        needs: list[dict] = []
        summary_lower = summary.lower()

        # Keyword-based extraction
        resource_keywords = {
            "water tanker": {"type": "vehicle", "sub_type": "water_tanker", "capabilities": ["water_delivery"]},
            "ambulance": {"type": "vehicle", "sub_type": "ambulance", "capabilities": ["medical_transport", "patient_stabilization"]},
            "fire truck": {"type": "vehicle", "sub_type": "fire_truck", "capabilities": ["firefighting"]},
            "helicopter": {"type": "vehicle", "sub_type": "helicopter", "capabilities": ["aerial_support"]},
            "paramedic": {"type": "personnel", "sub_type": "paramedic", "capabilities": ["medical_treatment"]},
            "firefighter": {"type": "personnel", "sub_type": "firefighter", "capabilities": ["firefighting"]},
            "medical team": {"type": "personnel", "sub_type": "paramedic", "capabilities": ["medical_treatment"]},
            "medical kit": {"type": "supply", "sub_type": "medical_kit", "capabilities": ["medical_supply"]},
            "generator": {"type": "supply", "sub_type": "generator", "capabilities": ["power_supply"]},
            "evacuation centre": {"type": "facility", "sub_type": "evacuation_centre", "capabilities": ["shelter"]},
            "bus": {"type": "vehicle", "sub_type": "bus", "capabilities": ["passenger_transport"]},
        }

        for keyword, resource_info in resource_keywords.items():
            if keyword in summary_lower:
                need = dict(resource_info)
                # Try to extract quantity from summary
                need["quantity"] = self._extract_quantity(summary_lower, keyword)
                need["priority"] = self._infer_priority(summary_lower)
                needs.append(need)

        # Extract coordination tasks from assessment data
        if assessment_data:
            tasks = assessment_data.get("coordination_tasks", [])
            for task in tasks:
                need = {
                    "type": task.get("resource_type", "personnel"),
                    "sub_type": task.get("resource_sub_type", ""),
                    "capabilities": task.get("required_capabilities", []),
                    "quantity": task.get("quantity", 1),
                    "priority": task.get("priority", "moderate"),
                    "location": task.get("location"),
                }
                needs.append(need)

        return needs

    def _extract_quantity(self, text: str, keyword: str) -> int:
        """Extract quantity from text near a keyword."""
        import re
        # Look for patterns like "3 ambulances", "five water tankers"
        word_numbers = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        idx = text.find(keyword)
        if idx > 0:
            preceding = text[max(0, idx - 20):idx].strip()
            # Check for digit
            match = re.search(r"(\d+)\s*$", preceding)
            if match:
                return int(match.group(1))
            # Check for word numbers
            for word, num in word_numbers.items():
                if word in preceding:
                    return num
        return 1

    def _extract_priority(self, text: str) -> str:
        """Extract priority from text."""
        if "critical" in text:
            return "critical"
        if "urgent" in text or "immediate" in text:
            return "critical"
        if "high" in text:
            return "high"
        if "moderate" in text or "medium" in text:
            return "moderate"
        return "moderate"

    def _infer_priority(self, text: str) -> str:
        """Infer priority from summary text."""
        return self._extract_priority(text)

    def _infer_transport_capabilities(self, vehicle_type: str) -> list[str]:
        """Infer capabilities from vehicle type for transport requests."""
        cap_map = {
            "wheelchair_accessible": ["passenger_transport", "wheelchair_accessible"],
            "ambulance": ["medical_transport", "patient_stabilization"],
            "bus": ["passenger_transport"],
            "helicopter": ["aerial_transport"],
            "minibus": ["passenger_transport"],
        }
        return cap_map.get(vehicle_type, ["passenger_transport"])

    # ------------------------------------------------------------------
    # Stage 4: Resource inventory query
    # ------------------------------------------------------------------

    def _stage4_query_inventory(
        self,
        demands: list[ResourceDemand],
        config_hash: str,
        incident_scope_key: str,
    ) -> list[ResourceInventoryItem]:
        """Load and filter eligible resources from inventory."""
        from resource_allocation.models import ResourceInventoryItem

        all_eligible: list[ResourceInventoryItem] = []
        seen_ids: set[str] = set()

        for demand in demands:
            eligible = self._inventory.get_eligible_resources(demand)
            for resource in eligible:
                if resource.resource_id not in seen_ids:
                    all_eligible.append(resource)
                    seen_ids.add(resource.resource_id)

        # Apply operational limit flags
        self._inventory.flag_operational_limits(all_eligible)

        return all_eligible

    # ------------------------------------------------------------------
    # Stage 5: Resource-demand matching
    # ------------------------------------------------------------------

    def _stage5_match_resources(
        self,
        demands: list[ResourceDemand],
        eligible_resources: list[ResourceInventoryItem],
        handoff: AgentHandoffEvent,
        config_hash: str,
        incident_scope_key: str,
    ) -> tuple[list[ResourceAssignment], list[ShortfallDetail]]:
        """Match demands to resources using greedy algorithm."""
        assignments, shortfalls = self._matcher.match_demands(
            demands=demands,
            eligible_resources=eligible_resources,
            config=self._config,
        )

        # Audit matched resources
        for assignment in assignments:
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.resource_matched,
                rationale=f"Resource {assignment.resource_id} matched to demand {assignment.demand_id}",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
                demand_id=assignment.demand_id,
                resource_id=assignment.resource_id,
            )

        # Audit shortfalls
        for shortfall in shortfalls:
            self._write_audit(
                handoff_id=handoff.handoff_id,
                decision_type=DecisionType.partial_allocation,
                rationale=f"Shortfall for demand {shortfall.demand_id}: {shortfall.quantity_unmet} unmet",
                config_hash=config_hash,
                incident_scope_key=incident_scope_key,
                tenant_id=handoff.tenant_id,
                demand_id=shortfall.demand_id,
            )

        return assignments, shortfalls

    # ------------------------------------------------------------------
    # Stage 6: Cross-incident analysis
    # ------------------------------------------------------------------

    def _stage6_cross_incident_analysis(
        self,
        demands: list[ResourceDemand],
        eligible_resources: list[ResourceInventoryItem],
        handoff: AgentHandoffEvent,
        config_hash: str,
        incident_scope_key: str,
    ) -> TradeOffAnalysis | None:
        """Detect cross-incident contention and generate trade-off analysis."""
        contentions = self._matcher.detect_cross_incident_contention(
            demands, eligible_resources
        )

        if not contentions:
            return None

        competing_incidents = set()
        contested_resources = []
        for c in contentions:
            competing_incidents.update(c["competing_incidents"])
            contested_resources.append(c["resource_id"])

        trade_off = TradeOffAnalysis(
            competing_incidents=sorted(competing_incidents),
            contested_resources=contested_resources,
            allocations=[],
            reallocation_recommendations=[],
            impact_summary=f"{len(contested_resources)} resource(s) demanded by {len(competing_incidents)} incidents",
            requires_commander_approval=True,
        )

        self._write_audit(
            handoff_id=handoff.handoff_id,
            decision_type=DecisionType.reallocation_recommended,
            rationale=f"Cross-incident contention: {len(contested_resources)} contested resources",
            config_hash=config_hash,
            incident_scope_key=incident_scope_key,
            tenant_id=handoff.tenant_id,
        )

        return trade_off

    # ------------------------------------------------------------------
    # Stage 7: Plan generation
    # ------------------------------------------------------------------

    def _stage7_generate_plan(
        self,
        handoff: AgentHandoffEvent,
        demands: list[ResourceDemand],
        assignments: list[ResourceAssignment],
        shortfalls: list[ShortfallDetail],
        trade_off: TradeOffAnalysis | None,
        config_hash: str,
        incident_scope_key: str,
    ) -> ResourceDeploymentPlan:
        """Generate versioned deployment plan with LLM or template summary."""
        # Assign version
        version = self._version_counter.assign_version(
            incident_id=handoff.incident_id,
            incident_scope_key=incident_scope_key,
        )

        plan_id = f"rdp-{handoff.incident_id}-v{version}"

        # Compute confidence
        confidence = self._config.confidence_base
        generation_method = "ai_assisted"

        # Generate summary
        summary = self._generate_summary(
            handoff=handoff,
            demands=demands,
            assignments=assignments,
            shortfalls=shortfalls,
            trade_off=trade_off,
            confidence=confidence,
        )

        if summary.get("generation_method") in ("template_fallback", "safety_fallback"):
            confidence *= self._config.fallback_reduction_factor
            generation_method = summary["generation_method"]

        confidence = max(0.0, min(1.0, confidence))
        confidence_level = confidence_to_level(confidence)

        # Build deployment timelines
        timelines = self._build_timelines(assignments)

        # Build input snapshot
        input_snapshot = InputSnapshot(
            demands_snapshot=[d.model_dump(mode="json") for d in demands],
            inventory_snapshot_hash=self._inventory.compute_inventory_hash(),
            inventory_staleness_minutes=self._compute_inventory_staleness(),
            config_version=config_hash,
            scoring_parameters={
                "priority_weights": {
                    "critical": self._config.priority_weight_critical,
                    "high": self._config.priority_weight_high,
                    "moderate": self._config.priority_weight_moderate,
                    "low": self._config.priority_weight_low,
                },
                "distance_floor_km": self._config.distance_floor_km,
                "availability_returning": self._config.availability_returning,
            },
        )

        # Build traceability
        payload = handoff.payload or {}
        traceability = Traceability(
            handoff_id=handoff.handoff_id,
            recommendation_id=payload.get("recommendationId"),
            assessment_id=payload.get("assessmentId"),
            evacuation_plan_id=payload.get("evacuationPlanId"),
            transport_requirement_ids=[
                r.get("requirementId", "")
                for r in payload.get("transportRequirements", [])
                if r.get("requirementId")
            ],
        )

        now = datetime.now(UTC)
        plan = ResourceDeploymentPlan(
            plan_id=plan_id,
            incident_id=handoff.incident_id,
            version=version,
            demands=demands,
            assignments=assignments,
            unmet_demands=shortfalls,
            deployment_timelines=timelines,
            confidence_score=confidence,
            confidence_level=confidence_level,
            status=PlanStatus.proposed,
            generation_method=generation_method,
            configuration_version=config_hash,
            input_snapshot=input_snapshot,
            traceability=traceability,
            summary=str(summary.get("text", "")),
            trade_off_analysis=trade_off,
            expires_at=now + timedelta(hours=self._config.plan_expiry_hours),
            incident_scope_key=incident_scope_key,
            tenant_id=handoff.tenant_id,
            created_at=now,
            updated_at=now,
        )

        return plan

    def _generate_summary(
        self,
        handoff: AgentHandoffEvent,
        demands: list[ResourceDemand],
        assignments: list[ResourceAssignment],
        shortfalls: list[ShortfallDetail],
        trade_off: TradeOffAnalysis | None,
        confidence: float,
    ) -> dict:
        """Generate plan summary using LLM with template fallback."""
        # Build template text first (always available)
        template_text = generate_plan_summary(
            plan=None,
            assignments=assignments,
            shortfalls=shortfalls,
            trade_offs=trade_off,
        )

        # For transport dispatch, use transport-specific template
        if handoff.source_agent == "evacuation":
            evac_plan_id = (handoff.payload or {}).get("evacuationPlanId")
            template_text = generate_transport_dispatch_summary(
                assignments=assignments,
                evacuation_plan_id=evac_plan_id,
            )

        # Try LLM generation
        if self._llm_generate_fn is not None:
            try:
                prompt = (
                    f"Generate a concise AIIMS-consistent resource allocation summary. "
                    f"Incident: {handoff.incident_id}. "
                    f"{len(assignments)} resources assigned, {len(shortfalls)} shortfalls. "
                    f"Confidence: {confidence:.2f}. "
                    f"Include deployment priorities and any trade-offs."
                )
                result = self._llm_generate_fn(
                    purpose="reasoning",
                    prompt=prompt,
                    template_text=template_text,
                    max_output_tokens=300,
                    timeout_seconds=10.0,
                )
                return result
            except Exception as exc:
                logger.warning("LLM summary generation failed: %s", exc)

        return {
            "text": template_text,
            "generation_method": "template_fallback",
        }

    def _build_timelines(
        self,
        assignments: list[ResourceAssignment],
    ) -> list[DeploymentTimeline]:
        """Build deployment timelines from assignments."""
        timelines = []
        now = datetime.now(UTC)

        for assignment in assignments:
            timeline = DeploymentTimeline(
                assignment_id=assignment.assignment_id,
                resource_id=assignment.resource_id,
                mobilisation_minutes=assignment.mobilisation_minutes,
                travel_minutes=assignment.estimated_travel_minutes - assignment.mobilisation_minutes,
                total_deployment_minutes=assignment.estimated_travel_minutes,
                estimated_departure=now + timedelta(minutes=assignment.mobilisation_minutes),
                estimated_arrival=assignment.estimated_arrival_time,
            )
            timelines.append(timeline)

        return timelines

    def _compute_inventory_staleness(self) -> float:
        """Compute how stale the inventory data is in minutes."""
        last_loaded = self._inventory.last_loaded_at
        if last_loaded is None:
            return 0.0
        delta = datetime.now(UTC) - last_loaded
        return delta.total_seconds() / 60.0

    # ------------------------------------------------------------------
    # Stage 8: Plan persistence
    # ------------------------------------------------------------------

    def _stage8_persist_plan(
        self,
        plan: ResourceDeploymentPlan,
        config_hash: str,
        incident_scope_key: str,
    ) -> None:
        """Persist plan to Cosmos DB, superseding previous versions."""
        if self._cosmos_plans is not None:
            try:
                # Supersede previous versions
                self._supersede_previous_plans(
                    plan.incident_id, plan.version, incident_scope_key, config_hash
                )

                # Write new plan
                doc = plan.model_dump(mode="json")
                doc["id"] = plan.plan_id
                self._cosmos_plans.create_item(body=doc)
            except Exception as exc:
                logger.error("Failed to persist plan %s: %s", plan.plan_id, exc)

    def _supersede_previous_plans(
        self,
        incident_id: str,
        current_version: int,
        incident_scope_key: str,
        config_hash: str,
    ) -> None:
        """Mark previous plan versions as superseded."""
        if self._cosmos_plans is None:
            return

        for v in range(1, current_version):
            old_plan_id = f"rdp-{incident_id}-v{v}"
            try:
                doc = self._cosmos_plans.read_item(
                    item=old_plan_id,
                    partition_key=incident_scope_key,
                )
                if doc.get("status") in ("proposed", "approved"):
                    doc["status"] = "superseded"
                    doc["updated_at"] = datetime.now(UTC).isoformat()
                    self._cosmos_plans.replace_item(item=old_plan_id, body=doc)

                    self._write_audit(
                        handoff_id=doc.get("traceability", {}).get("handoff_id", ""),
                        decision_type=DecisionType.plan_superseded,
                        rationale=f"Plan {old_plan_id} superseded by v{current_version}",
                        config_hash=config_hash,
                        incident_scope_key=incident_scope_key,
                        tenant_id=doc.get("tenant_id", "live"),
                        plan_id=old_plan_id,
                        plan_version=v,
                    )
            except Exception:
                pass  # Plan may not exist or already superseded

    # ------------------------------------------------------------------
    # Stage 9: Audit finalisation
    # ------------------------------------------------------------------

    def _stage9_audit_finalise(
        self,
        handoff: AgentHandoffEvent,
        plan: ResourceDeploymentPlan,
        duration_ms: float,
        config_hash: str,
        incident_scope_key: str,
    ) -> None:
        """Write final audit record for plan generation."""
        self._write_audit(
            handoff_id=handoff.handoff_id,
            decision_type=DecisionType.plan_generated,
            rationale=f"Plan {plan.plan_id} generated with {len(plan.assignments)} assignments",
            config_hash=config_hash,
            incident_scope_key=incident_scope_key,
            tenant_id=handoff.tenant_id,
            plan_id=plan.plan_id,
            plan_version=plan.version,
            confidence_score=plan.confidence_score,
            processing_duration_ms=duration_ms,
            generation_method=plan.generation_method,
        )

    # ------------------------------------------------------------------
    # Audit helper
    # ------------------------------------------------------------------

    def _write_audit(
        self,
        handoff_id: str,
        decision_type: DecisionType,
        rationale: str,
        config_hash: str,
        incident_scope_key: str,
        tenant_id: str = "live",
        plan_id: str | None = None,
        plan_version: int | None = None,
        demand_id: str | None = None,
        resource_id: str | None = None,
        confidence_score: float = 0.0,
        processing_duration_ms: float = 0.0,
        generation_method: str = "algorithmic",
        priority_tier: str | None = None,
        urgency: str | None = None,
    ) -> None:
        """Write a single audit record."""
        record = AllocationDecisionRecord(
            handoff_id=handoff_id,
            plan_id=plan_id,
            plan_version=plan_version,
            demand_id=demand_id,
            resource_id=resource_id,
            decision_type=decision_type,
            confidence_score=confidence_score,
            priority_tier=priority_tier,
            urgency=urgency,
            processing_duration_ms=processing_duration_ms,
            decision_rationale=rationale,
            generation_method=generation_method,
            agent_version=self._config.agent_version,
            configuration_version=config_hash,
            incident_scope_key=incident_scope_key,
            tenant_id=tenant_id,
        )
        self._audit.write(record)
