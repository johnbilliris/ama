"""Planning Agent — AIDR emergency planning with 9-step process and plan lifecycle.

Implements the AIIMS Planning function with a ``create_app()`` factory
returning a FastAPI application. Follows the established agent pattern.

FRs: FR-001–007 | Research: R-001, R-002, R-008, R-012
"""

import logging
from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel

from planning.config import PlanningConfig

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    agent: str
    agent_version: str
    timestamp: str


class PlanningAgent:
    """Core planning agent with emergency plan lifecycle management."""

    def __init__(self, config: PlanningConfig | None = None):
        self._config = config or PlanningConfig()


def create_app(
    agent: PlanningAgent | None = None,
    config: PlanningConfig | None = None,
) -> FastAPI:
    """Factory function returning a configured FastAPI application."""
    _config = config or PlanningConfig()
    _agent = agent or PlanningAgent(config=_config)

    app = FastAPI(title="Planning Agent", version=_config.agent_version)

    # Store dependencies on app.state
    app.state.agent = _agent
    app.state.config = _config

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            agent="planning",
            agent_version=_config.agent_version,
            timestamp=datetime.now(UTC).isoformat(),
        )

    return app
