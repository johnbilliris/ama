import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.repositories.governance_repository import GovernanceRepository
from app.validators.governance_validators import validate_agent_name, validate_handoff_chain
from fastapi import HTTPException

from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment
from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.functional_domain_precedence import (
    FunctionalDomainPrecedence,
)
from packages.domain.src.domain.models.governance_audit import GovernanceAuditEntry
from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition
from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data

logger = logging.getLogger("governance_registry")

DEFAULT_GRACE_PERIOD_HOURS = 72


class GovernanceRegistryService:
    def __init__(self, repo: GovernanceRepository | None = None) -> None:
        self._repo = repo or GovernanceRepository()

    # --- Audit helper ---

    def _audit(
        self, data_source_id: str, action: str, actor_id: str,
        details: dict | None = None, related_entity_id: str | None = None,
    ) -> GovernanceAuditEntry:
        entry = GovernanceAuditEntry(
            audit_entry_id=f"audit-{uuid4().hex}",
            data_source_id=data_source_id,
            action=action,
            actor_id=actor_id,
            timestamp=datetime.now(UTC),
            details=details or {},
            related_entity_id=related_entity_id,
        )
        try:
            return self._repo.append_audit(entry)
        except Exception:
            logger.exception("audit_trail_write_failure", extra={"data_source_id": data_source_id, "action": action})
            raise

    # --- Seed catalogue ---

    def import_seed_catalogue(self, seed_root: Path, actor_id: str = "system") -> list[DataSource]:
        seed_data = bootstrap_seed_data(seed_root)
        imported: list[DataSource] = []
        for raw in seed_data.get("data_sources", []):
            source = DataSource(**raw)
            existing = self._repo.get_source(source.data_source_id)
            if not existing:
                self._repo.save_source(source)
                self._audit(source.data_source_id, "registered", actor_id, {"source": "seed_catalogue"})
                imported.append(source)
        return imported

    # --- Data source CRUD ---

    def register_source(self, source: DataSource, actor_id: str) -> DataSource:
        if self._repo.get_source(source.data_source_id):
            raise HTTPException(status_code=409, detail=f"Data source '{source.data_source_id}' already exists.")
        saved = self._repo.save_source(source)
        self._audit(saved.data_source_id, "registered", actor_id, {"name": saved.name})
        return saved

    def get_source(self, data_source_id: str) -> DataSource:
        source = self._repo.get_source(data_source_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Data source '{data_source_id}' not found.")
        return source

    def list_sources(self, **filters: str | None) -> list[DataSource]:
        return self._repo.list_sources(**filters)

    def update_source(self, data_source_id: str, updates: dict, actor_id: str) -> DataSource:
        source = self.get_source(data_source_id)
        old_values = {k: getattr(source, k) for k in updates if hasattr(source, k)}
        for key, value in updates.items():
            if hasattr(source, key) and value is not None:
                setattr(source, key, value)
        saved = self._repo.save_source(source)
        self._audit(data_source_id, "updated", actor_id, {"old": old_values, "new": updates})
        self._trigger_rereview_on_change(data_source_id, actor_id)
        return saved

    def deactivate_source(self, data_source_id: str, actor_id: str) -> DataSource:
        source = self.get_source(data_source_id)
        if source.status == "deactivated":
            raise HTTPException(status_code=409, detail="Source is already deactivated.")
        source.status = "deactivated"
        source.deactivated_at = datetime.now(UTC)
        saved = self._repo.save_source(source)
        self._audit(data_source_id, "deactivated", actor_id)
        return saved

    # --- Constitutional compliance ---

    def create_assessment(self, assessment: ConstitutionalAssessment, actor_id: str) -> ConstitutionalAssessment:
        self.get_source(assessment.data_source_id)

        if assessment.compliance_status == "partially_compliant" and not assessment.conditions:
            raise HTTPException(status_code=400, detail="Conditions required for partially_compliant status.")
        if assessment.compliance_status in ("partially_compliant", "non_compliant") and not assessment.gaps:
            raise HTTPException(
                status_code=400,
                detail="Gaps required for partially_compliant or non_compliant status.",
            )

        current = [
            a for a in self._repo.get_current_assessments(assessment.data_source_id)
            if a.principle == assessment.principle
        ]
        for prev in current:
            prev.is_current = False
            prev.superseded_by = assessment.assessment_id
            self._repo.save_assessment(prev)
            self._audit(
                assessment.data_source_id, "assessment_superseded",
                actor_id, related_entity_id=prev.assessment_id,
            )

        saved = self._repo.save_assessment(assessment)
        self._audit(
            assessment.data_source_id, "assessment_created", actor_id,
            {"principle": assessment.principle, "status": assessment.compliance_status},
            related_entity_id=saved.assessment_id,
        )
        self._derive_compliance_status(assessment.data_source_id)
        return saved

    def get_compliance_profile(self, data_source_id: str) -> dict:
        self.get_source(data_source_id)
        all_assessments = self._repo.get_assessments_for_source(data_source_id)
        return {
            "data_source_id": data_source_id,
            "current_assessments": [a for a in all_assessments if a.is_current],
            "historical_assessments": [a for a in all_assessments if not a.is_current],
        }

    def _derive_compliance_status(self, data_source_id: str) -> None:
        source = self.get_source(data_source_id)
        current = self._repo.get_current_assessments(data_source_id)
        if not current:
            source.compliance_status = "unassessed"
        elif any(a.compliance_status == "non_compliant" for a in current):
            source.compliance_status = "non_compliant"
        elif any(a.compliance_status == "partially_compliant" for a in current):
            source.compliance_status = "partially_compliant"
        else:
            source.compliance_status = "compliant"
        self._repo.save_source(source)

    # --- Re-review triggers ---

    def _trigger_rereview_on_change(self, data_source_id: str, actor_id: str) -> None:
        current = self._repo.get_current_assessments(data_source_id)
        if current:
            self._audit(data_source_id, "rereview_triggered", actor_id, {"triggered_by": "source_change"})

    def trigger_constitution_amendment_rereview(self, actor_id: str) -> int:
        flagged = 0
        for source in self._repo.list_sources():
            current = self._repo.get_current_assessments(source.data_source_id)
            if current:
                self._audit(
                    source.data_source_id, "rereview_triggered",
                    actor_id, {"triggered_by": "constitution_amendment"},
                )
                flagged += 1
        return flagged

    # --- Grace period ---

    def start_grace_period(
        self, data_source_id: str, actor_id: str,
        grace_hours: int = DEFAULT_GRACE_PERIOD_HOURS,
    ) -> DataSource:
        source = self.get_source(data_source_id)
        now = datetime.now(UTC)
        source.compliance_status = "compliance_lapsed"
        source.grace_period_start = now
        source.grace_period_end = now + timedelta(hours=grace_hours)
        saved = self._repo.save_source(source)
        self._audit(
            data_source_id, "grace_period_started", actor_id,
            {"grace_hours": grace_hours, "expires_at": saved.grace_period_end.isoformat()},
        )
        return saved

    def extend_grace_period(
        self, data_source_id: str, extend_hours: int,
        actor_id: str, rationale: str = "",
    ) -> DataSource:
        source = self.get_source(data_source_id)
        if source.compliance_status != "compliance_lapsed":
            raise HTTPException(status_code=409, detail="Source is not in compliance_lapsed state.")
        source.grace_period_end = source.grace_period_end + timedelta(hours=extend_hours)
        saved = self._repo.save_source(source)
        self._audit(
            data_source_id, "grace_period_extended", actor_id,
            {
                "extend_hours": extend_hours,
                "rationale": rationale,
                "new_end": saved.grace_period_end.isoformat(),
            },
        )
        return saved

    def block_source_immediately(self, data_source_id: str, actor_id: str) -> DataSource:
        source = self.get_source(data_source_id)
        if source.compliance_status != "compliance_lapsed":
            raise HTTPException(status_code=409, detail="Source is not in compliance_lapsed state.")
        source.compliance_status = "non_compliant"
        source.grace_period_start = None
        source.grace_period_end = None
        saved = self._repo.save_source(source)
        self._audit(data_source_id, "auto_blocked", actor_id, {"reason": "immediate_block_override"})
        return saved

    def check_expired_grace_periods(self) -> list[str]:
        blocked: list[str] = []
        now = datetime.now(UTC)
        for source in self._repo.list_sources(compliance_status="compliance_lapsed"):
            if source.grace_period_end and source.grace_period_end <= now:
                source.compliance_status = "non_compliant"
                source.grace_period_start = None
                source.grace_period_end = None
                self._repo.save_source(source)
                self._audit(source.data_source_id, "auto_blocked", "system", {"reason": "grace_period_expired"})
                blocked.append(source.data_source_id)
        return blocked

    # --- Agent governance ---

    def assign_agent(self, assignment: AgentGovernanceAssignment, actor_id: str) -> AgentGovernanceAssignment:
        source = self.get_source(assignment.data_source_id)
        if source.compliance_status == "non_compliant":
            raise HTTPException(status_code=409, detail="Cannot assign agents to a non-compliant data source.")
        validate_agent_name(assignment.agent_name)

        if assignment.role == "primary":
            existing_primary = [
                a for a in self._repo.get_assignments_for_source(assignment.data_source_id)
                if a.role == "primary"
            ]
            for ep in existing_primary:
                ep.status = "revoked"
                self._repo.save_assignment(ep)

        saved = self._repo.save_assignment(assignment)
        self._audit(
            assignment.data_source_id, "agent_assigned", actor_id,
            {"agent": assignment.agent_name, "role": assignment.role},
            related_entity_id=saved.assignment_id,
        )
        self._derive_governance_status(assignment.data_source_id)
        return saved

    def define_handoff_chain(self, chain: HandoffChainDefinition, actor_id: str) -> HandoffChainDefinition:
        self.get_source(chain.data_source_id)
        assignments = self._repo.get_assignments_for_source(chain.data_source_id)
        primary = next((a for a in assignments if a.role == "primary"), None)
        primary_agent = primary.agent_name if primary else None

        validate_handoff_chain(chain, primary_agent)

        existing = self._repo.get_chain_for_source(chain.data_source_id)
        if existing:
            existing.status = "deprecated"
            self._repo.save_chain(existing)
            self._audit(
                chain.data_source_id, "handoff_deprecated",
                actor_id, related_entity_id=existing.chain_id,
            )

        saved = self._repo.save_chain(chain)
        self._audit(
            chain.data_source_id, "handoff_defined", actor_id,
            {"steps": len(chain.steps)}, related_entity_id=saved.chain_id,
        )
        self._derive_governance_status(chain.data_source_id)
        return saved

    def get_governance_profile(self, data_source_id: str) -> dict:
        self.get_source(data_source_id)
        return {
            "data_source_id": data_source_id,
            "assignments": self._repo.get_assignments_for_source(data_source_id),
            "handoff_chain": self._repo.get_chain_for_source(data_source_id),
        }

    def _derive_governance_status(self, data_source_id: str) -> None:
        source = self.get_source(data_source_id)
        assignments = self._repo.get_assignments_for_source(data_source_id)
        chain = self._repo.get_chain_for_source(data_source_id)
        has_primary = any(a.role == "primary" for a in assignments)

        if not has_primary:
            source.governance_status = "unassigned"
        elif not chain:
            source.governance_status = "assigned"
        elif source.compliance_status in ("compliant", "partially_compliant"):
            source.governance_status = "fully_governed"
        else:
            source.governance_status = "assigned"
        self._repo.save_source(source)

    # --- Precedence ---

    def set_precedence(self, precedence: FunctionalDomainPrecedence, actor_id: str) -> FunctionalDomainPrecedence:
        saved = self._repo.save_precedence(precedence)
        self._audit(
            precedence.primary_data_source_id, "precedence_set", actor_id,
            {"hazard_type": precedence.hazard_type, "jurisdiction": precedence.jurisdiction_id},
        )
        return saved

    def list_precedence(
        self, hazard_type: str | None = None, jurisdiction_id: str | None = None,
    ) -> list[FunctionalDomainPrecedence]:
        return self._repo.list_precedence(hazard_type, jurisdiction_id)

    # --- Governance gaps ---

    def detect_governance_gaps(self) -> list[dict]:
        gaps: list[dict] = []
        for source in self._repo.list_sources():
            if source.status == "deactivated":
                continue
            current_assessments = self._repo.get_current_assessments(source.data_source_id)
            assignments = self._repo.get_assignments_for_source(source.data_source_id)
            if not current_assessments:
                gaps.append({"data_source_id": source.data_source_id, "gap": "no_assessment"})
            if not assignments:
                gaps.append({"data_source_id": source.data_source_id, "gap": "no_assignment"})
        return gaps

    # --- Dashboard ---

    def get_dashboard_summary(self) -> dict:
        sources = [s for s in self._repo.list_sources() if s.status != "deactivated"]
        gaps = self.detect_governance_gaps()
        gap_count = len(gaps)
        lapsed = [s for s in sources if s.compliance_status == "compliance_lapsed"]

        logger.info("governance_gap_count", extra={"gap_count": gap_count})
        for s in lapsed:
            if s.grace_period_end:
                remaining = (s.grace_period_end - datetime.now(UTC)).total_seconds() / 3600
                logger.warning(
                    "grace_period_expiry_warning",
                    extra={
                        "data_source_id": s.data_source_id,
                        "hours_remaining": round(remaining, 1),
                    },
                )

        return {
            "total_sources": len(sources),
            "compliant": sum(1 for s in sources if s.compliance_status == "compliant"),
            "partially_compliant": sum(1 for s in sources if s.compliance_status == "partially_compliant"),
            "non_compliant": sum(1 for s in sources if s.compliance_status == "non_compliant"),
            "unassessed": sum(1 for s in sources if s.compliance_status == "unassessed"),
            "compliance_lapsed": len(lapsed),
            "assigned": sum(1 for s in sources if s.governance_status in ("assigned", "fully_governed")),
            "unassigned": sum(1 for s in sources if s.governance_status == "unassigned"),
            "fully_governed": sum(1 for s in sources if s.governance_status == "fully_governed"),
            "rereview_pending": 0,
        }

    # --- Audit trail ---

    def get_audit_trail(
        self, data_source_id: str, action: str | None = None,
        from_dt: datetime | None = None, to_dt: datetime | None = None,
    ) -> list[GovernanceAuditEntry]:
        return self._repo.get_audit_trail(data_source_id, action, from_dt, to_dt)

    # --- Handoff lookup ---

    def lookup_handoff_chain(self, data_source_id: str) -> HandoffChainDefinition | None:
        start = time.monotonic()
        result = self._repo.get_chain_for_source(data_source_id)
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "handoff_chain_lookup",
            extra={
                "data_source_id": data_source_id,
                "latency_ms": round(elapsed_ms, 2),
                "found": result is not None,
            },
        )
        return result
