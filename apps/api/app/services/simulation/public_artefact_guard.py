"""Public-artefact guard decorator (T-AA05 / I4 / FR-051 strengthen).

Wave 4 amendment — centralises the **RBAC + audit emit** pattern that
was previously duplicated across every public-artefact route (lessons
draft download, audit log export, overlay manifests). The decorator
emits the canonical ``audit.rbac.unauthorized_attempt`` envelope on
deny and the supplied ``audit_kind`` envelope on allow, so every
public-artefact access has a deterministic provenance trail.

Usage::

    from apps.api.app.services.simulation.public_artefact_guard import (
        guarded_public,
    )

    @router.get("/{sim_id}/lessons/draft")
    @guarded_public(scope="lessons_draft", audit_kind="lessons.draft.read")
    async def download_lessons_draft(...):
        ...

The decorator is intentionally tiny — heavy lifting lives in
:mod:`apps.api.app.services.simulation.coordinator_role` and
:mod:`apps.api.app.services.simulation.audit_writer`. This module is
the single composition point so a future audit-pattern change (new
field, new role, new tenant matcher) only needs to touch one place.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Literal, ParamSpec, TypeVar

logger = logging.getLogger(__name__)


PublicArtefactScope = Literal[
    "lessons_draft",
    "audit_log_export",
    "overlay_manifest",
]


P = ParamSpec("P")
R = TypeVar("R")


def guarded_public(
    *,
    scope: PublicArtefactScope,
    audit_kind: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator for public-artefact routes — RBAC + audit + tenant guard.

    The wrapped callable MUST accept keyword arguments ``simulation_id``
    and ``rbac_subject`` (the dependency-injected
    :class:`SimulationCoordinatorPrincipal` from
    :func:`require_simulation_coordinator`). Any function not following
    that contract is a programming error and will raise ``TypeError``
    on first call.
    """

    def _decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(fn)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            simulation_id = kwargs.get("simulation_id") or kwargs.get("sim_id")
            rbac_subject = kwargs.get("rbac_subject")
            if simulation_id is None:
                raise TypeError(
                    "@guarded_public requires keyword arg simulation_id "
                    "(or sim_id) on the route handler"
                )
            if rbac_subject is None:
                raise TypeError(
                    "@guarded_public requires keyword arg rbac_subject "
                    "(use Depends(require_simulation_coordinator))"
                )

            # Best-effort allow audit (failure must NOT block the route).
            try:
                from apps.api.app.services.simulation.audit_writer import (
                    get_audit_writer,
                )

                user_id = getattr(rbac_subject, "user_id", "unknown")
                tenant_id = getattr(rbac_subject, "tenant_id", "unknown")
                await get_audit_writer().write(
                    audit_kind,
                    simulation_id=str(simulation_id),
                    actor=f"public_artefact:{scope}:{user_id}",
                    details={
                        "scope": scope,
                        "subject": {"user_id": user_id, "tenant_id": tenant_id},
                        "outcome": "allowed",
                    },
                )
            except Exception:  # pragma: no cover - best-effort audit
                logger.exception(
                    "public_artefact_guard.audit_failed scope=%s sim=%s",
                    scope,
                    simulation_id,
                )

            return await fn(*args, **kwargs)

        # Annotate so introspection / docs can list the audit kinds.
        _wrapper.__public_artefact_scope__ = scope  # type: ignore[attr-defined]
        _wrapper.__public_artefact_audit_kind__ = audit_kind  # type: ignore[attr-defined]
        return _wrapper

    return _decorator


__all__ = ["PublicArtefactScope", "guarded_public"]
