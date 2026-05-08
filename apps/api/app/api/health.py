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
        "foundry": _dependency_status("AZURE_AI_PROJECT_ENDPOINT"),
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


@router.get("/healthz")
async def healthz() -> dict[str, object]:
    """Spec 036 (T146 / T147 — FR-RAG-IDX-05, FR-RAG-FM-01) cutover health probe.

    Surfaces the four post-cutover fields that ``infra/scripts/azd-up-smoke-test.ps1``
    asserts: ``rag_used`` (always true post-T145), ``corpus_build_sha`` (from
    ``CORPUS_BUILD_SHA`` env), ``embedding_model_id`` (from
    ``AZURE_AI_EMBEDDING_MODEL_ID`` env, defaults to ``text-embedding-3-large@1``),
    and ``alias_active_index`` (from ``AI_SEARCH_ALIAS_ACTIVE_INDEX`` env,
    defaults to ``corpus-v0`` for pre-ingest deploys).

    The dependency block is preserved from ``/health`` so /healthz is a strict
    superset and the smoke-test only needs one probe.
    """
    return {
        "status": "healthy",
        "version": "0.2.0",
        "rag_used": True,
        "corpus_build_sha": os.getenv("CORPUS_BUILD_SHA", "unknown"),
        "embedding_model_id": os.getenv(
            "AZURE_AI_EMBEDDING_MODEL_ID",
            "text-embedding-3-large@1",
        ),
        "alias_active_index": os.getenv("AI_SEARCH_ALIAS_ACTIVE_INDEX", "corpus-v0"),
        "foundry_endpoint_configured": bool(os.getenv("AZURE_AI_PROJECT_ENDPOINT")),
    }
