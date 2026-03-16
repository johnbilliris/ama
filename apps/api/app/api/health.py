import os

from fastapi import APIRouter

router = APIRouter(tags=["system"])


def _dependency_status(env_name: str) -> str:
    value = os.getenv(env_name)
    if not value:
        return "stub"
    return "healthy"


@router.get("/health")
async def healthcheck() -> dict[str, object]:
    dependencies = {
        "cosmos": _dependency_status("COSMOS_ENDPOINT"),
        "redis": _dependency_status("REDIS_HOST"),
        "openai": _dependency_status("AZURE_OPENAI_ENDPOINT"),
    }

    status = "healthy"
    if any(value == "unavailable" for value in dependencies.values()):
        status = "degraded"

    return {
        "status": status,
        "version": "0.2.0",
        "dependencies": dependencies,
    }
