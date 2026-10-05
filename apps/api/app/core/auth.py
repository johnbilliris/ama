from dataclasses import dataclass

from app.core.dev_access import dev_access_enabled
from fastapi import HTTPException, Request


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    agency_id: str
    jurisdiction_ids: tuple[str, ...]
    roles: tuple[str, ...]
    persona_id: str | None = None

    @property
    def has_simulation_role(self) -> bool:
        return "SimulationUser" in self.roles


def _claim_strings(claims: dict[str, object], name: str) -> tuple[str, ...]:
    value = claims.get(name, [])
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"JWT claim {name!r} must be a list of strings")
    values: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"JWT claim {name!r} must contain only strings")
        values.append(item)
    return tuple(values)


def extract_principal_from_claims(claims: dict[str, object]) -> AuthenticatedPrincipal:
    persona_id = claims.get("persona_id") or claims.get("personaId")
    return AuthenticatedPrincipal(
        subject=str(claims.get("oid") or claims.get("sub") or "anonymous"),
        agency_id=str(claims.get("agency_id", "unknown-agency")),
        jurisdiction_ids=_claim_strings(claims, "jurisdiction_ids"),
        roles=_claim_strings(claims, "roles"),
        persona_id=str(persona_id) if persona_id else None,
    )


def require_authenticated_persona(request: Request, asserted_persona_id: str | None = None) -> str:
    claims = getattr(request.state, "claims", None) or {}
    principal = extract_principal_from_claims(claims)
    if dev_access_enabled():
        return asserted_persona_id or principal.persona_id or "dev-user"
    if principal.subject == "anonymous" or not principal.persona_id:
        raise HTTPException(status_code=401, detail="Authenticated persona claim is required")
    if asserted_persona_id and asserted_persona_id != principal.persona_id:
        raise HTTPException(status_code=403, detail="Body persona id must match authenticated persona")
    return principal.persona_id
