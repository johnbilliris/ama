"""Eval API router (`/api/eval/...`).

Wires the run, scorecard, dataset, metric and tier-2 endpoints. Specific route
handlers live in sibling modules to keep this file thin.

Mounted in `apps/api/app/api/router.py`.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(prefix="/eval", tags=["eval"])


@router.get("/health")
async def health() -> dict[str, str | bool]:
    """Health probe for the eval API.

    Exposes ``anonymousAccess`` so the operator script can detect FR-022a
    dev-only anonymous mode and skip minting an Authorization header.
    """

    env_name = os.environ.get("ENVIRONMENT", "").strip().lower()
    anon_flag = os.environ.get("EVAL_ALLOW_ANONYMOUS", "").strip()
    anonymous_access = env_name == "dev" and anon_flag == "1"
    return {
        "status": "ok",
        "module": "llm-eval-framework",
        "checkedAt": datetime.now(UTC).isoformat(),
        "environment": env_name or "unknown",
        "anonymousAccess": anonymous_access,
    }


def register_subroutes() -> None:
    """Lazy-register sub-routers to avoid circular imports."""
    from . import datasets, metrics, runs, scorecards, traces  # noqa: PLC0415

    router.include_router(runs.router)
    router.include_router(scorecards.router)
    router.include_router(datasets.router)
    router.include_router(metrics.router)
    router.include_router(traces.router)


__all__ = ["router", "register_subroutes"]
