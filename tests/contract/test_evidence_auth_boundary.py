from __future__ import annotations

from app.auth.rbac_registry import APP_ROLES, is_role_allowed_on_route
from app.middleware.entra_auth import _is_protected as entra_is_protected
from app.middleware.rbac_check import _is_protected as rbac_is_protected


def test_evidence_api_requires_entra_and_rbac_in_production() -> None:
    path = "/api/v1/evidence/kpi-ladder"

    assert entra_is_protected(path)
    assert rbac_is_protected(path)


def test_every_operational_app_role_can_read_evidence() -> None:
    path = "/api/v1/evidence/kpi-ladder"

    denied = sorted(role for role in APP_ROLES if not is_role_allowed_on_route(role, path))
    assert denied == []


def test_evidence_health_remains_anonymous_for_platform_probes() -> None:
    path = "/api/healthz/evidence"

    assert not entra_is_protected(path)
    assert not rbac_is_protected(path)
