"""Autonomy dial (spec 032 FR-AG02).

Per environment + per jurisdiction, agents read an autonomy level
(``low|standard|high``) that gates whether the agent may decide vs must
escalate. Implementation is a small in-memory cache fed by JurisdictionPolicy
(stored in Cosmos; loaded by the API).

Defaults (per ADR + clarify Pass-2 Q4):
  - dev = high
  - staging = standard
  - production = standard
  - rehearsal = high

Jurisdiction policy may override; ``low`` is reserved for life-safety windows
declared by the Incident Commander or Executive Leader.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol

logger = logging.getLogger(__name__)

AutonomyLevel = Literal["low", "standard", "high"]
Environment = Literal["dev", "staging", "production", "rehearsal"]


class JurisdictionPolicy(Protocol):
    autonomy_level: AutonomyLevel
    version: int


DEFAULT_AUTONOMY_BY_ENV: dict[Environment, AutonomyLevel] = {
    "dev": "high",
    "staging": "standard",
    "production": "standard",
    "rehearsal": "high",
}


@dataclass(frozen=True)
class AutonomyDial:
    """Snapshot of autonomy at decision time."""

    environment: Environment
    jurisdiction_code: str
    level: AutonomyLevel
    rationale: str
    snapshot_at: datetime

    def can_decide_life_safety(self) -> bool:
        """Whether the agent may decide a life-safety action without explicit operator approval.

        Always ``False`` because Constitution NN-1 hard-codes human-in-the-loop
        for life-safety actions. The dial only widens or narrows non-life-safety
        autonomy.
        """
        return False

    def can_auto_publish(self) -> bool:
        """Whether the agent may auto-publish non-life-safety information."""
        return self.level == "high"

    def requires_dual_approval(self) -> bool:
        """Whether sensitive non-life-safety actions need dual approval (true in production)."""
        return self.environment == "production" and self.level != "high"


class AutonomyEvaluator:
    """Resolves autonomy for an (env, jurisdiction) pair from the policy store.

    The store argument is intentionally a Protocol-shaped function for
    testability; real instances pass an `apps.api.app.repositories.JurisdictionPolicyRepository`-backed
    callable.
    """

    def __init__(
        self,
        policy_lookup: Callable[[str], JurisdictionPolicy | None] | None = None,
        environment: Environment | None = None,
    ) -> None:
        self._policy_lookup = policy_lookup
        self._environment = environment or self._detect_env()

    @staticmethod
    def _detect_env() -> Environment:
        env = os.getenv("AMA_ENVIRONMENT", "dev").lower()
        if env not in DEFAULT_AUTONOMY_BY_ENV:
            logger.warning("Unknown AMA_ENVIRONMENT %r; defaulting to dev", env)
            return "dev"
        return env

    def evaluate(self, jurisdiction_code: str) -> AutonomyDial:
        """Return the autonomy dial for the given jurisdiction (with snapshot timestamp)."""
        env_default = DEFAULT_AUTONOMY_BY_ENV[self._environment]
        level: AutonomyLevel = env_default
        rationale = f"environment-default ({self._environment})"

        if self._policy_lookup is not None:
            try:
                policy = self._policy_lookup(jurisdiction_code)
                if policy and getattr(policy, "autonomy_level", None) in ("low", "standard", "high"):
                    level = policy.autonomy_level
                    rationale = f"jurisdiction-policy:{jurisdiction_code}:v{getattr(policy, 'version', 0)}"
            except Exception as exc:  # noqa: BLE001
                logger.warning("policy_lookup for %s failed: %s; using env default", jurisdiction_code, exc)

        return AutonomyDial(
            environment=self._environment,
            jurisdiction_code=jurisdiction_code,
            level=level,
            rationale=rationale,
            snapshot_at=datetime.now(UTC),
        )
