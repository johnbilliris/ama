"""Telemetry-injection + cascade + routing audit envelope models.

Mirrors the JSON schema in ``contracts/audit-envelope.md`` for feature 036.
Discriminated union by ``entry_type`` over the **20 typed entries** (post
spec-036 amendment cycle T-O06):

- injection.attempted
- injection.success
- injection.refused
- injection.circuit_open
- routing.viewport_hint_mismatch
- routing.jurisdiction_ambiguous
- routing.ambiguous
- cascade.degraded_to_annotation
- cascade.depth2_refused
- thread.cap_exceeded
- lifecycle.paused
- lifecycle.aborted
- lifecycle.resumed
- audit.watermark.locale_missing
- audit.idempotency.replay_cross_user      (NEW — T-O06 / ADR-036-009 §6)
- synthetic-delivery
- sub_agent.timeout
- sub_agent.cancel
- sub_agent.degraded
- tenant_isolation.violation

Every record is append-only; ``sequence_number`` is gap-free per ``simulation_id`` (FR-048).

Spec-036 amendment-cycle T-A06 [AMEND] / T-T03 / T-O07 (FR-061 / FR-066)
------------------------------------------------------------------------
The :class:`AuditEnvelope` carries a small set of optional top-level
fields so AIIMS attribution + idempotency provenance + delivery channel
can be propagated alongside any audit entry without re-amending each
per-type ``details`` schema:

* ``aiims_function`` + ``secondary_aiims_tags`` (T-T03 / FR-061; cap 1+≤2).
* ``prompt_hash_source`` (T-O07; enum
  ``raw_user_input | canonical_llm_prompt | system_only`` per FR-065 / pass-1 Q5).
* ``idempotency_key`` (T-O07; FR-066 / pass-1 Q2).
* ``request_correlation_id`` (T-O07; per audit-envelope §6).
* ``delivery_channel`` (T-O07; enum ``audio | text-live-log | both`` per
  FR-058 / FR-064 / pass-2 Q6).

The per-entry ``details`` schemas for ``sub_agent.timeout`` /
``sub_agent.cancel`` / ``sub_agent.degraded`` are intentionally **NOT**
amended this cycle (audit-envelope.md §6.3 carve-out).
"""

from datetime import datetime
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator

from .aiims_role_assignment import AiimsFunction

EntryType = Literal[
    "injection.attempted",
    "injection.success",
    "injection.refused",
    "injection.circuit_open",
    "routing.viewport_hint_mismatch",
    "routing.jurisdiction_ambiguous",
    "routing.ambiguous",
    "cascade.degraded_to_annotation",
    "cascade.depth2_refused",
    "thread.cap_exceeded",
    "lifecycle.paused",
    "lifecycle.aborted",
    "lifecycle.resumed",
    "lifecycle.refused_while_paused",
    "audit.watermark.locale_missing",
    "audit.watermark.applied",
    "audit.sequence.uncertainty",
    "audit.idempotency.replay_cross_user",
    "audit.rbac.unauthorized_attempt",
    "synthetic-delivery",
    "sub_agent.timeout",
    "sub_agent.cancel",
    "sub_agent.degraded",
    "tenant_isolation.violation",
    "signal_pipeline.dispatch_failed",
    "staging_promotion.refused",
]

ALL_ENTRY_TYPES: tuple[str, ...] = (
    "injection.attempted",
    "injection.success",
    "injection.refused",
    "injection.circuit_open",
    "routing.viewport_hint_mismatch",
    "routing.jurisdiction_ambiguous",
    "routing.ambiguous",
    "cascade.degraded_to_annotation",
    "cascade.depth2_refused",
    "thread.cap_exceeded",
    "lifecycle.paused",
    "lifecycle.aborted",
    "lifecycle.resumed",
    "lifecycle.refused_while_paused",
    "audit.watermark.locale_missing",
    "audit.watermark.applied",
    "audit.sequence.uncertainty",
    "audit.idempotency.replay_cross_user",
    "audit.rbac.unauthorized_attempt",
    "synthetic-delivery",
    "sub_agent.timeout",
    "sub_agent.cancel",
    "sub_agent.degraded",
    "tenant_isolation.violation",
    "signal_pipeline.dispatch_failed",
    "staging_promotion.refused",
)


