from datetime import datetime

from packages.domain.src.domain.models.agent_governance import AgentGovernanceAssignment
from packages.domain.src.domain.models.constitutional_assessment import ConstitutionalAssessment
from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.models.functional_domain_precedence import FunctionalDomainPrecedence
from packages.domain.src.domain.models.governance_audit import GovernanceAuditEntry
from packages.domain.src.domain.models.handoff_chain import HandoffChainDefinition


class GovernanceRepository:
    """In-memory governance store. Swap for Cosmos DB client in production."""

    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}
        self._assessments: dict[str, ConstitutionalAssessment] = {}
        self._assignments: dict[str, AgentGovernanceAssignment] = {}
        self._chains: dict[str, HandoffChainDefinition] = {}
        self._precedence: dict[str, FunctionalDomainPrecedence] = {}
        self._audit: list[GovernanceAuditEntry] = []

    # --- DataSource ---

    def save_source(self, source: DataSource) -> DataSource:
        now = datetime.utcnow()
        if source.data_source_id not in self._sources:
            source.created_at = source.created_at or now
        source.updated_at = now
        self._sources[source.data_source_id] = source
        return source

    def get_source(self, data_source_id: str) -> DataSource | None:
        return self._sources.get(data_source_id)

    def list_sources(self, **filters: str | None) -> list[DataSource]:
        results = list(self._sources.values())
        for key, value in filters.items():
            if value is not None:
                results = [s for s in results if getattr(s, key, None) == value]
        return results

    # --- ConstitutionalAssessment ---

    def save_assessment(self, assessment: ConstitutionalAssessment) -> ConstitutionalAssessment:
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    def get_assessments_for_source(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return [a for a in self._assessments.values() if a.data_source_id == data_source_id]

    def get_current_assessments(self, data_source_id: str) -> list[ConstitutionalAssessment]:
        return [a for a in self.get_assessments_for_source(data_source_id) if a.is_current]

    # --- AgentGovernanceAssignment ---

    def save_assignment(self, assignment: AgentGovernanceAssignment) -> AgentGovernanceAssignment:
        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_assignments_for_source(self, data_source_id: str) -> list[AgentGovernanceAssignment]:
        return [
            a for a in self._assignments.values()
            if a.data_source_id == data_source_id and a.status == "active"
        ]

    # --- HandoffChainDefinition ---

    def save_chain(self, chain: HandoffChainDefinition) -> HandoffChainDefinition:
        self._chains[chain.chain_id] = chain
        return chain

    def get_chain_for_source(self, data_source_id: str) -> HandoffChainDefinition | None:
        for chain in self._chains.values():
            if chain.data_source_id == data_source_id and chain.status == "active":
                return chain
        return None

    # --- FunctionalDomainPrecedence ---

    def save_precedence(self, precedence: FunctionalDomainPrecedence) -> FunctionalDomainPrecedence:
        self._precedence[precedence.precedence_id] = precedence
        return precedence

    def list_precedence(self, hazard_type: str | None = None, jurisdiction_id: str | None = None) -> list[FunctionalDomainPrecedence]:
        results = list(self._precedence.values())
        if hazard_type:
            results = [p for p in results if p.hazard_type == hazard_type]
        if jurisdiction_id is not None:
            results = [p for p in results if p.jurisdiction_id == jurisdiction_id]
        return results

    def resolve_precedence(self, hazard_type: str, jurisdiction_id: str | None = None) -> FunctionalDomainPrecedence | None:
        if jurisdiction_id:
            override = next(
                (p for p in self._precedence.values()
                 if p.hazard_type == hazard_type and p.jurisdiction_id == jurisdiction_id),
                None,
            )
            if override:
                return override
        return next(
            (p for p in self._precedence.values()
             if p.hazard_type == hazard_type and p.jurisdiction_id is None),
            None,
        )

    # --- GovernanceAuditEntry ---

    def append_audit(self, entry: GovernanceAuditEntry) -> GovernanceAuditEntry:
        self._audit.append(entry)
        return entry

    def get_audit_trail(
        self,
        data_source_id: str,
        action: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[GovernanceAuditEntry]:
        results = [e for e in self._audit if e.data_source_id == data_source_id]
        if action:
            results = [e for e in results if e.action == action]
        if from_dt:
            results = [e for e in results if e.timestamp >= from_dt]
        if to_dt:
            results = [e for e in results if e.timestamp <= to_dt]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)
