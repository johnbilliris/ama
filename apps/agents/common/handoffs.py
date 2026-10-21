"""Legacy point-to-point agent handoff primitives.

DEPRECATED — superseded by ``apps/agents/maf_runtime/workflow/builder.py`` +
the per-agent custom Executors under ``apps/agents/maf_runtime/workflow/executors/``.
This module is retained for FR-026 fallback during the per-agent cutover
window. Once SC-001 (legacy paths removed or behind documented fallback flag)
is satisfied, this module may be deleted.

See the cutover playbook (``docs/aidr/runbooks/maf-cutover-playbook.md``) and
the rollback runbook (``docs/aidr/runbooks/maf-rollback.md``) for the operator
flow.
"""

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from common.circuit_breaker import CircuitBreaker
from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)

_claim_lock = threading.Lock()
_delivery_claims: set[tuple[str, str]] = set()


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _claim_delivery(tenant_id: str, handoff_id: str) -> bool:
    claim_key = (tenant_id, handoff_id)
    with _claim_lock:
        if claim_key in _delivery_claims:
            return False
        _delivery_claims.add(claim_key)
        return True


def _release_delivery(tenant_id: str, handoff_id: str) -> None:
    with _claim_lock:
        _delivery_claims.discard((tenant_id, handoff_id))


class AgentHandoffEvent(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )

    handoff_id: str
    incident_id: str
    source_agent: str
    target_agent: str
    scope_key: str
    confidence: float = Field(ge=0.0, le=1.0)
    payload: dict[str, object]
    tenant_id: str = "live"
    status: Literal["pending", "delivered", "retrying", "failed", "dead_lettered"] = "pending"
    attempt_count: int = Field(default=0, ge=0, le=3)
    retry_count: int = Field(default=0, ge=0, le=2)
    max_attempts: int = Field(default=3, ge=1, le=3)
    max_retries: int = Field(default=2, ge=0, le=2)
    retry_window_seconds: float = Field(default=300.0, gt=0.0)
    next_retry_at: datetime | None = None
    timeline_event_id: str | None = None
    dead_letter_entry_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def _validate_invariants(self) -> "AgentHandoffEvent":
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.next_retry_at is not None and self.next_retry_at.tzinfo is None:
            raise ValueError("next_retry_at must be timezone-aware")
        if self.delivered_at is not None and self.delivered_at.tzinfo is None:
            raise ValueError("delivered_at must be timezone-aware")
        if self.failed_at is not None and self.failed_at.tzinfo is None:
            raise ValueError("failed_at must be timezone-aware")

        if self.max_attempts != self.max_retries + 1:
            raise ValueError("max_attempts must equal max_retries + 1")

        if self.attempt_count == 0 and self.retry_count != 0:
            raise ValueError("retry_count must be 0 when attempt_count is 0")
        if self.attempt_count > 0 and self.retry_count != self.attempt_count - 1:
            raise ValueError("retry_count must equal attempt_count - 1")
        if self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count must be <= max_attempts")
        if self.retry_count > self.max_retries:
            raise ValueError("retry_count must be <= max_retries")

        if self.status in {"failed", "dead_lettered"} and not self.failure_reason:
            raise ValueError("failure_reason is required when status is failed or dead_lettered")
        if self.status == "delivered" and self.delivered_at is None:
            raise ValueError("delivered_at is required when status is delivered")
        return self

    def _assert_status_transition(self, next_status: str) -> None:
        allowed: dict[str, set[str]] = {
            "pending": {"delivered", "retrying", "failed"},
            "retrying": {"delivered", "failed"},
            "failed": {"dead_lettered"},
            "delivered": set(),
            "dead_lettered": set(),
        }
        if self.status == next_status:
            return
        if next_status not in allowed.get(self.status, set()):
            raise ValueError(f"invalid handoff status transition: {self.status} -> {next_status}")

    def mark_retrying(self, *, reason: str, next_retry_at: datetime | None = None) -> None:
        self._assert_status_transition("retrying")
        self.failure_reason = reason
        self.next_retry_at = next_retry_at
        self.status = "retrying"

    def mark_delivered(self, *, delivered_at: datetime | None = None) -> None:
        self._assert_status_transition("delivered")
        if self.attempt_count == 0:
            self._set_attempt_state(1)
        self.failure_reason = None
        self.next_retry_at = None
        self.delivered_at = delivered_at or datetime.now(UTC)
        self.status = "delivered"

    def mark_failed(self, *, reason: str, failed_at: datetime | None = None) -> None:
        self._assert_status_transition("failed")
        self.failure_reason = reason
        self.failed_at = failed_at or datetime.now(UTC)
        self.next_retry_at = None
        self.status = "failed"

    def mark_dead_lettered(self, *, reason: str, dead_letter_entry_id: str | None = None) -> None:
        self._assert_status_transition("dead_lettered")
        self.failure_reason = reason
        self.dead_letter_entry_id = dead_letter_entry_id
        if self.failed_at is None:
            self.failed_at = datetime.now(UTC)
        self.next_retry_at = None
        self.status = "dead_lettered"

    def _set_attempt_state(self, attempt_count: int) -> None:
        retry_count = max(0, attempt_count - 1)
        if attempt_count < 0 or attempt_count > self.max_attempts:
            raise ValueError("attempt_count out of bounds")
        if retry_count > self.max_retries:
            raise ValueError("retry_count out of bounds")
        object.__setattr__(self, "attempt_count", attempt_count)
        object.__setattr__(self, "retry_count", retry_count)

    def set_attempt_budget(self, total_attempts: int) -> None:
        if total_attempts < 1 or total_attempts > 3:
            raise ValueError("total_attempts must be between 1 and 3")
        object.__setattr__(self, "max_attempts", total_attempts)
        object.__setattr__(self, "max_retries", total_attempts - 1)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "status" and "status" in self.__dict__:
            self._assert_status_transition(str(value))
        super().__setattr__(name, value)


