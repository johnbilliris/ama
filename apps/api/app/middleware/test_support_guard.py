"""Dual-guard middleware for the test-support endpoint (spec 034).

Activates the test-support API surface only when **both** of these hold:

1. ``os.environ.get("AMA_TEST_SUPPORT") == "1"`` (explicit operator opt-in).
2. ``settings.environment in {"dev", "test"}`` (never in staging or production).

Refusing either guard means the router is **not registered** in
``apps/api/app/main.py``; direct requests collapse to a stock FastAPI 404.
A structured log line is emitted at startup so deployments can prove the
guard fired.

Contract: ``specs/034-webapp-capstone-coverage/contracts/persona-fixture.contract.md``
sections "Activation" and "Acceptance criteria for this contract".
"""

from __future__ import annotations

import logging
import os
from typing import Final

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

_ENV_VAR: Final[str] = "AMA_TEST_SUPPORT"
_ALLOWED_ENVIRONMENTS: Final[frozenset[str]] = frozenset({"dev", "test"})


def is_enabled() -> bool:
    """Return ``True`` only if both activation guards are satisfied."""

    settings = get_settings()
    env_flag = os.environ.get(_ENV_VAR, "")
    environment = getattr(settings, "environment", "production")
    return env_flag == "1" and environment in _ALLOWED_ENVIRONMENTS


def log_activation_status() -> None:
    """Emit a single, structured startup log line documenting the guard."""

    settings = get_settings()
    environment = getattr(settings, "environment", "production")
    env_flag_present = "1" if os.environ.get(_ENV_VAR) == "1" else "0"

    if is_enabled():
        logger.warning(
            "test-support enabled: environment=%s AMA_TEST_SUPPORT=%s",
            environment,
            env_flag_present,
        )
    else:
        logger.info(
            "test-support disabled: environment=%s AMA_TEST_SUPPORT=%s",
            environment,
            env_flag_present,
        )
