"""Activation-mutex lifespan invariant (spec-035 T014, Clarifications Q8).

Guarantees that the API process refuses to serve traffic if BOTH
``ACTIVATION_SIMULATION`` and ``ACTIVATION_PRODUCTION`` env vars are truthy.
This module enforces the invariant during application startup.

When violation is detected:
1. Append an audit row with ``outcome = activation_mutex_violation`` if
   the ``audit-events`` container can be reached (best-effort; never blocks
   shutdown).
2. Raise ``ActivationMutexViolation`` from the ``lifespan`` startup, which
   FastAPI propagates as a non-zero exit.

Spec-035 follow-up: this lifespan also seeds the in-memory coordination-task
store (`apps/api/app/services/workspace_seed.py`) so the persona workspace
UI surfaces non-empty Assigned-Tasks / Dependencies columns. The seed step
is best-effort and never blocks startup.
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


_TRUTHY = {"1", "true", "yes", "y", "on"}


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


class ActivationMutexViolation(RuntimeError):
    """Both activation guards were truthy at startup — refuses to serve."""


async def _emit_violation_audit(reason: str) -> None:
    """Best-effort audit append. Failures are swallowed; we are mid-startup."""
    try:
        from app.repositories.audit_repository import AuditRepository

        repo = AuditRepository()
        await repo.append(
            {
                "outcome": "activation_mutex_violation",
                "appRole": "system-administrator",
                "personaId": "*",
                "operatorIdentity": "system",
                "route": "/lifespan/startup",
                "requestHash": "n/a",
                "extensionEnvelope": {
                    "code": "activation_mutex_violation",
                    "detail": reason,
                },
            },
            correlation_id=str(uuid.uuid4()),
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to emit activation_mutex_violation audit row")


def assert_activation_mutex() -> None:
    """Raise ``ActivationMutexViolation`` if both guards are truthy."""
    sim = _truthy("ACTIVATION_SIMULATION")
    prod = _truthy("ACTIVATION_PRODUCTION")
    if sim and prod:
        msg = (
            "ACTIVATION_SIMULATION and ACTIVATION_PRODUCTION are mutually exclusive "
            "(Q8 activation mutex). Unset one before starting the API."
        )
        logger.critical(msg)
        raise ActivationMutexViolation(msg)


def _seed_workspace_tasks_safely() -> None:
    """Best-effort coordination-task seeding (spec-035 follow-up).

    Pulled out of the lifespan body so unit tests can monkeypatch it.
    Failures are logged and swallowed — a missing or malformed seed file
    must NEVER prevent the API from starting.
    """
    try:
        from app.services.workspace_seed import seed_workspace_tasks

        count = seed_workspace_tasks()
        logger.info("Lifespan startup: seeded %d coordination tasks", count)
    except Exception:  # noqa: BLE001
        logger.exception("Workspace task seeder failed; continuing startup")


@asynccontextmanager
async def activation_mutex_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """FastAPI ``lifespan`` invariant — refuses to start if both guards are active."""
    try:
        assert_activation_mutex()
    except ActivationMutexViolation as exc:
        await _emit_violation_audit(str(exc))
        raise
    _seed_workspace_tasks_safely()
    yield


def install_activation_mutex(app: FastAPI) -> None:
    """Install the lifespan handler on an existing FastAPI app.

    Use this in test contexts where ``create_app`` already exists and we want
    to layer the invariant in. ``main.create_app`` should pass ``lifespan=
    activation_mutex_lifespan`` directly.
    """
    app.router.lifespan_context = activation_mutex_lifespan