def build_handoff(
    *,
    incident_id: str,
    source_agent: str,
    target_agent: str,
    scope_key: str,
    payload: dict[str, object],
    confidence: float,
    tenant_id: str = "live",
) -> AgentHandoffEvent:
    return AgentHandoffEvent(
        handoff_id=f"handoff-{uuid4().hex}",
        incident_id=incident_id,
        source_agent=source_agent,
        target_agent=target_agent,
        scope_key=scope_key,
        payload=payload,
        confidence=confidence,
        tenant_id=tenant_id,
    )


def build_recovery_handoff(
    *,
    incident_id: str,
    source_agent: str,
    recovery_data: dict[str, object],
    confidence: float = 0.8,
) -> AgentHandoffEvent:
    """Build a recovery-phase handoff (Risk Assessment → recovery agents).

    Uses category_filter=["recovery_assessment"] per FR-054.
    """
    return build_handoff(
        incident_id=incident_id,
        source_agent=source_agent,
        target_agent="recovery_service",
        scope_key="recovery_assessment",
        payload={
            "category": "recovery_assessment",
            **recovery_data,
        },
        confidence=confidence,
    )


def build_lessons_capture_handoff(
    *,
    incident_id: str,
    source_agent: str,
    incident_level: int,
    trigger_source: str = "incident_closure",
    scenario_run_id: str | None = None,
    confidence: float = 1.0,
) -> AgentHandoffEvent:
    """Build a lessons-capture handoff (incident closure Level 2+ → lessons service).

    Uses category_filter=["lessons_capture"] per FR-054.
    """
    payload: dict[str, object] = {
        "category": "lessons_capture",
        "incident_level": incident_level,
        "trigger_source": trigger_source,
    }
    if scenario_run_id:
        payload["scenario_run_id"] = scenario_run_id
    return build_handoff(
        incident_id=incident_id,
        source_agent=source_agent,
        target_agent="lessons_service",
        scope_key="lessons_capture",
        payload=payload,
        confidence=confidence,
    )


