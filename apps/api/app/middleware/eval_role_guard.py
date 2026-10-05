"""FastAPI dependency for tier-2 (`/api/eval/runs/{id}/scorecard/traces/...`) access.

Implements FR-021: Tier-2 endpoints require Eval.Auditor or Eval.Operator role and
emit an `audit.scorecard.trace.read` event for every successful access.

Roles are read from the Entra ID `roles` claim on the JWT (mirrors the AMA pattern
in `apps/api/app/middleware/auth.py`). Falls back to env-var-based dev tokens to
support local development without an Entra app registration.

FR-022a (dev-only anonymous mode): in the development environment only, when both
``ENVIRONMENT == "dev"`` and ``EVAL_ALLOW_ANONYMOUS == "1"`` are set, the role guard
returns a synthetic ``EvalPrincipal(sub="anonymous", ...)`` carrying the full eval
role set so an operator can exercise the pipeline against the synthetic dev dataset
without standing up an Entra ID app or issuing tokens. Anonymous principals are
restricted to the synthetic dev dataset (``disaster-response-core``); access to any
other dataset id is rejected with 403. Staging and production deployments MUST NOT
set ``EVAL_ALLOW_ANONYMOUS`` and the guard refuses to honour it outside ``dev``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status

logger = logging.getLogger(__name__)

# Roles that may read traces / evidence bundles
TIER_2_ROLES = frozenset({"Eval.Auditor", "Eval.Operator"})
# Roles that may queue/cancel runs
RUN_OPERATOR_ROLES = frozenset({"Eval.Operator"})
# Roles that may read scorecards (tier-1, broader audience)
SCORECARD_VIEWER_ROLES = frozenset({"Eval.Viewer", "Eval.Auditor", "Eval.Operator"})

# FR-022a: synthetic principal carries the full eval role set
ANONYMOUS_ROLES = frozenset({"Eval.Operator", "Eval.Viewer", "Eval.Auditor"})
ANONYMOUS_SUB = "anonymous"
# FR-022a (b): anonymous principals may only touch the synthetic dev dataset.
# Real-derived datasets (provenance=sanitised-real) and any dataset whose cases
# carry sensitivity labels outside this allow-list MUST be rejected.
ANONYMOUS_ALLOWED_DATASETS = frozenset({"disaster-response-core"})


@dataclass(frozen=True)
class EvalPrincipal:
    sub: str
    roles: frozenset[str]
    is_dev_token: bool = False
    environment: str | None = None
    is_anonymous: bool = field(default=False)


def _parse_token(token: str) -> EvalPrincipal:
    """Parse JWT or dev token. Real signature verification is handled upstream
    (FR-021 requires Entra ID validation in production via Azure SWA)."""

    if token.startswith("dev:"):
        # dev token format: dev:<sub>:<role1,role2>
        if not os.environ.get("EVAL_ALLOW_DEV_TOKENS"):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "dev tokens disabled")
        parts = token.split(":", 2)
        if len(parts) != 3:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid dev token")
        sub = parts[1]
        roles = frozenset(r for r in parts[2].split(",") if r)
        return EvalPrincipal(sub=sub, roles=roles, is_dev_token=True)

    # Production: decode without signature here — gateway verifies
    try:
        import base64
        import json

        seg = token.split(".")[1] + "=="
        payload = json.loads(base64.urlsafe_b64decode(seg))
        sub = payload.get("oid") or payload.get("sub", "")
        roles = frozenset(payload.get("roles", []))
        if not sub:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing sub")
        return EvalPrincipal(sub=sub, roles=roles)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")


async def get_principal(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> EvalPrincipal:
    if not authorization:
        # FR-022a: anonymous access is permitted **only** when both the
        # environment is dev *and* the operator has explicitly opted in via
        # EVAL_ALLOW_ANONYMOUS=1. Any other environment value (or a missing
        # opt-in env var) yields 401 — staging/production behaviour unchanged.
        env_name = os.environ.get("ENVIRONMENT", "").strip().lower()
        anon_flag = os.environ.get("EVAL_ALLOW_ANONYMOUS", "").strip()
        if env_name == "dev" and anon_flag == "1":
            return EvalPrincipal(
                sub=ANONYMOUS_SUB,
                roles=ANONYMOUS_ROLES,
                is_dev_token=True,
                environment="dev",
                is_anonymous=True,
            )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "expected Bearer token")
    return _parse_token(authorization.split(" ", 1)[1])


def _require_roles(allowed: frozenset[str]) -> Callable[..., Awaitable[EvalPrincipal]]:
    async def _dep(p: Annotated[EvalPrincipal, Depends(get_principal)]) -> EvalPrincipal:
        if not (p.roles & allowed):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"requires one of: {sorted(allowed)} (have: {sorted(p.roles)})",
            )
        return p

    return _dep


require_tier2 = _require_roles(TIER_2_ROLES)
require_run_operator = _require_roles(RUN_OPERATOR_ROLES)
require_scorecard_viewer = _require_roles(SCORECARD_VIEWER_ROLES)


def enforce_anonymous_dataset_scope(p: EvalPrincipal, dataset_id: str) -> None:
    """FR-022a (b): anonymous dev principals may only access the synthetic dev dataset.

    Any other ``dataset_id`` (including future real-derived or
    ``sanitised-real``-provenance datasets) MUST be rejected with HTTP 403.
    No-op for non-anonymous principals.
    """

    if p.is_anonymous and dataset_id not in ANONYMOUS_ALLOWED_DATASETS:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            (
                f"anonymous dev principals may not access dataset '{dataset_id}'; "
                f"only synthetic dev datasets are permitted: "
                f"{sorted(ANONYMOUS_ALLOWED_DATASETS)}"
            ),
        )


def audit_metadata(p: EvalPrincipal, **extra: Any) -> dict[str, Any]:
    """Return audit-event metadata, tagging anonymous calls with ``environment=dev``.

    Per FR-022a (a), every audit event emitted on behalf of an anonymous dev
    principal must carry ``environment=dev`` so reviewers can distinguish those
    calls from real Entra-authenticated traffic.
    """

    md: dict[str, Any] = dict(extra)
    if p.is_anonymous:
        md.setdefault("environment", p.environment or "dev")
    return md


__all__ = [
    "EvalPrincipal",
    "audit_metadata",
    "enforce_anonymous_dataset_scope",
    "get_principal",
    "require_run_operator",
    "require_scorecard_viewer",
    "require_tier2",
    "ANONYMOUS_ALLOWED_DATASETS",
    "ANONYMOUS_ROLES",
    "ANONYMOUS_SUB",
    "RUN_OPERATOR_ROLES",
    "SCORECARD_VIEWER_ROLES",
    "TIER_2_ROLES",
]