#: Allowed values for the optional ``prompt_hash_source`` envelope field.
PromptHashSource = Literal[
    "raw_user_input",
    "canonical_llm_prompt",
    "system_only",
]

#: Allowed values for the optional ``delivery_channel`` envelope field.
DeliveryChannel = Literal[
    "audio",
    "text-live-log",
    "both",
]


class AuditSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    component: str
    user_id: str | None = None
    trace_id: str | None = None


# ---- Per-entry detail payloads --------------------------------------------------------


class InjectionAttemptedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    user_id: str
    original_text_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    parse_started_at: datetime
    viewport_centroid_lat: float | None = None
    viewport_centroid_lng: float | None = None
    pii_redactions: int = 0


class InjectionSuccessDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    injection_correlation_id: str
    signal_ids: list[str]
    categories: list[str]
    confidences: list[Literal["high", "medium", "low"]]
    model_deployment: str | None = None
    prompt_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    # Cycle 2 Amendment A2-04 / FR-069 — byte-equal to HTTP 202 body's array
    # after RFC 8785 JCS canonicalisation (pass-1 Q1 / CHK135). Items are
    # JCS-canonicalised dicts of TriggeredSubAgent (extra="forbid",
    # lex-ordered by sub_agent PascalCase per pass-1 Q4). Optional for
    # backward-compat with Cycle 1 audit consumers — emitted on every Cycle 2
    # write but absent from historic Cycle 1 entries (CHK144 read-tolerance).
    triggered_sub_agents: list[dict[str, Any]] | None = None


InjectionRefusalReason = Literal[
    "missing_provenance",
    "life_safety_low_confidence",
    "unknown_category",
    "malformed_input",
    "pii_detected",
    "real_world_action_request",
]


class InjectionRefusedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    reason: InjectionRefusalReason
    original_text_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    parsed_category: str | None = None
    inferred_confidence: Literal["high", "medium", "low"] | None = None
    clarification_question: str | None = None


class InjectionCircuitOpenDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    user_id: str
    attempts_in_window: int
    threshold: int = 60
    window_seconds: int = 60
    enforcement_layer: Literal["apim", "in_process"] = "in_process"
    cooldown_seconds: int = 60


class RoutingViewportHintMismatchDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    client_hint: str
    server_computed: str
    viewport_centroid_lat: float
    viewport_centroid_lng: float
    jurisdiction_dataset_version: str | None = None


class RoutingJurisdictionAmbiguousDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    inference_step_attempted: int = Field(ge=1, le=5)
    candidates: list[str]
    clarification_question: str | None = None


class RoutingAmbiguousDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    chat_turn_id: str
    candidate_agents: list[str]
    confidences: list[float] = Field(default_factory=list)
    clarification_question: str | None = None


class CascadeDegradedToAnnotationDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origin_cascade_id: str
    triggering_thread_id: str
    target_thread_id: str
    affinity_step: int = Field(ge=1, le=5)
    suppressed_proposal: dict[str, Any]


class CascadeDepth2RefusedDetails(BaseModel):
    """`cascade.depth2_refused` — see audit-envelope.md §3.9."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    audit_id: str
    simulation_id: str
    sequence_number: PositiveInt
    tenant_id: str
    timestamp_utc: datetime
    actor: str
    entry_type: Literal["cascade.depth2_refused"] = "cascade.depth2_refused"
    attempted_signal_id: str
    originating_cascade_id: str
    refusal_reason: Literal["depth2_cascade_disallowed"] = "depth2_cascade_disallowed"
    chat_reply_text: str = Field(max_length=500)
    new_top_level_correlation_id: str


class ThreadCapExceededDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    proposed_thread: dict[str, Any]
    current_thread_count: Literal[5] = 5
    rejection_source: Literal["coordinator_injection", "scenario_setup"]


class LifecyclePausedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    attempted_action: Literal["chat_turn", "sub_agent_invocation", "telemetry_injection"]
    coordinator_user_id: str | None = None


class LifecycleAbortedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    coordinator_user_id: str
    cancelled_invocations: int = Field(ge=0)
    abort_timestamp: datetime
    reason: str | None = Field(default=None, max_length=500)


class LifecycleResumedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    coordinator_user_id: str
    previous_paused_duration_seconds: int


class AuditWatermarkLocaleMissingDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    artefact_id: str
    locale: str
    pathway: Literal["text", "audio"]
    fallback_applied: Literal["english_only_text", "english_only_spoken_prefix"]


class AuditIdempotencyReplayCrossUserDetails(BaseModel):
    """Per ``contracts/audit-envelope.md §3.14c`` (T-O06).

    Emitted when a cached idempotent response is replayed by a different
    RBAC subject than the one that originally produced it. Per ADR-036-009
    the replay is permitted (cache wins) but the cross-user replay MUST
    be audited so reviewers can correlate ownership transitions.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    cache_doc_id: str
    cached_rbac_subject_id: str
    replay_rbac_subject_id: str
    verb: str
    route: str


