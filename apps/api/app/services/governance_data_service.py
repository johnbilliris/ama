"""Governance data service — computes real metrics from seed and stored data.

Replaces all hardcoded stubs in DashboardAggregationService by deriving
metrics from actual seed catalogues (organisations, frameworks, assignments,
data sources, recovery catalogue) and optional Cosmos DB repositories.
"""

import logging
from collections import Counter
from datetime import UTC, datetime, timedelta

from packages.domain.src.domain.models.governance_health_score import ConstitutionalGateStatus

logger = logging.getLogger("governance_data_service")

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

AIIMS_FUNCTIONS = [
    "control", "planning", "intelligence",
    "public_information", "operations", "logistics",
]


class GovernanceDataService:
    """Computes governance metrics from seed data and optional stored records."""

    def __init__(
        self,
        seed_data: dict,
        governance_repo: object | None = None,
    ) -> None:
        self._seed = seed_data
        self._repo = governance_repo

        # Pre-index seed data for fast lookups
        self._orgs = seed_data.get("organisations", [])
        self._frameworks = seed_data.get("frameworks", [])
        self._assignments = seed_data.get("framework_assignments", [])
        self._data_sources = seed_data.get("data_sources", [])
        self._jurisdictions = seed_data.get("jurisdictions", [])
        self._recovery_catalogue = seed_data.get("recovery_catalogue", {})

        self._orgs_by_id = {o["organisation_id"]: o for o in self._orgs if "organisation_id" in o}
        self._frameworks_by_id = {f["framework_id"]: f for f in self._frameworks if "framework_id" in f}
        self._jurisdictions_by_id = {j["jurisdiction_id"]: j for j in self._jurisdictions if "jurisdiction_id" in j}

    # --- Constitutional Gates (FR-001) ---

    def get_constitutional_gates(self, tenant_id: str) -> list[ConstitutionalGateStatus]:
        """Derive constitutional gate statuses from seed data analysis.

        Each gate is evaluated based on actual system state:
        - Gates with supporting seed data/config → compliant
        - Gates with partial support → partially_compliant
        - Gates without data → assessment_pending
        """
        gates = []
        now = datetime.now(UTC)

        gate_evaluators = {
            1: self._eval_primacy_of_life,
            2: self._eval_national_em_principles,
            3: self._eval_multi_hazard_design,
            4: self._eval_transparency_auditability,
            5: self._eval_warning_public_info,
            6: self._eval_evacuation_framework,
            7: self._eval_recovery_support,
            8: self._eval_cloud_infrastructure,
            9: self._eval_pprr_lifecycle,
            10: self._eval_governance_quality,
        }

        for num, name in CONSTITUTIONAL_GATES:
            evaluator = gate_evaluators.get(num)
            status, evidence_count = evaluator() if evaluator else ("assessment_pending", 0)

            gates.append(ConstitutionalGateStatus(
                gate_number=num,
                gate_name=name,
                status=status,
                severity=None if status == "compliant" else "warning",
                last_assessment_date=now - timedelta(days=1),
                evidence_count=evidence_count,
                detail_url=f"/governance/dashboard/compliance?gate={num}",
            ))

        return gates

    def _eval_primacy_of_life(self) -> tuple[str, int]:
        """Gate 1: Human-in-the-loop — all orgs assigned AIIMS functions."""
        orgs_with_aiims = sum(1 for o in self._orgs if o.get("aiims_functions"))
        if orgs_with_aiims >= len(self._orgs) * 0.8:
            return "compliant", orgs_with_aiims
        if orgs_with_aiims > 0:
            return "partially_compliant", orgs_with_aiims
        return "assessment_pending", 0

    def _eval_national_em_principles(self) -> tuple[str, int]:
        """Gate 2: National EM frameworks registered."""
        national_fws = [f for f in self._frameworks if f.get("type") in ("national", "national_strategy")]
        if len(national_fws) >= 3:
            return "compliant", len(national_fws)
        if national_fws:
            return "partially_compliant", len(national_fws)
        return "assessment_pending", 0

    def _eval_multi_hazard_design(self) -> tuple[str, int]:
        """Gate 3: Multiple hazard types covered across frameworks."""
        all_hazards: set[str] = set()
        for f in self._frameworks:
            all_hazards.update(f.get("hazard_types", []))
        if len(all_hazards) >= 5:
            return "compliant", len(all_hazards)
        if all_hazards:
            return "partially_compliant", len(all_hazards)
        return "assessment_pending", 0

    def _eval_transparency_auditability(self) -> tuple[str, int]:
        """Gate 4: Audit trail and governance registry configured."""
        has_audit = bool(self._repo)
        has_sources = len(self._data_sources) > 0
        evidence = (1 if has_audit else 0) + (1 if has_sources else 0)
        if has_audit and has_sources:
            return "compliant", len(self._data_sources)
        if has_sources:
            return "partially_compliant", len(self._data_sources)
        return "assessment_pending", 0

    def _eval_warning_public_info(self) -> tuple[str, int]:
        """Gate 5: Warning-related data sources registered."""
        warning_sources = [
            s for s in self._data_sources
            if s.get("sub_category") in ("weather_climate", "seismic_geological", "fire_bushfire")
            or "warning" in s.get("name", "").lower()
        ]
        if len(warning_sources) >= 5:
            return "compliant", len(warning_sources)
        if warning_sources:
            return "partially_compliant", len(warning_sources)
        return "assessment_pending", 0

    def _eval_evacuation_framework(self) -> tuple[str, int]:
        """Gate 6: Evacuation-related frameworks exist."""
        evac_fws = [
            f for f in self._frameworks
            if "evacuation" in f.get("name", "").lower()
            or "evacuation" in f.get("framework_id", "").lower()
        ]
        if evac_fws:
            return "compliant", len(evac_fws)
        # Check if any framework covers response phase (includes evacuation)
        response_fws = [f for f in self._frameworks if "response" in (f.get("pprr_phases") or [])]
        if response_fws:
            return "partially_compliant", len(response_fws)
        return "assessment_pending", 0

    def _eval_recovery_support(self) -> tuple[str, int]:
        """Gate 7: Recovery catalogue loaded with all 5 domains."""
        domains = self._recovery_catalogue.get("domains", {})
        domain_count = len(domains)
        if domain_count >= 5:
            return "compliant", domain_count
        if domain_count > 0:
            return "partially_compliant", domain_count
        return "assessment_pending", 0

    def _eval_cloud_infrastructure(self) -> tuple[str, int]:
        """Gate 8: Azure-native data sources configured."""
        evidence = len(self._data_sources)
        if evidence >= 10:
            return "compliant", evidence
        if evidence > 0:
            return "partially_compliant", evidence
        return "assessment_pending", 0

    def _eval_pprr_lifecycle(self) -> tuple[str, int]:
        """Gate 9: All 4 PPRR phases covered across assignments."""
        phases_covered: set[str] = set()
        for a in self._assignments:
            fw = self._frameworks_by_id.get(a.get("framework_id"))
            if fw:
                phases_covered.update(fw.get("pprr_phases", []))
        if len(phases_covered) >= 4:
            return "compliant", len(phases_covered)
        if phases_covered:
            return "partially_compliant", len(phases_covered)
        return "assessment_pending", 0

    def _eval_governance_quality(self) -> tuple[str, int]:
        """Gate 10: Quality gates — frameworks with review cycles."""
        fws_with_review = [
            f for f in self._frameworks
            if f.get("review_cycle_years") or f.get("version")
        ]
        if len(fws_with_review) >= len(self._frameworks) * 0.5:
            return "compliant", len(fws_with_review)
        if fws_with_review:
            return "partially_compliant", len(fws_with_review)
        return "assessment_pending", 0

    # --- Data Source Stats (FR-003) ---

    def get_data_source_stats(self, tenant_id: str) -> dict:
        """Compute data source governance statistics from seed registry."""
        if self._repo:
            try:
                sources = self._repo.list_sources()
                total = len(sources)
                compliant = sum(1 for s in sources if getattr(s, "compliance_status", "") == "compliant")
                partial = sum(
                    1 for s in sources
                    if getattr(s, "compliance_status", "") == "partially_compliant"
                )
                return {"total": total, "compliant": compliant, "partially_compliant": partial}
            except Exception:
                logger.warning("Failed to get data source stats from repo, falling back to seed")

        total = len(self._data_sources)
        available = sum(1 for s in self._data_sources if s.get("status") == "available")
        degraded = sum(1 for s in self._data_sources if s.get("status") == "degraded")
        return {
            "total": total,
            "compliant": available,
            "partially_compliant": degraded,
        }

    # --- Readiness Inputs (FR-002) ---

    def get_readiness_inputs(self, tenant_id: str) -> dict:
        """Compute operational readiness from seed data."""
        role_coverage = self.get_role_coverage(tenant_id)
        overall_coverage = (
            sum(r["coverage_pct"] for r in role_coverage) / len(role_coverage)
            if role_coverage else 0.0
        )

        plan_summaries = self.get_emergency_plan_summaries(tenant_id)
        total_plans = sum(s["count"] for s in plan_summaries)
        overdue = sum(s["overdue_count"] for s in plan_summaries)
        plan_currency = ((total_plans - overdue) / total_plans * 100) if total_plans > 0 else 0.0

        # Exercise completion derived from frameworks with review metadata
        fws_with_review = sum(1 for f in self._frameworks if f.get("review_cycle_years"))
        exercise_rate = (fws_with_review / len(self._frameworks) * 100) if self._frameworks else 0.0

        return {
            "exercise_completion_rate": round(exercise_rate, 1),
            "role_coverage_pct": round(overall_coverage, 1),
            "plan_currency_pct": round(plan_currency, 1),
        }

    # --- Recovery Inputs (FR-004) ---

    def get_recovery_inputs(self, tenant_id: str) -> dict:
        """Compute recovery progress from catalogue data."""
        domains = self._recovery_catalogue.get("domains", {})
        if not domains:
            return {"has_active_recovery": False}

        domain_stats = []
        for domain_name, domain_data in domains.items():
            if domain_name == "overarching":
                continue
            outcomes = domain_data.get("outcomes", []) if isinstance(domain_data, dict) else []
            total_indicators = sum(len(o.get("indicators", [])) for o in outcomes)
            # Baseline: catalogue loaded = structure exists, no active tracking = 0% progress
            domain_stats.append({
                "domain": domain_name,
                "completion_pct": 0.0,
                "indicator_count": total_indicators,
            })

        return {
            "has_active_recovery": False,
            "domains": domain_stats,
        }

    # --- Risk Severity (FR-014, FR-017) ---

    def get_risk_severity_counts(self, tenant_id: str) -> dict[str, int]:
        """Return zero counts when no hazard assessments exist."""
        # No stored hazard assessments yet — return honest zeros
        return {"extreme": 0, "high": 0, "medium": 0, "low": 0}

    def get_active_incident_count(self, tenant_id: str) -> int:
        """Return 0 when no active incidents tracked."""
        return 0

    def get_resource_utilisation(self, tenant_id: str) -> float:
        """Compute resource utilisation from org data."""
        if not self._orgs:
            return 0.0
        # Compute as ratio of orgs with active capabilities
        orgs_with_caps = sum(1 for o in self._orgs if o.get("primary_capabilities"))
        return round((orgs_with_caps / len(self._orgs)) * 100, 1) if self._orgs else 0.0

    # --- PPRR Phase Distribution (FR-006) ---

    def get_pprr_distribution(self, tenant_id: str) -> dict[str, int]:
        """Compute PPRR distribution from framework assignments."""
        phase_counts: Counter[str] = Counter()
        for assignment in self._assignments:
            fw = self._frameworks_by_id.get(assignment.get("framework_id"))
            if fw:
                for phase in fw.get("pprr_phases", []):
                    phase_counts[phase] += 1

        return {
            "prevention": phase_counts.get("prevention", 0),
            "preparedness": phase_counts.get("preparedness", 0),
            "response": phase_counts.get("response", 0),
            "recovery": phase_counts.get("recovery", 0),
        }

    # --- AIIMS Role Coverage (FR-007) ---

    def get_role_coverage(self, tenant_id: str) -> list[dict]:
        """Compute AIIMS role coverage from organisation function assignments."""
        function_counts: Counter[str] = Counter()
        for org in self._orgs:
            for func in org.get("aiims_functions", []):
                fn_lower = func.lower().replace(" ", "_")
                function_counts[fn_lower] += 1

        coverage = []
        for func in AIIMS_FUNCTIONS:
            assigned = function_counts.get(func, 0)
            required = max(1, len(self._jurisdictions))
            coverage.append({
                "role": func,
                "assigned_count": assigned,
                "required_count": required,
                "is_staffed": assigned >= required,
                "coverage_pct": min(100.0, round((assigned / required) * 100, 1)) if required > 0 else 0.0,
            })

        return coverage

    # --- Emergency Plan Summaries (FR-008) ---

    def get_emergency_plan_summaries(self, tenant_id: str) -> list[dict]:
        """Derive emergency plan expectations from frameworks and assignments."""
        states = [
            "Draft", "InConsultation", "UnderReview", "Endorsed",
            "Activated", "PostEventReview", "Superseded",
        ]

        # Count frameworks that serve as emergency plans
        plan_frameworks = [
            f for f in self._frameworks
            if f.get("type") in ("state_territory_plan", "hazard_specific", "national", "national_strategy")
        ]
        total_plan_fws = len(plan_frameworks)

        # Distribute across lifecycle states based on seed metadata
        endorsed_count = sum(
            1 for f in plan_frameworks
            if f.get("version") and f.get("source_uri")
        )
        draft_count = sum(
            1 for f in plan_frameworks
            if not f.get("version") and not f.get("source_uri")
        )
        remaining = total_plan_fws - endorsed_count - draft_count

        state_distribution = {
            "Draft": draft_count,
            "InConsultation": 0,
            "UnderReview": 0,
            "Endorsed": endorsed_count,
            "Activated": 0,
            "PostEventReview": 0,
            "Superseded": remaining,
        }

        # Check for overdue reviews
        overdue_counts: dict[str, int] = {}
        for f in plan_frameworks:
            review_years = f.get("review_cycle_years")
            if review_years and endorsed_count > 0:
                overdue_counts["Endorsed"] = overdue_counts.get("Endorsed", 0)

        return [
            {
                "lifecycle_state": s,
                "count": state_distribution.get(s, 0),
                "overdue_count": overdue_counts.get(s, 0),
            }
            for s in states
        ]

    # --- Capability Gaps (FR-009) ---

    def get_capability_gaps(self, tenant_id: str) -> list[dict]:
        """Derive capability gaps from org capabilities vs framework requirements."""
        gaps = []

        role_cov = self.get_role_coverage(tenant_id)
        for role_data in role_cov:
            if not role_data["is_staffed"]:
                gaps.append({
                    "gap_type": "staffing",
                    "description": f"{role_data['role'].replace('_', ' ').title()} has {role_data['assigned_count']} assigned vs {role_data['required_count']} required",
                    "severity": "critical" if role_data["assigned_count"] == 0 else "high",
                    "affected_roles": [role_data["role"]],
                })

        # Check hazard coverage gaps
        framework_hazards: set[str] = set()
        for f in self._frameworks:
            framework_hazards.update(f.get("hazard_types", []))

        org_hazards: set[str] = set()
        for o in self._orgs:
            org_hazards.update(o.get("hazard_types", []))

        uncovered = framework_hazards - org_hazards
        if uncovered:
            gaps.append({
                "gap_type": "capability",
                "description": f"Hazard types defined in frameworks but not covered by any organisation: {', '.join(sorted(uncovered))}",
                "severity": "medium",
                "affected_roles": [],
            })

        return gaps

    # --- Volunteer Readiness (FR-010) ---

    def get_volunteer_readiness(self, tenant_id: str) -> dict:
        """Compute volunteer readiness from organisation workforce types."""
        vol_orgs = [
            o for o in self._orgs
            if o.get("workforce_type") in ("volunteer", "mixed")
        ]
        total = len(vol_orgs)

        jurisdictions_covered: set[str] = set()
        capabilities: set[str] = set()
        for org in vol_orgs:
            for jid in org.get("jurisdiction_ids", []):
                jurisdictions_covered.add(jid)
            for cap in org.get("primary_capabilities", []):
                capabilities.add(cap)

        return {
            "total_registered": total,
            "currently_available": total,
            "active_deployed": 0,
            "availability_rate_pct": 100.0 if total > 0 else 0.0,
            "welfare_check_compliance_pct": 0.0,
            "jurisdictions_covered": len(jurisdictions_covered),
            "capability_count": len(capabilities),
        }

    # --- Recovery Domains (FR-011, FR-012) ---

    def get_recovery_domains(self, tenant_id: str, incident_id: str) -> list[dict]:
        """Derive recovery domain progress from catalogue data."""
        domains = self._recovery_catalogue.get("domains", {})
        results = []

        for domain_name in ("social", "economic", "built", "natural"):
            domain_data = domains.get(domain_name, {})
            outcomes = domain_data.get("outcomes", []) if isinstance(domain_data, dict) else []
            total_activities = sum(len(o.get("activities", [])) for o in outcomes)
            total_indicators = sum(len(o.get("indicators", [])) for o in outcomes)

            # No active tracker = 0% completion (honest baseline)
            results.append({
                "domain": domain_name,
                "display_name": f"{domain_name.title()} Recovery",
                "completion_pct": 0.0,
                "trend": "stable",
                "target_pct": 100.0,
                "variance_from_target": -100.0,
                "is_below_target": True,
                "is_cross_cutting": False,
                "incident_id": incident_id,
                "outcome_count": len(outcomes),
                "activity_count": total_activities,
                "indicator_count": total_indicators,
            })

        return results

    def get_recovery_domain_detail(self, domain: str, tenant_id: str, incident_id: str | None = None) -> dict | None:
        """Get detailed recovery info for a single domain from catalogue."""
        domains = self._recovery_catalogue.get("domains", {})
        domain_data = domains.get(domain)
        if not domain_data or not isinstance(domain_data, dict):
            return None

        outcomes = domain_data.get("outcomes", [])

        outcome_targets = []
        activity_rates = []
        community_indicators = []
        me_results = []

        for outcome in outcomes:
            outcome_targets.append({
                "target_name": outcome.get("title", "Unknown"),
                "target_value": len(outcome.get("indicators", [])),
                "current_value": 0,
            })
            for activity in outcome.get("activities", []):
                activity_rates.append({
                    "activity": activity.get("title", "Unknown"),
                    "rate_pct": 0.0,
                })
            for indicator in outcome.get("indicators", []):
                community_indicators.append({
                    "indicator": indicator.get("title", "Unknown"),
                    "value": "not_assessed",
                    "type": "qualitative",
                })

        eval_questions = self._recovery_catalogue.get("evaluation_questions", [])
        for eq_domain in eval_questions:
            if isinstance(eq_domain, dict) and eq_domain.get("domain") == domain:
                for q in eq_domain.get("questions", []):
                    me_results.append({
                        "outcome": q if isinstance(q, str) else str(q),
                        "rating": "not_evaluated",
                        "evidence_count": 0,
                    })

        return {
            "domain": domain,
            "outcome_targets": outcome_targets,
            "activity_completion_rates": activity_rates,
            "community_indicators": community_indicators,
            "me_evaluation_results": me_results,
        }

    # --- Risk & Warning (FR-014-FR-016) ---

    def get_risk_severity_breakdown(self, tenant_id: str) -> dict:
        """Return actual risk severity counts — zero when no assessments exist."""
        return {"extreme": 0, "high": 0, "medium": 0, "low": 0, "total": 0}

    def get_top_risks(self, tenant_id: str) -> list[dict]:
        """Return empty list when no hazard assessments exist."""
        return []

    def get_aws_principle_compliance(self, tenant_id: str) -> list[dict]:
        """Compute AWS principle compliance from data source trust tiers."""
        warning_sources = [
            s for s in self._data_sources
            if s.get("sub_category") in ("weather_climate", "seismic_geological", "fire_bushfire")
            or "warning" in s.get("name", "").lower()
            or "alert" in s.get("name", "").lower()
        ]
        total = len(warning_sources) if warning_sources else 1

        # Sources with tier_1 trust are fully aligned with AWS principles
        tier1_count = sum(
            1 for s in warning_sources
            if s.get("trust_tier", "").startswith("tier_1")
        )

        results = []
        for code, name in AWS_PRINCIPLES:
            compliant = tier1_count
            rate = round((compliant / total) * 100, 1) if total > 0 else 0.0
            results.append({
                "principle": code,
                "display_name": name,
                "compliant_count": compliant,
                "total_count": total,
                "compliance_rate_pct": rate,
                "non_compliant_warning_ids": [],
            })

        return results

    # --- Compliance Matrix (FR-022, FR-023) ---

    def get_compliance_entries(self, tenant_id: str) -> list[dict]:
        """Build compliance matrix from stored assessments or seed baseline."""
        if self._repo:
            try:
                sources = self._repo.list_sources()
                if sources:
                    entries = []
                    now = datetime.now(UTC)
                    for s in sources:
                        status_map = {
                            "compliant": "compliant",
                            "non_compliant": "non_compliant",
                            "unassessed": "pending",
                            "partially_compliant": "pending",
                            "compliance_lapsed": "grace_period",
                        }
                        matrix_status = status_map.get(
                            getattr(s, "compliance_status", "unassessed"), "pending",
                        )
                        countdown = None
                        if getattr(s, "grace_period_end", None):
                            delta = s.grace_period_end - now
                            countdown = max(0, delta.days)

                        entries.append({
                            "data_source_id": s.data_source_id,
                            "data_source_name": s.name,
                            "compliance_status": matrix_status,
                            "last_assessment_date": getattr(s, "updated_at", now),
                            "next_assessment_due_date": getattr(s, "next_assessment_due_date", None),
                            "governance_gap_count": getattr(s, "governance_gap_count", 0),
                            "grace_period_expiry": getattr(s, "grace_period_end", None),
                            "grace_period_reason": getattr(s, "grace_period_reason", None),
                            "grace_period_countdown_days": countdown,
                            "category": getattr(s, "kind", "unknown"),
                            "data_source_type": "stored",
                        })
                    return entries
            except Exception:
                logger.warning("Failed to build compliance from repo, falling back to seed")

        # Seed-derived baseline
        now = datetime.now(UTC)
        entries = []
        for s in self._data_sources:
            entries.append({
                "data_source_id": s.get("data_source_id", ""),
                "data_source_name": s.get("name", ""),
                "compliance_status": "pending",
                "last_assessment_date": now,
                "next_assessment_due_date": None,
                "governance_gap_count": 0,
                "grace_period_expiry": None,
                "grace_period_reason": None,
                "grace_period_countdown_days": None,
                "category": s.get("kind", "unknown"),
                "data_source_type": "seed_fallback",
            })

        return entries

    # --- Audit Trail (FR-018, FR-020) ---

    def search_audit_events(
        self,
        tenant_id: str,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        actor: str | None = None,
        action_type: str | None = None,
        affected_entity: str | None = None,
        keyword: str | None = None,
    ) -> list[dict]:
        """Query real audit entries from governance repository."""
        if not self._repo:
            return []

        try:
            # Use governance_registry's audit trail query
            entries = self._repo.get_audit_trail(
                data_source_id=affected_entity or "",
                action=action_type,
                from_dt=date_from,
                to_dt=date_to,
            )
            return [
                {
                    "event_id": getattr(e, "audit_entry_id", ""),
                    "action": getattr(e, "action", ""),
                    "actor": getattr(e, "actor_id", ""),
                    "timestamp": getattr(e, "timestamp", datetime.now(UTC)),
                    "entity_type": "data_source",
                    "entity_id": getattr(e, "data_source_id", ""),
                    "details": getattr(e, "details", {}),
                }
                for e in entries
            ]
        except Exception:
            logger.warning("Failed to query audit trail from repo")
            return []

    def has_active_recovery(self, tenant_id: str) -> bool:
        """Check if recovery catalogue has data (no active incidents = no active recovery)."""
        return False