async def deliver_handoff_with_retry(
    *,
    handoff: AgentHandoffEvent,
    deliver: Callable[[AgentHandoffEvent], Awaitable[None]],
    on_dead_letter: Callable[[AgentHandoffEvent], str] | None = None,
    max_retries: int = 3,
    retry_window_seconds: float = 300,
    circuit_breaker: CircuitBreaker | None = None,
    clock: Callable[[], float] | None = None,
    sleep_func: Callable[[float], Awaitable[None]] | None = None,
) -> AgentHandoffEvent:
    """Deliver a handoff with circuit checks, one deadline budget, and idempotent claim semantics."""
    total_attempts = max(1, min(max_retries, 3))
    handoff.set_attempt_budget(total_attempts)
    handoff.retry_window_seconds = retry_window_seconds

    if not _claim_delivery(handoff.tenant_id, handoff.handoff_id):
        handoff.mark_delivered()
        logger.info(
            "handoff_duplicate_claim_skipped",
            extra={
                "handoff_id": handoff.handoff_id,
                "tenant_id": handoff.tenant_id,
            },
        )
        return handoff

    timer = clock or time.monotonic
    sleep = sleep_func or asyncio.sleep
    target_circuit = circuit_breaker or CircuitBreaker()

    backoff_base_seconds = 0.5
    start_time = timer()
    deadline = start_time + float(retry_window_seconds)

    try:
        for attempt in range(1, total_attempts + 1):
            handoff._set_attempt_state(attempt)
            remaining_budget = deadline - timer()
            if remaining_budget <= 0:
                handoff.mark_failed(reason="retry window exhausted before delivery")
                break

            if not target_circuit.can_execute():
                if attempt < total_attempts:
                    retry_sleep = min(backoff_base_seconds * (2 ** (attempt - 1)), remaining_budget)
                    handoff.mark_retrying(
                        reason="target circuit open",
                        next_retry_at=datetime.fromtimestamp(datetime.now(UTC).timestamp() + retry_sleep, tz=UTC),
                    )
                    await sleep(retry_sleep)
                else:
                    handoff.mark_failed(reason="target circuit open")
                continue

            try:
                timeout_budget = max(0.001, min(2.0, remaining_budget))
                await asyncio.wait_for(deliver(handoff), timeout=timeout_budget)
                target_circuit.record_success()
                handoff.mark_delivered(delivered_at=datetime.now(UTC))
                duration_ms = (timer() - start_time) * 1000
                logger.info(
                    "handoff_delivered",
                    extra={
                        "handoff_id": handoff.handoff_id,
                        "attempt_count": attempt,
                        "retry_count": attempt - 1,
                        "duration_ms": duration_ms,
                    },
                )
                return handoff
            except Exception as error:
                error_reason = str(error).strip() or type(error).__name__
                target_circuit.record_failure()
                if attempt < total_attempts:
                    handoff.mark_retrying(reason=error_reason)
                else:
                    handoff.mark_failed(reason=error_reason)
                logger.warning(
                    "handoff_retry",
                    extra={
                        "handoff_id": handoff.handoff_id,
                        "attempt_count": attempt,
                        "retry_count": max(0, attempt - 1),
                        "target_agent": handoff.target_agent,
                        "error_reason": error_reason,
                    },
                )
                if attempt < total_attempts:
                    remaining_after_error = deadline - timer()
                    if remaining_after_error <= 0:
                        handoff.mark_failed(reason="retry window exhausted after failure")
                        break
                    retry_sleep = min(backoff_base_seconds * (2 ** (attempt - 1)), remaining_after_error)
                    handoff.mark_retrying(
                        reason=handoff.failure_reason or "delivery retry",
                        next_retry_at=datetime.fromtimestamp(datetime.now(UTC).timestamp() + retry_sleep, tz=UTC),
                    )
                    await sleep(retry_sleep)

        reason = handoff.failure_reason or "delivery failed after retry attempts"
        handoff.retry_count = max(0, handoff.attempt_count - 1)
        dead_letter_entry_id: str | None = None
        if on_dead_letter is not None:
            dead_letter_entry_id = on_dead_letter(handoff)
        handoff.mark_dead_lettered(reason=reason, dead_letter_entry_id=dead_letter_entry_id)
        logger.error(
            "handoff_dead_lettered",
            extra={
                "handoff_id": handoff.handoff_id,
                "attempt_count": handoff.attempt_count,
                "retry_count": handoff.retry_count,
                "dead_letter_entry_id": dead_letter_entry_id,
            },
        )
        return handoff
    finally:
        _release_delivery(handoff.tenant_id, handoff.handoff_id)


def build_plan_activation_handoff(
    *,
    incident_id: str,
    plan_id: str,
    activated_by: str,
) -> AgentHandoffEvent:
    """Build a plan activation handoff (incident management → planning).

    Used when an incident is declared and a pre-existing emergency plan
    should be activated. Follows quickstart.md §Agent Handoff Pattern.
    """
    return build_handoff(
        incident_id=incident_id,
        source_agent="incident_management",
        target_agent="planning",
        scope_key=f"plan_activation:{plan_id}",
        payload={"plan_id": plan_id, "activated_by": activated_by},
        confidence=1.0,
    )


def build_evaluation_lessons_handoff(
    *,
    incident_id: str,
    report_id: str,
    recommendations: list[dict[str, object]],
) -> AgentHandoffEvent:
    """Build a handoff from evaluation report recommendations to lessons management."""
    return build_handoff(
        incident_id=incident_id,
        source_agent="monitoring",
        target_agent="lessons_management",
        scope_key=f"evaluation_lessons:{report_id}",
        payload={"report_id": report_id, "recommendations": recommendations},
        confidence=0.85,
    )


def build_me_framework_handoff(
    *,
    incident_id: str,
    plan_id: str,
) -> AgentHandoffEvent:
    """Build an M&E framework initialisation handoff (planning → monitoring).

    Triggered when recovery arrangements are activated, signalling the
    monitoring agent to set up M&E tracking. Follows quickstart.md §Agent Handoff Pattern.
    """
    return build_handoff(
        incident_id=incident_id,
        source_agent="planning",
        target_agent="monitoring",
        scope_key="me_framework_init",
        payload={"plan_id": plan_id, "trigger": "recovery_arrangements_activated"},
        confidence=0.9,
    )
