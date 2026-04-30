"""Planning Agent configuration — reads all environment variables at startup.

All configurable parameters consolidated per data-model.md §Configurable Parameters.
Values are read once at module import and frozen for the lifetime of the process.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlanningConfig:
    """Immutable configuration read from environment variables with sensible defaults."""

    # Plan generation timeout (NFR-001)
    plan_generation_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("PLAN_GENERATION_TIMEOUT_SECONDS", "15"))
    )

    # Plan review reminder interval
    plan_review_reminder_days: int = field(default_factory=lambda: int(os.getenv("PLAN_REVIEW_REMINDER_DAYS", "365")))

    # Max concurrent active plans (NFR-005)
    max_concurrent_plans: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_PLANS", "20")))

    # Version
    agent_version: str = field(default_factory=lambda: os.getenv("AGENT_VERSION", "0.1.0"))

    def __post_init__(self) -> None:
        """Validate configuration values immediately after construction."""
        if self.plan_generation_timeout_seconds <= 0:
            raise ValueError(f"PLAN_GENERATION_TIMEOUT_SECONDS must be > 0, got {self.plan_generation_timeout_seconds}")
        if self.plan_review_reminder_days <= 0:
            raise ValueError(f"PLAN_REVIEW_REMINDER_DAYS must be > 0, got {self.plan_review_reminder_days}")
        if self.max_concurrent_plans <= 0:
            raise ValueError(f"MAX_CONCURRENT_PLANS must be > 0, got {self.max_concurrent_plans}")
