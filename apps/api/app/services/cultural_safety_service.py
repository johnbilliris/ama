"""Cultural-safety subsystem service (spec-035 T053 / FR-016 / NN-4).

Implements the elder-routing + 90-second-timeout + AWS-level-conditional outcome
policy from the
[cultural-safety contract](../../../specs/035-webapp-capstone-closure/contracts/cultural-safety.contract.md).

The service is intentionally self-contained: production wiring layers a
Service Bus client + App Configuration loader on top of the abstract hooks
defined here without altering the core decision logic.

Outcomes (closed-set):

* ``cultural_safety_timeout_override`` — only on ``emergency_warning`` and only
  when the IC explicitly confirms via the action card.
* ``cultural_safety_held`` — for ``watch_and_act`` / ``advice`` timeouts and for
  any explicit elder decline.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from app.observability.audit_span import record_audit_outcome

logger = logging.getLogger(__name__)


class AwsLevel(StrEnum):
    advice = "advice"
    watch_and_act = "watch_and_act"
    emergency_warning = "emergency_warning"


class CulturalSafetyState(StrEnum):
    pending_elder = "pending_elder"
    approved = "approved"
    declined = "declined"
    timeout_lifesafety_override = "timeout_lifesafety_override"
    timeout_blocked = "timeout_blocked"


class CulturalSafetyOutcome(StrEnum):
    """Audit outcomes emitted by the subsystem (closed-set)."""

    cultural_safety_timeout_override = "cultural_safety_timeout_override"
    cultural_safety_held = "cultural_safety_held"


_DEFAULT_TIMEOUT_SECONDS = 90
_TIMEOUT_OVERRIDE_AWS_LEVELS: frozenset[AwsLevel] = frozenset(
    {AwsLevel.emergency_warning}
)


@dataclass
class CulturalSafetyDraft:
    draft_id: str
    aws_level: AwsLevel
    jurisdiction: str
    language_pack: str
    operator_identity: str
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class CulturalSafetyDecision:
    state: CulturalSafetyState
    outcome: CulturalSafetyOutcome | None
    audit_row: dict[str, Any]


class CulturalSafetyError(Exception):
    """Raised when an IC override is attempted on a non-eligible AWS level."""


ElderRouter = Callable[[CulturalSafetyDraft], Awaitable[None]]


class CulturalSafetyService:
    """Pure decision service for cultural-safety outcomes.

    A production driver wraps this with a real Service Bus router and an App
    Configuration-backed timeout/feature-flag loader.
    """

    def __init__(
        self,
        *,
        elder_router: ElderRouter | None = None,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
        timeout_override_aws_levels: frozenset[AwsLevel] | None = None,
    ) -> None:
        self._elder_router = elder_router
        self._timeout_seconds = timeout_seconds
        self._timeout_override_aws_levels = (
            timeout_override_aws_levels or _TIMEOUT_OVERRIDE_AWS_LEVELS
        )

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

    async def enqueue_elder_approval(self, draft: CulturalSafetyDraft) -> None:
        """Routes the draft to the elder-approval queue if a router is wired."""

        if self._elder_router is None:
            logger.debug(
                "cultural_safety.elder_router_not_configured",
                extra={"draft_id": draft.draft_id},
            )
            return
        await self._elder_router(draft)

    def on_timeout(
        self,
        draft: CulturalSafetyDraft,
        *,
        ic_confirmer_oid: str | None = None,
    ) -> CulturalSafetyDecision:
        """Produces the timeout decision per AWS-level-conditional policy.

        ``ic_confirmer_oid`` is required to materialise an
        ``cultural_safety_timeout_override`` outcome and is rejected for any
        AWS level not in the timeout-override allowlist.
        """

        is_override_eligible = draft.aws_level in self._timeout_override_aws_levels
        if ic_confirmer_oid is not None and not is_override_eligible:
            raise CulturalSafetyError(
                f"IC override not permitted on aws_level={draft.aws_level.value}"
            )

        ts = datetime.now(UTC).isoformat()
        if is_override_eligible and ic_confirmer_oid is not None:
            outcome = CulturalSafetyOutcome.cultural_safety_timeout_override
            state = CulturalSafetyState.timeout_lifesafety_override
            audit_row: dict[str, Any] = {
                "outcome": outcome.value,
                "operator_identity": draft.operator_identity,
                "cultural_safety_confirmer": ic_confirmer_oid,
                "aws_level": draft.aws_level.value,
                "draft_id": draft.draft_id,
                "language_pack": draft.language_pack,
                "timeout_seconds": self._timeout_seconds,
                "correlation_id": draft.correlation_id,
                "timestamp": ts,
            }
            record_audit_outcome(
                outcome.value,
                attributes={
                    "ama.audit.aws_level": draft.aws_level.value,
                    "ama.audit.draft_id": draft.draft_id,
                    "ama.audit.correlation_id": draft.correlation_id,
                },
            )
            return CulturalSafetyDecision(state=state, outcome=outcome, audit_row=audit_row)

        outcome = CulturalSafetyOutcome.cultural_safety_held
        state = (
            CulturalSafetyState.timeout_lifesafety_override
            if is_override_eligible
            else CulturalSafetyState.timeout_blocked
        )
        audit_row = {
            "outcome": outcome.value,
            "operator_identity": draft.operator_identity,
            "aws_level": draft.aws_level.value,
            "draft_id": draft.draft_id,
            "language_pack": draft.language_pack,
            "timeout_seconds": self._timeout_seconds,
            "correlation_id": draft.correlation_id,
            "timestamp": ts,
        }
        record_audit_outcome(
            outcome.value,
            attributes={
                "ama.audit.aws_level": draft.aws_level.value,
                "ama.audit.draft_id": draft.draft_id,
                "ama.audit.correlation_id": draft.correlation_id,
            },
        )
        return CulturalSafetyDecision(state=state, outcome=outcome, audit_row=audit_row)

    def on_elder_decline(
        self, draft: CulturalSafetyDraft
    ) -> CulturalSafetyDecision:
        """Elder-decline outcome is held regardless of AWS level."""

        ts = datetime.now(UTC).isoformat()
        record_audit_outcome(
            CulturalSafetyOutcome.cultural_safety_held.value,
            attributes={
                "ama.audit.aws_level": draft.aws_level.value,
                "ama.audit.draft_id": draft.draft_id,
                "ama.audit.correlation_id": draft.correlation_id,
                "ama.audit.decline_reason": "elder_declined",
            },
        )
        return CulturalSafetyDecision(
            state=CulturalSafetyState.declined,
            outcome=CulturalSafetyOutcome.cultural_safety_held,
            audit_row={
                "outcome": CulturalSafetyOutcome.cultural_safety_held.value,
                "operator_identity": draft.operator_identity,
                "aws_level": draft.aws_level.value,
                "draft_id": draft.draft_id,
                "language_pack": draft.language_pack,
                "decline_reason": "elder_declined",
                "correlation_id": draft.correlation_id,
                "timestamp": ts,
            },
        )

    def deadline_for(self, started_at: datetime) -> datetime:
        return started_at + timedelta(seconds=self._timeout_seconds)


__all__ = [
    "AwsLevel",
    "CulturalSafetyDecision",
    "CulturalSafetyDraft",
    "CulturalSafetyError",
    "CulturalSafetyOutcome",
    "CulturalSafetyService",
    "CulturalSafetyState",
]
