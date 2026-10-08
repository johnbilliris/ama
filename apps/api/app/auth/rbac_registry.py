"""Static AppRole + persona-scope registry for spec-035 RBAC (T024b).

11 closed-set AppRoles per
[`spec.md` § FR-011](../../../../specs/035-webapp-capstone-closure/spec.md#functional-requirements):

- 10 AIIMS operational roles + 1 ``system-administrator``.

Each role maps to (a) a set of route-family prefixes it may invoke and
(b) a set of AIIMS-functions whose personas the role may scope to.

Mapping deliberately lives in code (not config) because it is a regulatory
closed set per ASM-013; deviations require a new release.
"""

from __future__ import annotations

from typing import Final

# Closed set of 11 AppRoles (10 AIIMS + 1 admin). FR-011.
APP_ROLES: Final[frozenset[str]] = frozenset(
    {
        "incident-commander",
        "planning-officer",
        "operations-officer",
        "logistics-officer",
        "public-information-officer",
        "field-coordinator",
        "observer-auditor",
        "risk-manager",
        "resilience-planner",
        "executive-leader",
        "system-administrator",
    }
)


# AppRole → AIIMS functions a caller's persona may belong to. ``system-administrator``
# inherits the impersonation target's function set when ``X-Impersonate-Persona`` is
# present (handled in the middleware).
ROLE_TO_AIIMS_FUNCTIONS: Final[dict[str, frozenset[str]]] = {
    "incident-commander": frozenset({"control"}),
    "planning-officer": frozenset({"planning"}),
    "operations-officer": frozenset({"operations"}),
    "logistics-officer": frozenset({"logistics"}),
    "public-information-officer": frozenset({"public-information"}),
    "field-coordinator": frozenset({"operations"}),
    "observer-auditor": frozenset({"control", "planning", "operations", "logistics", "public-information"}),
    "risk-manager": frozenset({"planning"}),
    "resilience-planner": frozenset({"planning"}),
    "executive-leader": frozenset({"control"}),
    "system-administrator": frozenset(),
}


# Route-family allowlist per AppRole. Path prefixes; longest-match wins.
# Every operational AppRole can hit /api/auth/whoami and /api/audit/list.
_COMMON_PREFIXES: frozenset[str] = frozenset(
    {
        "/api/auth/whoami",
        "/api/audit/list",
        "/api/incidents/",
        "/api/v1/evidence",
    }
)


_ROUTE_FAMILY_ALLOWLIST: Final[dict[str, frozenset[str]]] = {
    "incident-commander": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/data-sources",
            "/api/governance",
            "/api/recommendations/",
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-002/evaluate",
            "/api/outcomes/sc-003/evaluate",
            "/api/outcomes/sc-004/evaluate",
            "/api/outcomes/sc-005/evaluate",
            "/api/alerts/",
            "/api/recovery/handover",
            "/api/offline/replay",
        }
    ),
    "planning-officer": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/recommendations/",
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-002/evaluate",
            "/api/offline/replay",
        }
    ),
    "operations-officer": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/recommendations/",
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-002/evaluate",
            "/api/outcomes/sc-003/evaluate",
            "/api/offline/replay",
        }
    ),
    "logistics-officer": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/outcomes/sc-003/evaluate",
            "/api/outcomes/sc-004/evaluate",
            "/api/offline/replay",
        }
    ),
    "public-information-officer": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/outcomes/sc-002/evaluate",
            "/api/alerts/",
            "/api/offline/replay",
        }
    ),
    "field-coordinator": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-003/evaluate",
            "/api/offline/replay",
        }
    ),
    "observer-auditor": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/data-sources",
            "/api/governance",
        }
    ),
    "risk-manager": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-004/evaluate",
        }
    ),
    "resilience-planner": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/outcomes/sc-005/evaluate",
            "/api/recovery/handover",
            "/api/incidents/",
        }
    ),
    "executive-leader": _COMMON_PREFIXES
    | frozenset(
        {
            "/api/data-sources",
            "/api/governance",
            "/api/alerts/",
            "/api/recommendations/",
            "/api/outcomes/sc-001/evaluate",
            "/api/outcomes/sc-005/evaluate",
        }
    ),
    "system-administrator": frozenset(
        {
            "/api/data-sources",
            "/api/governance",
            "/api/alerts/",
            "/api/recommendations/",
            "/api/outcomes/",
            "/api/audit/list",
            "/api/auth/whoami",
            "/api/incidents/",
            "/api/offline/replay",
            "/api/recovery/handover",
            "/api/v1/evidence",
        }
    ),
}


def is_role_allowed_on_route(role: str, path: str) -> bool:
    """Return True iff ``role`` may invoke ``path``."""
    allowed = _ROUTE_FAMILY_ALLOWLIST.get(role)
    if allowed is None:
        return False
    return any(path == prefix or path.startswith(prefix) for prefix in allowed)


__all__ = [
    "APP_ROLES",
    "ROLE_TO_AIIMS_FUNCTIONS",
    "is_role_allowed_on_route",
]
