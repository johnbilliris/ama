from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request

GOVERNANCE_WRITE_ROLES = frozenset({"governance_lead", "safety_lead", "system_architect", "system_administrator"})
GOVERNANCE_READ_ROLES = frozenset(
    {
        "governance_lead",
        "safety_lead",
        "system_architect",
        "system_administrator",
        "incident_commander",
        "executive",
        "executive_leader",
        "auditor",
        "observer_auditor",
    }
)

_READ_ROLE_ORDER = (
    "auditor",
    "observer_auditor",
    "incident_commander",
    "executive",
    "executive_leader",
    "governance_lead",
    "safety_lead",
    "system_architect",
    "system_administrator",
)

_WRITE_ROLE_ORDER = (
    "governance_lead",
    "safety_lead",
    "system_architect",
    "system_administrator",
)


@dataclass(frozen=True)
class GovernancePrincipal:
    subject: str
    persona_id: str | None
    agency_id: str
    jurisdiction_ids: tuple[str, ...]
    roles: tuple[str, ...]
    effective_role: str


def _normalise_role(role: str) -> str:
    return role.strip().lower().replace("-", "_")


def _extract_roles(claims: dict[str, Any]) -> tuple[str, ...]:
    raw_roles: list[str] = []

    single_role = claims.get("role")
    if isinstance(single_role, str):
        raw_roles.append(single_role)

    app_role = claims.get("app_role") or claims.get("appRole")
    if isinstance(app_role, str):
        raw_roles.append(app_role)

    list_roles = claims.get("roles")
    if isinstance(list_roles, list):
        raw_roles.extend([str(role) for role in list_roles])

    deduped: list[str] = []
    for role in raw_roles:
        normalised = _normalise_role(role)
        if normalised and normalised not in deduped:
            deduped.append(normalised)
    return tuple(deduped)


def _minimise_subject(subject: str) -> str:
    cleaned = subject.strip()
    if "@" not in cleaned:
        return cleaned
    salt = os.environ.get("AMA_GOVERNANCE_SUBJECT_HASH_SALT", "ama-governance-v1")
    digest = hashlib.sha256(f"{salt}:{cleaned.lower()}".encode()).hexdigest()[:16]
    return f"subject:{digest}"


def _effective_role(roles: tuple[str, ...], allowed_roles: frozenset[str], order: tuple[str, ...]) -> str:
    candidates = [role for role in roles if role in allowed_roles]
    if not candidates:
        raise HTTPException(status_code=403, detail="Insufficient permissions for governance operation.")
    for role in order:
        if role in candidates:
            return role
    return sorted(candidates)[0]


def require_governance_read(request: Request) -> GovernancePrincipal:
    claims: dict[str, Any] = getattr(request.state, "claims", None) or {}
    subject = str(claims.get("sub", "")).strip()
    if not subject or subject.lower() == "anonymous":
        raise HTTPException(status_code=401, detail="Authenticated governance principal is required.")

    roles = _extract_roles(claims)
    effective_role = _effective_role(roles, GOVERNANCE_READ_ROLES, _READ_ROLE_ORDER)

    jurisdiction_ids = tuple(str(item) for item in claims.get("jurisdiction_ids", []) if isinstance(item, str))
    persona_id = claims.get("persona_id") or claims.get("personaId")

    return GovernancePrincipal(
        subject=_minimise_subject(subject),
        persona_id=str(persona_id) if persona_id else None,
        agency_id=str(claims.get("agency_id", "unknown-agency")),
        jurisdiction_ids=jurisdiction_ids,
        roles=roles,
        effective_role=effective_role,
    )


def require_governance_write(
    principal: GovernancePrincipal = Depends(require_governance_read),
) -> GovernancePrincipal:
    effective_role = _effective_role(principal.roles, GOVERNANCE_WRITE_ROLES, _WRITE_ROLE_ORDER)
    if effective_role != principal.effective_role:
        return GovernancePrincipal(
            subject=principal.subject,
            persona_id=principal.persona_id,
            agency_id=principal.agency_id,
            jurisdiction_ids=principal.jurisdiction_ids,
            roles=principal.roles,
            effective_role=effective_role,
        )
    return principal
