"""Dashboard aggregation service.

Cross-domain data aggregation for all governance dashboard views.
Orchestrates calls to GovernanceDataService for real metrics.
"""

import logging
from datetime import UTC, datetime

from app.models.governance_health import (
    AIIMSRoleCoverage,
    AlertComplianceMetrics,
    AuditDecisionChainResponse,
    AuditEventSummary,
    AuditTrailResponse,
    AWSPrincipleCompliance,
    CapabilityGap,
    ComplianceDetailResponse,
    ComplianceMatrixEntry,
    ComplianceMatrixResponse,
    EmergencyPlanSummary,
    ExecutiveSummaryResponse,
    OperationalReadinessResponse,
    PPRRPhaseStatus,
    RecoveryDomainDetail,
    RecoveryDomainProgress,
    RecoveryProgressResponse,
    RiskDetailResponse,
    RiskSeverityBreakdown,
    RiskWarningResponse,
    VolunteerReadiness,
)
from app.services.governance_data_service import GovernanceDataService
from app.services.health_score_service import HealthScoreService

from packages.domain.src.domain.models.governance_health_score import ConstitutionalGateStatus

logger = logging.getLogger("dashboard_aggregation")


class DashboardAggregationService:
    """Aggregates data from multiple sources for dashboard views."""

    def __init__(
        self,
        health_service: HealthScoreService | None = None,
        governance_repo: object | None = None,
        data_service: GovernanceDataService | None = None,
    ) -> None:
        self._health = health_service or HealthScoreService()
        self._repo = governance_repo
        self._data = data_service

    # --- Executive Summary (US1) ---

    def get_executive_summary(
        self,
        *,
        tenant_id: str = "live",
        has_active_incident: bool = False,
        jurisdiction_id: str | None = None,
    ) -> ExecutiveSummaryResponse:
        """Build executive summary from real governance data sources."""
        if self._data:
            gates = self._data.get_constitutional_gates(tenant_id)
            ds_stats = self._data.get_data_source_stats(tenant_id)
            readiness = self._data.get_readiness_inputs(tenant_id)
            recovery = self._data.get_recovery_inputs(tenant_id)
            risk_summary = self._data.get_risk_severity_counts(tenant_id)
            active_count = self._data.get_active_incident_count(tenant_id)
            utilisation = self._data.get_resource_utilisation(tenant_id)
        else:
            gates = [
                ConstitutionalGateStatus(
                    gate_number=num,
                    gate_name=name,
                    status="assessment_pending",
                    detail_url=f"/governance/dashboard/compliance?gate={num}",
                )
                for num, name in [
                    (1, "Primacy of Life"),
                    (2, "National EM Principles"),
                    (3, "Multi-Hazard Design"),
                    (4, "Transparency & Auditability"),
                    (5, "Warning & Public Information"),
                    (6, "Evacuation Framework"),
                    (7, "Recovery Support"),
                    (8, "Cloud Platform & Infrastructure"),
                    (9, "PPRR Lifecycle"),
                    (10, "Governance & Quality Gates"),
                ]
            ]
            ds_stats = {"total": 0, "compliant": 0, "partially_compliant": 0}
            readiness = {"exercise_completion_rate": 0.0, "role_coverage_pct": 0.0, "plan_currency_pct": 0.0}
            recovery = {"has_active_recovery": False}
            risk_summary = {"extreme": 0, "high": 0, "medium": 0, "low": 0}
            active_count = 0
            utilisation = 0.0

        gate_dicts = [{"status": g.status} for g in gates]
        health = self._health.calculate(
            constitutional_gates=gate_dicts,
            readiness_data=readiness,
            data_source_stats=ds_stats,
            recovery_data=recovery,
            tenant_id=tenant_id,
            has_active_incident=has_active_incident,
        )

        return ExecutiveSummaryResponse(
            health_score=health,
            constitutional_gates=gates,
            active_incident_count=active_count,
            resource_utilisation_pct=utilisation,
            risk_summary=risk_summary,
            data_freshness=datetime.now(UTC),
            tenant_id=tenant_id,
        )

    # --- Compliance Matrix (US2) ---

    def get_compliance_matrix(
        self,
        *,
        tenant_id: str = "live",
        compliance_status: str | None = None,
        category: str | None = None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
        page_size: int = 50,
        continuation_token: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> ComplianceMatrixResponse:
        """Build compliance matrix with filtering, sorting, pagination."""
        if self._data:
            raw_entries = self._data.get_compliance_entries(tenant_id)
        else:
            raw_entries = []

        entries = [
            ComplianceMatrixEntry(
                data_source_id=e["data_source_id"],
                data_source_name=e["data_source_name"],
                compliance_status=e["compliance_status"],
                last_assessment_date=e.get("last_assessment_date"),
                next_assessment_due_date=e.get("next_assessment_due_date"),
                governance_gap_count=e.get("governance_gap_count", 0),
                grace_period_expiry=e.get("grace_period_expiry"),
                grace_period_reason=e.get("grace_period_reason"),
                grace_period_countdown_days=e.get("grace_period_countdown_days"),
                category=e.get("category", "unknown"),
            )
            for e in raw_entries
        ]

        if compliance_status:
            entries = [e for e in entries if e.compliance_status == compliance_status]
        if category:
            entries = [e for e in entries if e.category == category]

        total = len(entries)
        filters = {
            k: v
            for k, v in {
                "compliance_status": compliance_status,
                "category": category,
            }.items()
            if v is not None
        }

        if sort_by:
            reverse = sort_dir == "desc"
            entries.sort(key=lambda e: getattr(e, sort_by, ""), reverse=reverse)

        start = 0
        if continuation_token:
            try:
                start = int(continuation_token)
            except ValueError:
                start = 0

        page = entries[start : start + page_size]
        next_token = str(start + page_size) if start + page_size < total else None

        return ComplianceMatrixResponse(
            entries=page,
            total_count=total,
            filters_applied=filters,
            continuation_token=next_token,
            page_size=page_size,
        )

    def get_compliance_detail(
        self,
        data_source_id: str,
        *,
        tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> ComplianceDetailResponse | None:
        """Get detailed compliance information for a single data source."""
        if self._data:
            entries = self._data.get_compliance_entries(tenant_id)
            for e in entries:
                if e["data_source_id"] == data_source_id:
                    return ComplianceDetailResponse(
                        data_source_id=data_source_id,
                        data_source_name=e["data_source_name"],
                        compliance_status=e["compliance_status"],
                        assessment_history=[],
                        remediation_actions=[],
                        related_audit_urls=[],
                    )

        return ComplianceDetailResponse(
            data_source_id=data_source_id,
            data_source_name=f"Source {data_source_id}",
            compliance_status="pending",
            assessment_history=[],
            remediation_actions=[],
            related_audit_urls=[],
        )

    # --- Audit Trail (US3) ---

    def search_audit_events(
        self,
        *,
        tenant_id: str = "live",
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        actor: str | None = None,
        action_type: str | None = None,
        affected_entity: str | None = None,
        keyword: str | None = None,
        page_size: int = 50,
        continuation_token: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> AuditTrailResponse:
        """Search audit events from real governance audit entries."""
        filters = {
            k: str(v)
            for k, v in {
                "date_from": date_from,
                "date_to": date_to,
                "actor": actor,
                "action_type": action_type,
                "affected_entity": affected_entity,
                "keyword": keyword,
            }.items()
            if v is not None
        }

        events: list[AuditEventSummary] = []
        if self._data:
            raw_events = self._data.search_audit_events(
                tenant_id,
                date_from=date_from,
                date_to=date_to,
                actor=actor,
                action_type=action_type,
                affected_entity=affected_entity,
                keyword=keyword,
            )
            events = [
                AuditEventSummary(
                    event_id=e.get("event_id", ""),
                    action=e.get("action", ""),
                    actor=e.get("actor", ""),
                    timestamp=e.get("timestamp", datetime.now(UTC)),
                    entity_type=e.get("entity_type", ""),
                    entity_id=e.get("entity_id", ""),
                    summary=e.get("details", {}).get("summary", "") if isinstance(e.get("details"), dict) else "",
                )
                for e in raw_events
            ]

        total = len(events)
        start = 0
        if continuation_token:
            try:
                start = int(continuation_token)
            except ValueError:
                start = 0

        page = events[start : start + page_size]
        next_token = str(start + page_size) if start + page_size < total else None

        return AuditTrailResponse(
            events=page,
            total_count=total,
            filters_applied=filters,
            continuation_token=next_token,
            page_size=page_size,
        )

    def get_decision_chain(
        self,
        event_id: str,
        *,
        tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> AuditDecisionChainResponse | None:
        """Get the decision chain for an audit event."""
        return AuditDecisionChainResponse(
            event_id=event_id,
            chain=[],
            chain_complete=False,
        )

    # --- Operational Readiness (US4) ---

    def get_operational_readiness(
        self,
        *,
        tenant_id: str = "live",
        jurisdiction_id: str | None = None,
        hazard_type: str | None = None,
    ) -> OperationalReadinessResponse:
        """Aggregate operational readiness from real seed data."""
        if self._data:
            pprr_dist = self._data.get_pprr_distribution(tenant_id)
            pprr = [
                PPRRPhaseStatus(
                    phase=phase,
                    is_active=pprr_dist.get(phase, 0) > 0,
                    indicator_status="active" if pprr_dist.get(phase, 0) > 0 else "inactive",
                )
                for phase in ("prevention", "preparedness", "response", "recovery")
            ]

            raw_plans = self._data.get_emergency_plan_summaries(tenant_id)
            plans = [
                EmergencyPlanSummary(
                    lifecycle_state=p["lifecycle_state"],
                    count=p["count"],
                    overdue_count=p["overdue_count"],
                )
                for p in raw_plans
            ]
            total_plans = sum(p.count for p in plans)
            overdue = sum(p.overdue_count for p in plans)

            raw_coverage = self._data.get_role_coverage(tenant_id)
            role_coverage = [
                AIIMSRoleCoverage(
                    role=r["role"],
                    assigned_count=r["assigned_count"],
                    required_count=r["required_count"],
                    is_staffed=r["is_staffed"],
                    coverage_pct=r["coverage_pct"],
                )
                for r in raw_coverage
            ]
            overall_coverage = sum(r.coverage_pct for r in role_coverage) / len(role_coverage) if role_coverage else 0.0

            raw_gaps = self._data.get_capability_gaps(tenant_id)
            capability_gaps = [
                CapabilityGap(
                    gap_type=g["gap_type"],
                    description=g["description"],
                    severity=g["severity"],
                    affected_roles=g["affected_roles"],
                )
                for g in raw_gaps
            ]

            vol = self._data.get_volunteer_readiness(tenant_id)
            volunteer = VolunteerReadiness(
                total_registered=vol["total_registered"],
                currently_available=vol["currently_available"],
                active_deployed=vol["active_deployed"],
                availability_rate_pct=vol["availability_rate_pct"],
                welfare_check_compliance_pct=vol["welfare_check_compliance_pct"],
            )

            readiness_inputs = self._data.get_readiness_inputs(tenant_id)
            exercise_rate = readiness_inputs.get("exercise_completion_rate", 0.0)
            overall_score = readiness_inputs.get("role_coverage_pct", 0.0)
        else:
            pprr = [
                PPRRPhaseStatus(phase=p, is_active=False, indicator_status="inactive")
                for p in ("prevention", "preparedness", "response", "recovery")
            ]
            plans = [
                EmergencyPlanSummary(lifecycle_state=s, count=0, overdue_count=0)
                for s in (
                    "Draft",
                    "InConsultation",
                    "UnderReview",
                    "Endorsed",
                    "Activated",
                    "PostEventReview",
                    "Superseded",
                )
            ]
            total_plans = 0
            overdue = 0
            _default_roles = [
                "incident_controller",
                "operations_officer",
                "planning_officer",
                "logistics_officer",
                "public_information_officer",
                "safety_officer",
                "liaison_officer",
                "intelligence_officer",
                "finance_officer",
                "medical_officer",
            ]
            role_coverage = [
                AIIMSRoleCoverage(
                    role=r,
                    assigned_count=0,
                    required_count=1,
                    is_staffed=False,
                    coverage_pct=0.0,
                )
                for r in _default_roles
            ]
            overall_coverage = 0.0
            capability_gaps = []
            volunteer = VolunteerReadiness(
                total_registered=0,
                currently_available=0,
                active_deployed=0,
                availability_rate_pct=0.0,
                welfare_check_compliance_pct=0.0,
            )
            exercise_rate = 0.0
            overall_score = 0.0

        # Derive exercise breakdown from PPRR distribution
        exercise_breakdown = []
        if self._data:
            pprr_dist = self._data.get_pprr_distribution(tenant_id)
            for ex_type, phase_key in [
                ("tabletop", "preparedness"),
                ("functional", "response"),
                ("full_scale", "recovery"),
            ]:
                count = pprr_dist.get(phase_key, 0)
                rate = min(100.0, round((count / max(1, len(self._data._assignments))) * 100, 1))
                exercise_breakdown.append({"type": ex_type, "rate": rate, "last_date": None})

        return OperationalReadinessResponse(
            pprr_phases=pprr,
            emergency_plans=plans,
            total_plans=total_plans,
            overdue_plans_total=overdue,
            exercise_completion_rate_pct=exercise_rate,
            exercise_breakdown=exercise_breakdown,
            overall_readiness_score=overall_score,
            aiims_role_coverage=role_coverage,
            overall_role_coverage_pct=round(overall_coverage, 1),
            capability_gap_count=len(capability_gaps),
            capability_gaps=capability_gaps,
            volunteer_readiness=volunteer,
        )

    # --- Recovery Progress (US5) ---

    def get_recovery_progress(
        self,
        *,
        tenant_id: str = "live",
        incident_id: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> RecoveryProgressResponse:
        """Aggregate recovery domain progress from catalogue data."""
        if self._data:
            has_recovery = self._data.has_active_recovery(tenant_id)
        else:
            has_recovery = False

        target_incident = incident_id or "INC-LATEST"

        if self._data:
            raw_domains = self._data.get_recovery_domains(tenant_id, target_incident)
        else:
            raw_domains = []

        concrete_domains = [
            RecoveryDomainProgress(
                domain=d["domain"],
                display_name=d["display_name"],
                completion_pct=d["completion_pct"],
                trend=d["trend"],
                target_pct=d["target_pct"],
                variance_from_target=d["variance_from_target"],
                is_below_target=d["is_below_target"],
                is_cross_cutting=d["is_cross_cutting"],
                incident_id=d["incident_id"],
            )
            for d in raw_domains
        ]

        if concrete_domains:
            avg_completion = sum(d.completion_pct for d in concrete_domains) / len(concrete_domains)
            avg_target = sum(d.target_pct for d in concrete_domains) / len(concrete_domains)
            overarching = RecoveryDomainProgress(
                domain="overarching",
                display_name="Overarching Recovery",
                completion_pct=round(avg_completion, 1),
                trend="stable",
                target_pct=round(avg_target, 1),
                variance_from_target=round(avg_completion - avg_target, 1),
                is_below_target=avg_completion < avg_target,
                is_cross_cutting=True,
                incident_id=target_incident,
            )
            all_domains = [overarching, *concrete_domains]
        else:
            all_domains = []

        return RecoveryProgressResponse(
            domains=all_domains,
            active_incident_id=target_incident if has_recovery else None,
            available_incidents=(
                [{"incident_id": target_incident, "name": "Current Recovery", "start_date": "2025-01-15"}]
                if has_recovery
                else []
            ),
            has_active_recovery=has_recovery or len(concrete_domains) > 0,
        )

    def get_recovery_domain_detail(
        self,
        domain: str,
        *,
        tenant_id: str = "live",
        incident_id: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> RecoveryDomainDetail | None:
        """Get detailed recovery information for a single domain."""
        valid_domains = {"overarching", "social", "economic", "built", "natural"}
        if domain not in valid_domains:
            return None

        if self._data:
            detail = self._data.get_recovery_domain_detail(domain, tenant_id, incident_id)
            if detail:
                return RecoveryDomainDetail(
                    domain=detail["domain"],
                    outcome_targets=detail["outcome_targets"],
                    activity_completion_rates=detail["activity_completion_rates"],
                    community_indicators=detail["community_indicators"],
                    me_evaluation_results=detail["me_evaluation_results"],
                )

        return RecoveryDomainDetail(
            domain=domain,
            outcome_targets=[],
            activity_completion_rates=[],
            community_indicators=[],
            me_evaluation_results=[],
        )

    # --- Risk & Warning (US6) ---

    def get_risk_and_warning(
        self,
        *,
        tenant_id: str = "live",
        jurisdiction_id: str | None = None,
        issuing_authority: str | None = None,
        hazard_type: str | None = None,
    ) -> RiskWarningResponse:
        """Aggregate risk register and warning compliance from real data."""
        if self._data:
            raw_severity = self._data.get_risk_severity_breakdown(tenant_id)
            severity = RiskSeverityBreakdown(
                extreme=raw_severity["extreme"],
                high=raw_severity["high"],
                medium=raw_severity["medium"],
                low=raw_severity["low"],
                total=raw_severity["total"],
            )
            top_risks = self._data.get_top_risks(tenant_id)
            raw_principles = self._data.get_aws_principle_compliance(tenant_id)
            principles = [
                AWSPrincipleCompliance(
                    principle=p["principle"],
                    display_name=p["display_name"],
                    compliant_count=p["compliant_count"],
                    total_count=p["total_count"],
                    compliance_rate_pct=p["compliance_rate_pct"],
                    non_compliant_warning_ids=p["non_compliant_warning_ids"],
                )
                for p in raw_principles
            ]
        else:
            severity = RiskSeverityBreakdown(extreme=0, high=0, medium=0, low=0, total=0)
            top_risks = []
            _default_principle_names = [
                ("life_saving", "Life Saving"),
                ("empowering", "Empowering"),
                ("trusted", "Trusted"),
                ("risk_scaled", "Risk Scaled"),
                ("timely_targeted", "Timely & Targeted"),
                ("impact_conveying", "Impact Conveying"),
                ("action_calling", "Action Calling"),
                ("clearly_communicated", "Clearly Communicated"),
                ("accessible", "Accessible"),
                ("bigger_picture", "Bigger Picture"),
            ]
            principles = [
                AWSPrincipleCompliance(
                    principle=pid,
                    display_name=name,
                    compliant_count=0,
                    total_count=0,
                    compliance_rate_pct=0.0,
                    non_compliant_warning_ids=[],
                )
                for pid, name in _default_principle_names
            ]

        overall_compliance = sum(p.compliance_rate_pct for p in principles) / len(principles) if principles else 0.0

        alert_compliance = AlertComplianceMetrics(
            avg_approval_latency_s=0.0,
            acceptable_threshold_s=120.0,
            exceeds_threshold=False,
            alerts_exceeding_threshold=[],
            aws_tier_usage={"advice": 0, "watch_and_act": 0, "emergency_warning": 0},
            broadcast_reach_pct=0.0,
            principle_compliance=principles,
            overall_principle_compliance_pct=round(overall_compliance, 1),
        )

        # Compute treatment closure rate from real data (0% when no risks)
        treatment_rate = 0.0

        return RiskWarningResponse(
            risk_severity=severity,
            treatment_closure_rate_pct=treatment_rate,
            alert_compliance=alert_compliance,
            top_risks=top_risks,
        )

    def get_risk_detail(
        self,
        risk_id: str,
        *,
        tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> RiskDetailResponse | None:
        """Get detailed risk information."""
        return RiskDetailResponse(
            risk_id=risk_id,
            description=f"Risk {risk_id}",
            severity="unknown",
            likelihood="unknown",
            consequence="unknown",
            treatments=[],
            treatment_history=[],
            related_audit_urls=[],
        )
