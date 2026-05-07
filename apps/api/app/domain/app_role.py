"""Closed-set Entra ID AppRole enum (spec-035 Clarifications Q1).

Exactly 11 values: 10 AIIMS-function roles + ``system-administrator``.
Mirrors ``packages/domain/src/app-role.ts``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class AppRole(StrEnum):
    """Closed enumeration of every Entra AppRole the system recognises."""

    INCIDENT_COMMANDER = "incident-commander"
    OPERATIONS_OFFICER = "operations-officer"
    LOGISTICS_OFFICER = "logistics-officer"
    PLANNING_OFFICER = "planning-officer"
    PUBLIC_INFORMATION_OFFICER = "public-information-officer"
    FIELD_COORDINATOR = "field-coordinator"
    OBSERVER_AUDITOR = "observer-auditor"
    RISK_MANAGER = "risk-manager"
    RESILIENCE_PLANNER = "resilience-planner"
    EXECUTIVE_LEADER = "executive-leader"
    SYSTEM_ADMINISTRATOR = "system-administrator"


APP_ROLES: Final[tuple[str, ...]] = tuple(member.value for member in AppRole)
APP_ROLE_COUNT: Final[int] = 11

ADMIN_APP_ROLE: Final[AppRole] = AppRole.SYSTEM_ADMINISTRATOR

AIIMS_FUNCTION_APP_ROLES: Final[tuple[AppRole, ...]] = tuple(
    role for role in AppRole if role is not AppRole.SYSTEM_ADMINISTRATOR
)
