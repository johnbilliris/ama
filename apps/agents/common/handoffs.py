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
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentHandoffEvent(BaseModel):
    handoff_id: str
    incident_id: str
    source_agent: str
    target_agent: str
    scope_key: str
    confidence: float
    payload: dict[str, object]
    tenant_id: str = "live"
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    retry_window_seconds: int = 300
    next_retry_at: datetime | None = None
    timeline_event_id: str | None = None
    dead_letter_entry_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None


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
    retry_window_seconds: int = 300,
) -> AgentHandoffEvent:
    """Deliver a handoff with async non-blocking retries and 2-second cap per attempt."""
    handoff.max_retries = max_retries
    handoff.retry_window_seconds = retry_window_seconds
    # Exponential backoff: 0.5s, 1s, 2s, 4s ... capped at retry_window_seconds
    # so the worst-case wait between attempts cannot exceed the configured window.
    backoff_base_seconds = 0.5
    start_time = time.monotonic()

    for attempt in range(1, max_retries + 1):
        try:
            # FR-002: 2-second maximum blocking cap per delivery attempt
            await asyncio.wait_for(deliver(handoff), timeout=2.0)
            handoff.status = "delivered"
            handoff.retry_count = attempt - 1
            handoff.delivered_at = datetime.now(UTC)
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "handoff_delivered",
                extra={
                    "handoff_id": handoff.handoff_id,
                    "retry_count": attempt - 1,
                    "duration_ms": duration_ms,
                },
            )
            return handoff
        except Exception as error:
            handoff.status = "retrying" if attempt < max_retries else "failed"
            handoff.retry_count = attempt
            handoff.failure_reason = str(error)
            handoff.next_retry_at = datetime.now(UTC)
            logger.warning(
                "handoff_retry",
                extra={
                    "handoff_id": handoff.handoff_id,
                    "attempt": attempt,
                    "target_agent": handoff.target_agent,
                    "error_reason": str(error),
                },
            )
            if attempt < max_retries:
                retry_sleep = min(
                    float(retry_window_seconds),
                    backoff_base_seconds * (2 ** (attempt - 1)),
                )
                await asyncio.sleep(retry_sleep)

    handoff.status = "dead_lettered"
    handoff.failed_at = datetime.now(UTC)
    if on_dead_letter is not None:
        handoff.dead_letter_entry_id = on_dead_letter(handoff)
    logger.error(
        "handoff_dead_lettered",
        extra={
            "handoff_id": handoff.handoff_id,
            "retry_count": max_retries,
            "dead_letter_entry_id": handoff.dead_letter_entry_id,
        },
    )
    return handoff


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
    recommendations: list[dict],
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