class LifecycleRefusedWhilePausedDetails(BaseModel):
    """Per ``contracts/audit-envelope.md §3.13a`` (T-P02).

    Emitted when a write request (chat turn, telemetry injection, sub-agent
    invocation) arrives while the simulation is in ``paused`` state and is
    refused with HTTP 409. Per pass 2 Q7, the 409 refusal itself is **NOT
    cached** in the FR-066 idempotency cache so a fresh request body is
    serviced cleanly on resume.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    attempted_action: Literal["chat_turn", "sub_agent_invocation", "telemetry_injection"]
    coordinator_user_id: str
    idempotency_key: str | None = None
    request_correlation_id: str
    refusal_response_status: Literal[409] = 409


class AuditWatermarkAppliedDetails(BaseModel):
    """Per ``contracts/audit-envelope.md §3.14a`` (T-P04 / Amendment Q / pass-2 Q6).

    Recorded when the FR-039 / FR-058 / FR-064 watermark is applied to a
    deliverable artefact. Captures the ``delivery_channel`` discriminator
    that links FR-058 audio-prefix renderings to FR-064 accessible
    live-log emissions; both pathways consume the SAME locale table
    (per pass 2 Q6 shared-source-of-truth).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    artefact_id: str
    delivery_channel: Literal["audio", "text-live-log", "both"]
    resolved_locale: str
    watermark_text_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    audio_prefix_table_version: str | None = None
    live_log_sse_event_id: str | None = None


class AuditSequenceUncertaintyDetails(BaseModel):
    """Per ``contracts/audit-envelope.md §3.14b`` (T-N04 / Amendment D / pass-1 Q2).

    Best-effort entry written to the fail-safe dead-letter queue (Cosmos
    ``simulation_audit_dlq`` container) when the FR-048 distributed
    sequence allocator (ADR-036-007) cannot allocate a gap-free
    ``sequence_number`` within its 5-attempt retry budget. Carries
    ``sequence_number = -1`` as a sentinel so downstream readers can
    detect evidence-integrity warnings.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    original_correlation_id: str
    uncertainty_reason: Literal[
        "etag_exhausted",
        "counter_unreachable",
        "replica_partition",
    ]
    sequence_number: Literal[-1] = -1
    fallback_audit_envelope: dict[str, Any]
    queued_at: datetime
    idempotency_key: str | None = None


class AuditRbacUnauthorizedAttemptSubject(BaseModel):
    """Subject of an RBAC denial — see ``audit-envelope.md §3.14d``."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    user_id: str
    tenant_id: str


