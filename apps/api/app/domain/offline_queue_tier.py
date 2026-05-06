"""Offline queue tier enum (spec-035 Clarifications Q7).

Mirrors ``packages/domain/src/offline-queue-tier.ts``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class OfflineQueueTier(StrEnum):
    """Service-Worker queue priority bands."""

    LIFE_SAFETY = "life_safety"
    ROUTINE = "routine"


OFFLINE_QUEUE_TIERS: Final[tuple[str, ...]] = tuple(member.value for member in OfflineQueueTier)
OFFLINE_QUEUE_CAP_PER_PERSONA: Final[int] = 500
OFFLINE_QUEUE_LIFE_SAFETY_BATCH_SIZE: Final[int] = 50
