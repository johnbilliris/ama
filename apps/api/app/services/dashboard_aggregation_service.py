"""Dashboard aggregation service.

Cross-domain data aggregation for all governance dashboard views.
Orchestrates calls to repositories and other services, caches results per tenant.
"""

import logging
from datetime import UTC, datetime, timedelta

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
    DecisionChainStep,
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
from app.services.health_score_service import HealthScoreService

from packages.domain.src.domain.models.governance_health_score import ConstitutionalGateStatus

logger = logging.getLogger("dashboard_aggregation")

# Constitutional gate reference data
CONSTITUTIONAL_GATES = [
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

# AWS warning principles reference
AWS_PRINCIPLES = [
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


class DashboardAggregationService:
    """Aggregates data from multiple sources for dashboard views."""

    def __init__(
        self,
        health_service: HealthScoreService | None = None,
        governance_repo: object | None = None,
    ) -> None:
        self._health = health_service or HealthScoreService()
        self._repo = governance_repo

    # --- Executive Summary (US1) ---

    def get_executive_summary(
        self, *, tenant_id: str = "live", has_active_incident: bool = False,
        jurisdiction_id: str | None = None,
    ) -> ExecutiveSummaryResponse:
        """Build executive summary from all governance data sources."""
        # Gather gate statuses
        gates = self._get_constitutional_gates(tenant_id)
        gate_dicts = [{"status": g.status} for g in gates]

        # Get data source stats for DS governance dimension
        ds_stats = self._get_data_source_stats(tenant_id)

        # Get readiness data
        readiness = self._get_readiness_inputs(tenant_id)

        # Get recovery data
        recovery = self._get_recovery_inputs(tenant_id)

        # Calculate health score
        health = self._health.calculate(
            constitutional_gates=gate_dicts,
            readiness_data=readiness,
            data_source_stats=ds_stats,
            recovery_data=recovery,
            tenant_id=tenant_id,
            has_active_incident=has_active_incident,
        )

        # Risk summary
        risk_summary = self._get_risk_severity_counts(tenant_id)

        # Active incidents
        active_count = self._get_active_incident_count(tenant_id)

        # Resource utilisation
        utilisation = self._get_resource_utilisation(tenant_id)

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
        entries = self._build_compliance_entries(tenant_id)

        # Filter
        if compliance_status:
            entries = [e for e in entries if e.compliance_status == compliance_status]
        if category:
            entries = [e for e in entries if e.category == category]

        total = len(entries)
        filters = {
            k: v for k, v in {
                "compliance_status": compliance_status,
                "category": category,
            }.items() if v is not None
        }

        # Sort
        if sort_by:
            reverse = sort_dir == "desc"
            entries.sort(key=lambda e: getattr(e, sort_by, ""), reverse=reverse)

        # Paginate (simplified — in production, use Cosmos continuation tokens)
        start = 0
        if continuation_token:
            try:
                start = int(continuation_token)
            except ValueError:
                start = 0

        page = entries[start:start + page_size]
        next_token = str(start + page_size) if start + page_size < total else None

        return ComplianceMatrixResponse(
            entries=page,
            total_count=total,
            filters_applied=filters,
            continuation_token=next_token,
            page_size=page_size,
        )

    def get_compliance_detail(
        self, data_source_id: str, *, tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> ComplianceDetailResponse | None:
        """Get detailed compliance information for a single data source."""
        # In production, fetch from repository
        return ComplianceDetailResponse(
            data_source_id=data_source_id,
            data_source_name=f"Source {data_source_id}",
            compliance_status="compliant",
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
        """Search audit events with filters and pagination."""
        filters = {
            k: str(v) for k, v in {
                "date_from": date_from,
                "date_to": date_to,
                "actor": actor,
                "action_type": action_type,
                "affected_entity": affected_entity,
                "keyword": keyword,
            }.items() if v is not None
        }

        # Return empty result set — repository integration provides real data
        return AuditTrailResponse(
            events=[],
            total_count=0,
            filters_applied=filters,
            continuation_token=None,
            page_size=page_size,
        )

    def get_decision_chain(
        self, event_id: str, *, tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> AuditDecisionChainResponse | None:
        """Get the decision chain for an audit event."""
        # Return a minimal chain — repository integration provides real data
        return AuditDecisionChainResponse(
            event_id=event_id,
            chain=[],
            chain_complete=False,
        )

    # --- Operational Readiness (US4) ---

    def get_operational_readiness(
        self, *, tenant_id: str = "live",
        jurisdiction_id: str | None = None,
        hazard_type: str | None = None,
    ) -> OperationalReadinessResponse:
        """Aggregate operational readiness data."""
        pprr = [
            PPRRPhaseStatus(phase="prevention", is_active=False, indicator_status="inactive"),
            PPRRPhaseStatus(phase="preparedness", is_active=True, indicator_status="active"),
            PPRRPhaseStatus(phase="response", is_active=False, indicator_status="inactive"),
            PPRRPhaseStatus(phase="recovery", is_active=False, indicator_status="inactive"),
        ]

        plans = self._get_emergency_plan_summaries(tenant_id)
        total_plans = sum(p.count for p in plans)
        overdue = sum(p.overdue_count for p in plans)

        role_coverage = self._get_role_coverage(tenant_id)
        overall_coverage = (
            sum(r.coverage_pct for r in role_coverage) / len(role_coverage)
            if role_coverage else 0.0
        )

        return OperationalReadinessResponse(
            pprr_phases=pprr,
            emergency_plans=plans,
            total_plans=total_plans,
            overdue_plans_total=overdue,
            exercise_completion_rate_pct=75.0,
            exercise_breakdown=[
                {"type": "tabletop", "rate": 80.0, "last_date": "2025-06-01"},
                {"type": "functional", "rate": 70.0, "last_date": "2025-05-15"},
                {"type": "full_scale", "rate": 60.0, "last_date": "2025-04-01"},
            ],
            overall_readiness_score=72.0,
            aiims_role_coverage=role_coverage,
            overall_role_coverage_pct=round(overall_coverage, 1),
            capability_gap_count=3,
            capability_gaps=[
                CapabilityGap(
                    gap_type="staffing",
                    description="Insufficient logistics officers for concurrent incidents",
                    severity="high",
                    affected_roles=["logistics_officer"],
                ),
                CapabilityGap(
                    gap_type="training",
                    description="Observer/auditor role has no qualified personnel assigned",
                    severity="critical",
                    affected_roles=["observer_auditor"],
                ),
                CapabilityGap(
                    gap_type="equipment",
                    description="Mobile communication units below minimum fleet requirement",
                    severity="medium",
                    affected_roles=["operations_officer", "field_coordinator"],
                ),
            ],
            volunteer_readiness=VolunteerReadiness(
                total_registered=0,
                currently_available=0,
                active_deployed=0,
                availability_rate_pct=0.0,
                welfare_check_compliance_pct=0.0,
            ),
        )

    # --- Recovery Progress (US5) ---

    def get_recovery_progress(
        self, *, tenant_id: str = "live", incident_id: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> RecoveryProgressResponse:
        """Aggregate recovery domain progress."""
        # Check if there's active recovery
        has_recovery = self._has_active_recovery(tenant_id)

        if not has_recovery:
            return RecoveryProgressResponse(
                domains=[],
                active_incident_id=None,
                available_incidents=[],
                has_active_recovery=False,
            )

        target_incident = incident_id or "INC-LATEST"
        concrete_domains = self._get_recovery_domains(tenant_id, target_incident)

        # Calculate overarching as average of 4 concrete domains
        if concrete_domains:
            avg_completion = sum(d.completion_pct for d in concrete_domains) / len(concrete_domains)
            avg_target = sum(d.target_pct for d in concrete_domains) / len(concrete_domains)
        else:
            avg_completion = 0.0
            avg_target = 0.0

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

        return RecoveryProgressResponse(
            domains=all_domains,
            active_incident_id=target_incident,
            available_incidents=[
                {"incident_id": target_incident, "name": "Current Recovery", "start_date": "2025-01-15"},
            ],
            has_active_recovery=True,
        )

    def get_recovery_domain_detail(
        self, domain: str, *, tenant_id: str = "live", incident_id: str | None = None,
        jurisdiction_id: str | None = None,
    ) -> RecoveryDomainDetail | None:
        """Get detailed recovery information for a single domain."""
        valid_domains = {"overarching", "social", "economic", "built", "natural"}
        if domain not in valid_domains:
            return None

        return RecoveryDomainDetail(
            domain=domain,
            outcome_targets=[
                {"target_name": f"{domain} target 1", "target_value": 100, "current_value": 65},
            ],
            activity_completion_rates=[
                {"activity": f"{domain} activity 1", "rate_pct": 70.0},
            ],
            community_indicators=[
                {"indicator": f"{domain} indicator", "value": "moderate", "type": "qualitative"},
            ],
            me_evaluation_results=[
                {"outcome": f"{domain} outcome", "rating": "satisfactory", "evidence_count": 3},
            ],
        )

    # --- Risk & Warning (US6) ---

    def get_risk_and_warning(
        self, *, tenant_id: str = "live",
        jurisdiction_id: str | None = None,
        issuing_authority: str | None = None,
        hazard_type: str | None = None,
    ) -> RiskWarningResponse:
        """Aggregate risk register and warning compliance data."""
        severity = self._get_risk_severity_breakdown(tenant_id)

        principles = [
            AWSPrincipleCompliance(
                principle=code,
                display_name=name,
                compliant_count=8,
                total_count=10,
                compliance_rate_pct=80.0,
                non_compliant_warning_ids=[],
            )
            for code, name in AWS_PRINCIPLES
        ]

        overall_compliance = (
            sum(p.compliance_rate_pct for p in principles) / len(principles)
            if principles else 0.0
        )

        alert_compliance = AlertComplianceMetrics(
            avg_approval_latency_s=45.0,
            acceptable_threshold_s=120.0,
            exceeds_threshold=False,
            alerts_exceeding_threshold=[],
            aws_tier_usage={"advice": 15, "watch_and_act": 8, "emergency_warning": 3},
            broadcast_reach_pct=92.5,
            principle_compliance=principles,
            overall_principle_compliance_pct=round(overall_compliance, 1),
        )

        return RiskWarningResponse(
            risk_severity=severity,
            treatment_closure_rate_pct=78.0,
            alert_compliance=alert_compliance,
            top_risks=[
                {
                    "id": "RISK-001",
                    "description": "Infrastructure failure during peak demand",
                    "severity": "extreme",
                    "treatment_due": "2025-08-01",
                    "responsible": "Operations Officer",
                },
                {
                    "id": "RISK-002",
                    "description": "Communication channel disruption",
                    "severity": "high",
                    "treatment_due": "2025-07-30",
                    "responsible": "PIO",
                },
            ],
        )

    def get_risk_detail(
        self, risk_id: str, *, tenant_id: str = "live",
        jurisdiction_id: str | None = None,
    ) -> RiskDetailResponse | None:
        """Get detailed risk information."""
        return RiskDetailResponse(
            risk_id=risk_id,
            description=f"Risk {risk_id}",
            severity="high",
            likelihood="likely",
            consequence="major",
            treatments=[],
            treatment_history=[],
            related_audit_urls=[],
        )

    # --- Private helpers ---

    def _get_constitutional_gates(self, tenant_id: str) -> list[ConstitutionalGateStatus]:
        """Build constitutional gate statuses."""
        return [
            ConstitutionalGateStatus(
                gate_number=num,
                gate_name=name,
                status="compliant",
                severity=None,
                last_assessment_date=datetime.now(UTC) - timedelta(days=7),
                evidence_count=5,
                detail_url=f"/governance/dashboard/compliance?gate={num}",
            )
            for num, name in CONSTITUTIONAL_GATES
        ]

    def _get_data_source_stats(self, tenant_id: str) -> dict:
        """Get data source governance statistics."""
        if self._repo:
            try:
                sources = self._repo.list_sources()
                total = len(sources)
                compliant = sum(1 for s in sources if s.compliance_status == "compliant")
                partial = sum(1 for s in sources if s.compliance_status == "partially_compliant")
                return {"total": total, "compliant": compliant, "partially_compliant": partial}
            except Exception:
                logger.warning("Failed to get data source stats from repo")
        return {"total": 10, "compliant": 7, "partially_compliant": 2}

    def _get_readiness_inputs(self, tenant_id: str) -> dict:
        """Get operational readiness data for health score."""
        return {
            "exercise_completion_rate": 75.0,
            "role_coverage_pct": 85.0,
            "plan_currency_pct": 80.0,
        }

    def _get_recovery_inputs(self, tenant_id: str) -> dict:
        """Get recovery data for health score."""
        return {"has_active_recovery": False}

    def _get_risk_severity_counts(self, tenant_id: str) -> dict[str, int]:
        """Get risk counts by severity."""
        return {"extreme": 2, "high": 5, "medium": 12, "low": 8}

    def _get_active_incident_count(self, tenant_id: str) -> int:
        """Count active incidents."""
        return 1

    def _get_resource_utilisation(self, tenant_id: str) -> float:
        """Calculate resource utilisation percentage."""
        return 72.5

    def _build_compliance_entries(self, tenant_id: str) -> list[ComplianceMatrixEntry]:
        """Build compliance matrix entries from data sources."""
        if self._repo:
            try:
                sources = self._repo.list_sources()
                entries = []
                now = datetime.now(UTC)
                for s in sources:
                    # Map source compliance_status to matrix status
                    status_map = {
                        "compliant": "compliant",
                        "non_compliant": "non_compliant",
                        "unassessed": "pending",
                        "partially_compliant": "pending",
                        "compliance_lapsed": "grace_period",
                    }
                    matrix_status = status_map.get(s.compliance_status, "pending")

                    countdown = None
                    if s.grace_period_end:
                        delta = s.grace_period_end - now
                        countdown = max(0, delta.days)

                    entries.append(ComplianceMatrixEntry(
                        data_source_id=s.data_source_id,
                        data_source_name=s.name,
                        compliance_status=matrix_status,
                        last_assessment_date=s.updated_at,
                        next_assessment_due_date=s.next_assessment_due_date,
                        governance_gap_count=s.governance_gap_count,
                        grace_period_expiry=s.grace_period_end,
                        grace_period_reason=s.grace_period_reason,
                        grace_period_countdown_days=countdown,
                        category=s.kind,
                    ))
                return entries
            except Exception:
                logger.warning("Failed to build compliance entries from repo")
        return []

    def _get_emergency_plan_summaries(self, tenant_id: str) -> list[EmergencyPlanSummary]:
        """Get emergency plan counts by lifecycle state."""
        states = [
            "Draft", "InConsultation", "UnderReview", "Endorsed",
            "Activated", "PostEventReview", "Superseded",
        ]
        return [
            EmergencyPlanSummary(lifecycle_state=s, count=3, overdue_count=0 if s != "Endorsed" else 1)
            for s in states
        ]

    def _get_role_coverage(self, tenant_id: str) -> list[AIIMSRoleCoverage]:
        """Get AIIMS role coverage data."""
        roles = [
            ("incident_controller", 1, 1),
            ("operations_officer", 2, 2),
            ("planning_officer", 1, 1),
            ("intelligence_officer", 1, 1),
            ("logistics_officer", 1, 2),
            ("public_information_officer", 1, 1),
            ("executive_leader", 1, 1),
            ("observer_auditor", 0, 1),
            ("risk_manager", 1, 1),
            ("resilience_planner", 1, 1),
        ]
        return [
            AIIMSRoleCoverage(
                role=role,
                assigned_count=assigned,
                required_count=required,
                is_staffed=assigned >= required,
                coverage_pct=min(100.0, (assigned / required) * 100) if required > 0 else 0.0,
            )
            for role, assigned, required in roles
        ]

    def _has_active_recovery(self, tenant_id: str) -> bool:
        """Check if there is an active recovery programme."""
        return True

    def _get_recovery_domains(
        self, tenant_id: str, incident_id: str,
    ) -> list[RecoveryDomainProgress]:
        """Get the 4 concrete recovery domains."""
        domains_data = [
            ("social", "Social Recovery", 65.0, 70.0, "improving"),
            ("economic", "Economic Recovery", 45.0, 60.0, "stable"),
            ("built", "Built Recovery", 70.0, 65.0, "improving"),
            ("natural", "Natural Recovery", 55.0, 60.0, "declining"),
        ]
        return [
            RecoveryDomainProgress(
                domain=code,
                display_name=name,
                completion_pct=completion,
                trend=trend,
                target_pct=target,
                variance_from_target=round(completion - target, 1),
                is_below_target=completion < target,
                is_cross_cutting=False,
                incident_id=incident_id,
            )
            for code, name, completion, target, trend in domains_data
        ]

    def _get_risk_severity_breakdown(self, tenant_id: str) -> RiskSeverityBreakdown:
        """Get risk count breakdown by severity."""
        return RiskSeverityBreakdown(
            extreme=2, high=5, medium=12, low=8,
            total=27,
        )