class AuditRbacUnauthorizedAttemptDetails(BaseModel):
    """Per ``contracts/audit-envelope.md §3.14d`` (T-M03 / FR-051 strengthen).

    Emitted whenever an authenticated principal attempts an action their
    role does not authorise. Per FR-051, every coordinator-only route
    MUST validate JWT/app-role + tenant membership BEFORE any audit
    attempt, and anonymous fallbacks are PROHIBITED in production. The
    cached idempotency response MUST NOT be served when this entry is
    written — the deny decision is authoritative even on replay.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    subject: AuditRbacUnauthorizedAttemptSubject
    route: str
    requested_role: Literal["coordinator", "observer", "admin"]
    actual_roles: list[str] = Field(default_factory=list)
    reason: Literal[
        "missing_role",
        "tenant_mismatch",
        "expired_token",
        "invalid_signature",
    ]
    sim_id: str | None = None
    request_correlation_id: str
    prompt_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    prompt_hash_source: (
        Literal[
            "raw_user_input",
            "canonical_llm_prompt",
            "system_only",
        ]
        | None
    ) = None


class SyntheticDeliveryDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    channel: str
    audience: str
    message_id: str = Field(pattern=r"^sim-msg-[a-f0-9]{4,}$")
    sim_timestamp: datetime
    block_reason: Literal[
        "simulation_tenant_egress_blocked",
        "publication_service_refusal",
        "http_wrapper_refusal",
    ]
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    watermark_applied: Literal[True] = True
    aws_tier: Literal["advice", "watch_and_act", "emergency_warning"] | None = None
    rendered_chat_text: str | None = Field(
        default=None,
        description="Always begins '[SIMULATION] '",
    )


class SubAgentTimeoutDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    correlation_id: str
    sub_agent: str
    timeout_seconds: float
    model_deployment: str | None = None
    soft_ack_emitted: bool | None = None


class SubAgentCancelDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    correlation_id: str
    sub_agent: str
    cancellation_reason: Literal["aborted", "paused_clean_shutdown"]
    elapsed_ms: float | None = None


class SubAgentDegradedDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    correlation_id: str
    sub_agent: str
    degradation_reason: Literal[
        "rate_limit_exhausted",
        "llm_unavailable",
        "cached_state_used",
        "network_partition",
    ]
    fallback_path: str | None = None


class TenantIsolationViolationDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    violation_kind: Literal[
        "citation_to_live_tenant",
        "signal_write_outside_partition",
        "subscription_to_live_signal",
    ]
    offending_resource_id: str
    sub_agent: str | None = None
    rejection_path: Literal["opa_policy", "application_layer", "rbac"] = "application_layer"


class SignalPipelineDispatchFailedDetails(BaseModel):
    """Cycle 2 Amendment A2-01 / A2-08 / FR-067 — typed dispatch-failed envelope.

    Companion to the HTTP 202 ``degraded_dispatch=true`` response surface.
    The ``triggered_sub_agents`` array MUST be byte-equal (after RFC 8785
    JCS canonicalisation) to the response body's array per pass-1 Q1
    (CHK135). The ``degraded_dispatch_flag`` is constrained to ``True`` and
    ``dispatch_ack_timeout_seconds`` to ``5.0`` per pass-2 Q1/Q2 invariants.

    See ``contracts/audit-envelope.md`` §3.25 for the full schema.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    injection_correlation_id: str
    exception_class: str = Field(max_length=200)
    exception_message: str = Field(
        max_length=1000,
        description=("PII-scrubbed truncated message body (≤1000 chars per audit-envelope.md §3.25)."),
    )
    triggered_sub_agents: list[dict[str, Any]] = Field(
        description=(
            "Cycle 2 pass-1 Q1 — byte-equal (after RFC 8785 JCS) to the "
            "HTTP 202 response body's `triggered_sub_agents` array. "
            "Lexicographically ordered by `sub_agent` PascalCase. ONE entry "
            "per attempted subscriber."
        ),
    )
    partial_successful_subset: list[str] = Field(
        description=(
            "Derived view — PascalCase sub_agent names that acknowledged "
            "within DISPATCH_ACK_TIMEOUT_SECONDS (forensic-export ergonomic)."
        ),
    )
    failed_subscriber_list: list[str] = Field(
        description=(
            "Derived view — PascalCase sub_agent names whose dispatch raised or timed out (forensic-export ergonomic)."
        ),
    )
    prompt_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    prompt_hash_source: Literal["raw_user_input", "canonical_llm_prompt", "system_only"]
    degraded_dispatch_flag: Literal[True] = True
    dispatch_ack_timeout_seconds: float = Field(
        default=5.0,
        description=(
            "Cycle 2 pass-2 Q1 — DISPATCH_ACK_TIMEOUT_SECONDS = 5.0 captured for forensic-replay determinism."
        ),
    )
    idempotency_key: str | None = None
    request_correlation_id: str


