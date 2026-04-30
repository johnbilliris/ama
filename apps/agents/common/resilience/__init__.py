"""Resilience sub-package — circuit breakers, retry policies, dead-letter handling, handoff retries.

Spec 032 (FR-A05/Q05) reorganises ``apps/agents/common/`` into three sub-packages:
``resilience/``, ``safety/``, ``lifecycle/``. This package is the canonical home for
resilience primitives.

Backward compatibility: existing flat-namespace imports (``from common.circuit_breaker
import CircuitBreaker``) continue to work because the original modules remain in place.
New code SHOULD import from this sub-package.
"""

from __future__ import annotations

from common.circuit_breaker import CircuitBreaker, CircuitState
from common.content_safety_circuit_breaker import ContentSafetyCircuitBreaker
from common.dead_letters import (
    DeadLetterEntry,
    DeadLetterRedeliveryPoller,
    DeadLetterStore,
)
from common.handoffs import (
    AgentHandoffEvent,
    build_handoff,
    build_lessons_capture_handoff,
    build_recovery_handoff,
)

from .pybreaker_adapter import PyBreakerCircuitBreaker

__all__ = [
    # Existing flat-namespace re-exports
    "CircuitBreaker",
    "CircuitState",
    "ContentSafetyCircuitBreaker",
    "DeadLetterEntry",
    "DeadLetterStore",
    "DeadLetterRedeliveryPoller",
    "AgentHandoffEvent",
    "build_handoff",
    "build_lessons_capture_handoff",
    "build_recovery_handoff",
    # New in spec 032
    "PyBreakerCircuitBreaker",
]
