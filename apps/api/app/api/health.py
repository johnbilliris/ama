import logging
import os

from fastapi import APIRouter

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


def _dependency_status(env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        return "stub"
    # Basic reachability: env var configured means the dependency is expected
    # In production, this would perform an actual connectivity check
    return "healthy"


@router.get("/health")
async def healthcheck() -> dict[str, object]:
    dependencies = {
        "cosmos": _dependency_status("COSMOS_ENDPOINT"),
        "redis": _dependency_status("REDIS_HOST"),
        # Spec 036 / ADR-20 — Foundry is the canonical chat plane post-cutover.
        # Falls back to AZURE_OPENAI_ENDPOINT for the env-var compatibility seam
        # while ADR-20 cleanup PR is pending.
        "foundry": (
            _dependency_status("AZURE_AI_PROJECT_ENDPOINT")
            if os.getenv("AZURE_AI_PROJECT_ENDPOINT")
            else _dependency_status("AZURE_OPENAI_ENDPOINT")
        ),
    }

    # Determine overall status based on dependency health
    statuses = set(dependencies.values())
    if "unavailable" in statuses:
        status = "degraded"
    elif statuses == {"stub"}:
        status = "healthy"  # No dependencies configured — running in stub mode
    else:
        status = "healthy"

    return {
        "status": status,
        "version": "0.2.0",
        "dependencies": dependencies,
    }