class StagingPromotionRefusedSampleFloorUnderage(BaseModel):
    """Cycle 3 / A3-01 / FR-071 — per-SLI sample-floor under-meet record."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    sli_id: str
    observed_samples: int = Field(ge=0)
    required_samples: int = Field(ge=1)


class StagingPromotionRefusedDetails(BaseModel):
    """Cycle 3 Amendment A3-01 / FR-071 — typed staging-promotion refusal envelope.

    Written by ``tests/staging_gates.py::assert_sli_thresholds()`` immediately
    before each ``StagingPromotionRefused`` raise (per Cycle 3 Pass-1 Q3 /
    ``spec.md:1016-1097``), recording the gate-job refusal for forensic
    reconstruction.

    The ``staging_promotion_correlation_id`` is a fresh UUID4 per refusal;
    two concurrent refused invocations produce two distinct envelopes with
    two distinct UUIDs (no coalescing). The top-level envelope
    ``correlation_id`` field MUST equal this value (single-stream JOIN
    invariant per Pass-1 Q4 / Pass-2 Q1).

    See ``contracts/audit-envelope.md`` §3.26 for the full schema.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    staging_promotion_correlation_id: str
    build_label: str
    triggering_workflow_run_id: int = Field(ge=1)
    triggering_actor: str
    breached_slis: list[str] = Field(
        description=(
            "Lex-sorted list of SLI ids whose threshold was breached. "
            "Empty list when refusal stems solely from sample-floor under-meets."
        ),
    )
    sample_floor_underages: list[StagingPromotionRefusedSampleFloorUnderage] = Field(
        description=(
            "Per-SLI sample-floor under-meets where observed_samples < "
            "required_samples (per Cycle 2 Pass-2 Q4 / "
            "MIN_SAMPLES_PER_SLI_24H). Empty list when refusal stems solely "
            "from threshold breaches."
        ),
    )
    refused_at: datetime
    gate_helper_version: str = Field(
        pattern=r"^[a-f0-9]{64}$",
        description=("SHA-256 of `tests/staging_gates.py` at run time, captured for forensic-replay determinism."),
    )


# ---- Top-level discriminated union --------------------------------------------------------


class AuditEnvelope(BaseModel):
    """Common audit envelope — applies to every typed entry (FR-048).

    Spec-036 T-A06 [AMEND] (schema 2.0.0) adds optional top-level
    ``aiims_function`` and ``secondary_aiims_tags`` so AIIMS attribution
    can be carried on any entry without amending the per-type ``details``
    payloads (audit-envelope.md §6.3 carve-out).
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    id: str
    partition_key: str = Field(alias="_partitionKey")
    simulation_id: str
    sequence_number: PositiveInt
    entry_type: EntryType
    timestamp: datetime
    source: AuditSource
    correlation_id: str | None = None
    turn_id: str | None = None
    details: dict[str, Any]

    # ---- AIIMS tagging (T-A06 [AMEND] / T-T03 / FR-061) -----------------
    aiims_function: AiimsFunction | None = Field(
        default=None,
        description=(
            "Single primary AIIMS function for the originating sub-agent "
            "invocation, when the entry pertains to one (T-T03). Optional."
        ),
    )
    secondary_aiims_tags: list[AiimsFunction] | None = Field(
        default=None,
        max_length=2,
        description=("≤2 secondary AIIMS tags (constitution v1.2.0). Disjoint from ``aiims_function``."),
    )

    # ---- T-A06 residual envelope fields (T-O07; FR-065 / FR-066) --------
    prompt_hash_source: PromptHashSource | None = Field(
        default=None,
        description=(
            "Provenance of any prompt hash carried in the entry per pass-1 Q5. "
            "One of ``raw_user_input`` / ``canonical_llm_prompt`` / "
            "``system_only``. Optional — only set on entries derived from "
            "user or model input."
        ),
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=512,
        description=(
            "The ``Idempotency-Key`` request header value tied to this audit "
            "entry, when the originating request flowed through the "
            "idempotency cache (T-O02..O06; FR-066)."
        ),
    )
    request_correlation_id: str | None = Field(
        default=None,
        description=(
            "End-to-end request correlation id (typically a UUID/v4 from the "
            "ingress gateway). Distinct from ``correlation_id`` which scopes "
            "to a sub-agent invocation."
        ),
    )
    delivery_channel: DeliveryChannel | None = Field(
        default=None,
        description=(
            "Live-log delivery channel per pass-2 Q6 (FR-058 / FR-064): "
            "``audio`` / ``text-live-log`` / ``both``. Optional — only set "
            "on entries that produced operator-facing output."
        ),
    )

    @model_validator(mode="after")
    def _validate_aiims_disjointness(self) -> "AuditEnvelope":
        if (
            self.aiims_function is not None
            and self.secondary_aiims_tags is not None
            and self.aiims_function in self.secondary_aiims_tags
        ):
            raise ValueError(
                f"secondary_aiims_tags {self.secondary_aiims_tags!r} must not "
                f"include the primary aiims_function {self.aiims_function!r} "
                "(constitution v1.2.0 1+≤2 cap requires disjoint sets)."
            )
        return self


# Convenience: per-type strict envelopes. Useful in unit/contract tests.

DetailsByEntry: dict[str, type[BaseModel]] = {
    "injection.attempted": InjectionAttemptedDetails,
    "injection.success": InjectionSuccessDetails,
    "injection.refused": InjectionRefusedDetails,
    "injection.circuit_open": InjectionCircuitOpenDetails,
    "routing.viewport_hint_mismatch": RoutingViewportHintMismatchDetails,
    "routing.jurisdiction_ambiguous": RoutingJurisdictionAmbiguousDetails,
    "routing.ambiguous": RoutingAmbiguousDetails,
    "cascade.degraded_to_annotation": CascadeDegradedToAnnotationDetails,
    "cascade.depth2_refused": CascadeDepth2RefusedDetails,
    "thread.cap_exceeded": ThreadCapExceededDetails,
    "lifecycle.paused": LifecyclePausedDetails,
    "lifecycle.aborted": LifecycleAbortedDetails,
    "lifecycle.resumed": LifecycleResumedDetails,
    "lifecycle.refused_while_paused": LifecycleRefusedWhilePausedDetails,
    "audit.watermark.locale_missing": AuditWatermarkLocaleMissingDetails,
    "audit.watermark.applied": AuditWatermarkAppliedDetails,
    "audit.sequence.uncertainty": AuditSequenceUncertaintyDetails,
    "audit.idempotency.replay_cross_user": AuditIdempotencyReplayCrossUserDetails,
    "audit.rbac.unauthorized_attempt": AuditRbacUnauthorizedAttemptDetails,
    "synthetic-delivery": SyntheticDeliveryDetails,
    "sub_agent.timeout": SubAgentTimeoutDetails,
    "sub_agent.cancel": SubAgentCancelDetails,
    "sub_agent.degraded": SubAgentDegradedDetails,
    "tenant_isolation.violation": TenantIsolationViolationDetails,
    "signal_pipeline.dispatch_failed": SignalPipelineDispatchFailedDetails,
    "staging_promotion.refused": StagingPromotionRefusedDetails,
}


def validate_details(entry_type: str, details: dict[str, Any]) -> BaseModel:
    """Validate a `details` payload against its discriminator's schema."""

    cls = DetailsByEntry.get(entry_type)
    if cls is None:
        raise ValueError(f"Unknown audit entry_type: {entry_type!r}")
    return cls.model_validate(details)


