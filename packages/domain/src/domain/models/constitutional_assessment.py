from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ConstitutionalPrinciple = Literal[
    "life_safety_first",
    "multi_agent_coordination",
    "data_trust_provenance_freshness",
    "privacy_security_regional_policy",
    "multilingual_accessible_actionable",
    "cloud_platform",
]

AssessmentComplianceStatus = Literal["compliant", "partially_compliant", "non_compliant", "not_applicable"]

AssessmentTrigger = Literal["initial_review", "source_change", "constitution_amendment"]


class ConstitutionalAssessment(BaseModel):
    assessment_id: str
    data_source_id: str
    principle: ConstitutionalPrinciple
    compliance_status: AssessmentComplianceStatus
    explanation: str
    conditions: list[str] = []
    gaps: list[str] = []
    assessor_id: str
    assessed_at: datetime
    superseded_by: str | None = None
    is_current: bool = True
    triggered_by: AssessmentTrigger = "initial_review"
