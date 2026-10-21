from __future__ import annotations

import os
from typing import Any

_DEV_ENVIRONMENTS = frozenset({"local", "dev", "development"})
_DEV_ACCESS_ROLES = (
    "SimulationUser",
    "simulation.admin",
    "simulation.coordinator",
    "system-administrator",
    "admin",
    "operator",
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
    "privacy-officer",
    "compliance-officer",
)


def dev_access_enabled() -> bool:
    environment = (os.environ.get("AMA_ENVIRONMENT") or os.environ.get("ENVIRONMENT") or "").strip().lower()
    return (
        environment in _DEV_ENVIRONMENTS
        and os.environ.get("AMA_ALLOW_ANONYMOUS_DEV_ACCESS", "0").strip() == "1"
        and os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1"
        and os.environ.get("AMA_ENABLE_INCIDENT_MAP_AUTH", "0") != "1"
    )


def dev_access_claims() -> dict[str, Any]:
    return {
        "sub": "dev-user",
        "oid": "dev-user",
        "agency_id": "dev",
        "jurisdiction_ids": [],
        "roles": list(_DEV_ACCESS_ROLES),
        "app_role": "system-administrator",
        "persona_id": "dev-user",
    }
