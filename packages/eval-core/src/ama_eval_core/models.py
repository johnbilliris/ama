"""Pydantic v2 models for the LLM Evaluation Framework.

Mirrors `specs/030-llm-eval-framework/data-model.md` field-for-field. The single
source of truth for both `apps/api` and `apps/eval-runner`.

Every cross-cutting invariant from data-model.md §"Cross-cutting invariants" is
enforced here via `model_validator`. JSON Schema alignment is asserted in
`tests/unit/eval/test_eval_core_models.py`.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# -- Enums --------------------------------------------------------------------


class HazardTag(StrEnum):
    structure_fire = "structure-fire"
    bushfire = "bushfire"
    flood = "flood"
    storm = "storm"
    building_collapse = "building-collapse"
    hazmat = "hazmat"
    mass_casualty = "mass-casualty"
    missing_person = "missing-person"
    fatality_report = "fatality-report"
    remains_recovery = "remains-recovery"
    evacuation_order = "evacuation-order"
    public_info = "public-info"
    crisis_distress = "crisis-distress"


class SensitivityLabel(StrEnum):
    graphic_fatality = "graphic-fatality"
    human_remains = "human-remains"
    minor_involved = "minor-involved"
    mass_casualty = "mass-casualty"
    prompt_injection = "prompt-injection"
    crisis_distress = "crisis-distress"


class ExpectedAction(StrEnum):
    answer = "answer"
    refuse = "refuse"
    escalate = "escalate"
    clarify = "clarify"
    redirect = "redirect"


class Tone(StrEnum):
    compassionate = "compassionate"
    directive = "directive"
    procedural = "procedural"


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Provenance(StrEnum):
    synthetic = "synthetic"
    sanitised_real = "sanitised-real"


class ApprovalState(StrEnum):
    draft = "draft"
    in_review = "in-review"
    approved = "approved"
    rejected = "rejected"


class ApprovalAction(StrEnum):
    draft = "draft"
    review = "review"
    approve = "approve"
    reject = "reject"
    supersede = "supersede"


class RunStatus(StrEnum):
    queued = "queued"
    provisioning = "provisioning"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelling = "cancelling"
    cancelled = "cancelled"


class RunMode(StrEnum):
    ad_hoc = "ad-hoc"
    scheduled_baseline = "scheduled-baseline"
    pr_fast_subset = "pr-fast-subset"
    progressive_delivery_full = "progressive-delivery-full"


class MetricFamily(StrEnum):
    quality = "quality"
    factuality = "factuality"
    groundedness = "groundedness"
    retrieval = "retrieval"
    safety = "safety"
    refusal_correctness = "refusal-correctness"
    tone = "tone"
    prompt_injection = "prompt-injection"
    operational = "operational"


class MetricTier(StrEnum):
    rule_based = "rule-based"
    primary_judge = "primary-judge"
    secondary_judge_sampled = "secondary-judge-sampled"


class JudgeRole(StrEnum):
    primary = "primary"
    secondary = "secondary"


class MetricState(StrEnum):
    draft = "draft"
    active = "active"
    retired = "retired"


class DatasetState(StrEnum):
    draft = "draft"
    published = "published"


# -- Sub-models ---------------------------------------------------------------

_BCP47_RE = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?(-[A-Za-z0-9]{1,8})*$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_JURISDICTION_RE = re.compile(r"^[A-Z]{2}-[A-Z0-9]{1,3}$")


class ApprovalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    principal: str
    action: ApprovalAction
    timestamp: datetime
    comment: str | None = None


class SanitisationLogEntry(BaseModel):
    entityType: str
    action: Literal["redacted", "replaced"]
    replacement: str | None = None
    at: datetime


class ProvenanceMeta(BaseModel):
    author: str
    reviewer: str
    sourceRunId: str | None = None
    sanitisationLog: list[SanitisationLogEntry] | None = None
    piiScanPass: bool | None = None


class ExpectedBehaviour(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mustInclude: list[str] = Field(default_factory=list)
    mustNotInclude: list[str] = Field(default_factory=list)
    expectedAction: ExpectedAction
    escalationTriggers: list[str] = Field(default_factory=list)
    referToAuthority: bool | None = None
    tone: Tone | None = None


class RetrievedContextEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    docId: str
    content: str
    rank: int = Field(ge=1)
    relevanceLabel: Literal["relevant", "partially-relevant", "irrelevant"] | None = None


# -- EvaluationCase -----------------------------------------------------------


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    caseId: str
    datasetId: str
    version: str
    inputs: dict[str, Any]
    expectedBehaviour: ExpectedBehaviour
    sensitivityLabels: list[SensitivityLabel] = Field(default_factory=list)
    hazardTags: list[HazardTag] = Field(min_length=1)
    jurisdictionTags: list[str] = Field(default_factory=list)
    severity: Severity
    language: str
    provenance: Provenance
    provenanceMeta: ProvenanceMeta
    approvalState: ApprovalState
    approvalChain: list[ApprovalEntry] = Field(default_factory=list)
    metricApplicability: list[str] = Field(default_factory=list)
    retrievalScope: bool = False
    retrievedContext: list[RetrievedContextEntry] = Field(default_factory=list)

    @field_validator("version")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not _SEMVER_RE.match(v):
            raise ValueError(f"version must be semver: got {v!r}")
        return v

    @field_validator("language")
    @classmethod
    def _bcp47(cls, v: str) -> str:
        if not _BCP47_RE.match(v):
            raise ValueError(f"language must be BCP-47: got {v!r}")
        return v

    @field_validator("jurisdictionTags")
    @classmethod
    def _jurisdiction(cls, v: list[str]) -> list[str]:
        for code in v:
            if not _JURISDICTION_RE.match(code):
                raise ValueError(f"jurisdiction must be ISO 3166-2: got {code!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self) -> EvaluationCase:
        # FR-008: refuse ⇒ referToAuthority must be set
        if (
            self.expectedBehaviour.expectedAction == ExpectedAction.refuse.value
            and self.expectedBehaviour.referToAuthority is None
        ):
            raise ValueError("expectedAction='refuse' requires referToAuthority to be set")

        # FR-023: sanitised-real ⇒ sanitisationLog + piiScanPass must be present
        if self.provenance == Provenance.sanitised_real.value:
            if not self.provenanceMeta.sanitisationLog:
                raise ValueError("provenance='sanitised-real' requires provenanceMeta.sanitisationLog")
            if self.provenanceMeta.piiScanPass is not True:
                raise ValueError("provenance='sanitised-real' requires provenanceMeta.piiScanPass=True")

        # FR-008 graphic-tag co-occurrence
        graphic_hazards = {HazardTag.fatality_report.value, HazardTag.remains_recovery.value}
        graphic_labels = {
            SensitivityLabel.graphic_fatality.value,
            SensitivityLabel.human_remains.value,
            SensitivityLabel.mass_casualty.value,
        }
        if any(h in graphic_hazards for h in self.hazardTags):
            if not any(label in graphic_labels for label in self.sensitivityLabels):
                raise ValueError(
                    "hazardTags include fatality-report/remains-recovery; "
                    "sensitivityLabels must include one of graphic-fatality/human-remains/mass-casualty"
                )

        # FR-001(d): retrievalScope=True requires retrievedContext to be populated
        if self.retrievalScope and not self.retrievedContext:
            raise ValueError("retrievalScope=true requires retrievedContext to be non-empty")

        return self


# -- Dataset version ----------------------------------------------------------


class DistributionEntry(BaseModel):
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=1.0)


class EvaluationDatasetVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    datasetId: str
    version: str
    state: DatasetState
    contentHash: str
    caseCount: int = Field(ge=1)
    distribution: dict[str, DistributionEntry]
    languageScope: list[str]
    manifestBlobUri: str
    publishedAt: datetime
    publishedBy: str
    approvalChain: list[ApprovalEntry] = Field(default_factory=list)

    @field_validator("contentHash")
    @classmethod
    def _hash(cls, v: str) -> str:
        if not _SHA256_RE.match(v):
            raise ValueError("contentHash must be sha256:<64-hex>")
        return v

    @field_validator("version")
    @classmethod
    def _ver(cls, v: str) -> str:
        if not _SEMVER_RE.match(v):
            raise ValueError("version must be semver")
        return v


# -- Metric and judge ---------------------------------------------------------


class ScoreScale(BaseModel):
    min: float
    max: float
    unit: str | None = None


class MetricApplicability(BaseModel):
    hazardTags: list[str] | None = None
    expectedAction: list[str] | None = None
    retrievalOnly: bool | None = None


class MetricDefinitionVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    metricId: str
    version: str
    family: MetricFamily
    scoreScale: ScoreScale
    scoringMethod: Literal["rule-based", "primary-judge", "secondary-judge-sampled", "hybrid"]
    tier: MetricTier
    secondarySamplingRate: float | None = Field(default=None, ge=0.0, le=1.0)
    passThreshold: float
    regressionDelta: float | None = Field(default=None, ge=0.0)
    evidenceFields: list[str] = Field(default_factory=list)
    appliesTo: MetricApplicability = Field(default_factory=MetricApplicability)
    judgeId: str | None = None
    state: MetricState = MetricState.draft
    approvalChain: list[ApprovalEntry] = Field(default_factory=list)


class JudgeModelVersion(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    judgeId: str
    version: str
    modelId: str
    modelVersion: str
    role: JudgeRole
    metricBindings: list[str] = Field(default_factory=list)
    promptTemplateRef: str | None = None
    approvedAt: datetime
    approvedBy: str


# -- Models / runs / scorecards -----------------------------------------------


class ModelDeploymentParameters(BaseModel):
    temperature: float | None = None
    topP: float | None = None
    maxTokens: int | None = None
    frequencyPenalty: float | None = None
    presencePenalty: float | None = None


class ModelUnderTest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modelId: str
    version: str
    deploymentRegion: str | None = None
    sku: str | None = None
    parameters: ModelDeploymentParameters | None = None
    catalogRef: str | None = None


class DatasetSubset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hazardTags: list[str] | None = None
    jurisdictionTags: list[str] | None = None
    severity: list[str] | None = None
    sensitivityLabels: list[str] | None = None
    provenance: list[str] | None = None
    maxCases: int | None = Field(default=None, ge=1)


class InfrastructureLifecycleRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    runId: str
    resourceGroup: str | None = None
    deployments: list[dict[str, Any]] = Field(default_factory=list)
    createdAt: datetime | None = None
    deprovisionedAt: datetime | None = None
    terminalState: str | None = None
    orphanCleaned: bool = False


class EvaluationRun(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    runId: str
    status: RunStatus
    mode: RunMode
    datasetId: str
    datasetVersion: str
    datasetSubset: DatasetSubset | None = None
    models: list[ModelUnderTest] = Field(min_length=1)
    metricSetVersion: str
    judgeSetVersion: str | None = None
    policyVersion: str
    estimatedCostAud: float | None = Field(default=None, ge=0.0)
    actualCostAud: float | None = Field(default=None, ge=0.0)
    createdAt: datetime
    createdBy: str
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    exitCode: Literal[0, 1, 2, 3] | None = None
    changeRef: str | None = None
    baselineRunId: str | None = None
    infraLifecycle: InfrastructureLifecycleRecord | None = None


class MetricResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    mean: float
    pass_: bool = Field(alias="pass")
    regression: float | None = None
    distribution: dict[str, Any] | None = None
    tierBreakdown: dict[str, float] | None = None
    judgeId: str | None = None
    judgeVersion: str | None = None


class ScorecardWinner(BaseModel):
    byMetric: dict[str, str] = Field(default_factory=dict)
    overall: str | None = None


class Scorecard(BaseModel):
    model_config = ConfigDict(extra="allow")

    runId: str
    datasetVersion: str
    metricSetVersion: str | None = None
    perModel: dict[str, dict[str, MetricResult]]
    winner: ScorecardWinner
    regressionDiagnostics: list[dict[str, Any]] = Field(default_factory=list)
    secondaryJudgeDisagreements: list[dict[str, Any]] = Field(default_factory=list)
    costAttributionAud: float | None = None
    createdAt: datetime
    baselineRunId: str | None = None


class SampleTrace(BaseModel):
    """Per-sample artefact (Tier-2 only). Stored at runs/{runId}/traces/{caseId}.json."""

    model_config = ConfigDict(extra="allow")

    runId: str
    caseId: str
    modelId: str
    modelVersion: str
    input: dict[str, Any]
    output: str
    safetyFilterTriggered: bool
    latencyMs: int
    tokenUsage: dict[str, int]
    perMetric: dict[str, dict[str, Any]]
    judgeRationale: dict[str, str] | None = None
    classification: Literal["answered", "refused", "failed-to-answer"] | None = None


class Baseline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runId: str
    datasetId: str
    datasetVersion: str
    modelTier: str
    environment: str
    designatedAt: datetime
    designatedBy: str
    supersededBy: str | None = None


class ProvisioningPolicy(BaseModel):
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    policyVersion: str
    env: Literal["dev", "staging", "production"]
    allowedRegions: list[str] = Field(min_length=1)
    allowedSkus: list[str] = Field(min_length=1)
    maxConcurrentDeployments: int = Field(ge=1)
    maxRunCostAud: float = Field(ge=0.0)
    maxRunDurationMinutes: int = Field(ge=1, le=480)
    prFastSubsetMaxMinutes: int = Field(ge=1, le=30)
    secondaryJudgeSamplingRate: float = Field(ge=0.0, le=1.0)
    evaluatorRoles: dict[str, str]
    metricOverrides: dict[str, Any] = Field(default_factory=dict)


class AuditEventSubject(BaseModel):
    type: Literal["dataset", "case", "metric", "judge", "run", "scorecard", "trace", "policy", "gate", "infra", "model"]
    id: str


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auditId: str
    action: str
    principal: str
    timestamp: datetime
    subject: AuditEventSubject
    runId: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    writtenAt: datetime | None = None


__all__ = [
    "ApprovalEntry",
    "ApprovalState",
    "ApprovalAction",
    "AuditEvent",
    "AuditEventSubject",
    "Baseline",
    "DatasetState",
    "DatasetSubset",
    "DistributionEntry",
    "EvaluationCase",
    "EvaluationDatasetVersion",
    "EvaluationRun",
    "ExpectedAction",
    "ExpectedBehaviour",
    "HazardTag",
    "InfrastructureLifecycleRecord",
    "JudgeModelVersion",
    "JudgeRole",
    "MetricDefinitionVersion",
    "MetricFamily",
    "MetricResult",
    "MetricState",
    "MetricTier",
    "MetricApplicability",
    "ModelUnderTest",
    "ModelDeploymentParameters",
    "Provenance",
    "ProvenanceMeta",
    "ProvisioningPolicy",
    "RetrievedContextEntry",
    "RunMode",
    "RunStatus",
    "SampleTrace",
    "SanitisationLogEntry",
    "Scorecard",
    "ScoreScale",
    "ScorecardWinner",
    "SensitivityLabel",
    "Severity",
    "Tone",
]