__all__ = [
    "ALL_ENTRY_TYPES",
    "AuditEnvelope",
    "AuditIdempotencyReplayCrossUserDetails",
    "AuditRbacUnauthorizedAttemptDetails",
    "AuditRbacUnauthorizedAttemptSubject",
    "AuditSequenceUncertaintyDetails",
    "AuditSource",
    "AuditWatermarkAppliedDetails",
    "AuditWatermarkLocaleMissingDetails",
    "CascadeDegradedToAnnotationDetails",
    "CascadeDepth2RefusedDetails",
    "DeliveryChannel",
    "DetailsByEntry",
    "EntryType",
    "InjectionAttemptedDetails",
    "InjectionCircuitOpenDetails",
    "InjectionRefusalReason",
    "InjectionRefusedDetails",
    "InjectionSuccessDetails",
    "LifecycleAbortedDetails",
    "LifecyclePausedDetails",
    "LifecycleRefusedWhilePausedDetails",
    "LifecycleResumedDetails",
    "PromptHashSource",
    "RoutingAmbiguousDetails",
    "RoutingJurisdictionAmbiguousDetails",
    "RoutingViewportHintMismatchDetails",
    "SignalPipelineDispatchFailedDetails",
    "StagingPromotionRefusedDetails",
    "StagingPromotionRefusedSampleFloorUnderage",
    "SubAgentCancelDetails",
    "SubAgentDegradedDetails",
    "SubAgentTimeoutDetails",
    "SyntheticDeliveryDetails",
    "TenantIsolationViolationDetails",
    "ThreadCapExceededDetails",
    "Annotated",
    "Union",
    "validate_details",
]
