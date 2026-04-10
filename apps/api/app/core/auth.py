from dataclasses import dataclass


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


def extract_principal_from_claims(claims: dict[str, object]) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=str(claims.get("sub", "anonymous")),
        agency_id=str(claims.get("agency_id", "unknown-agency")),
        jurisdiction_ids=tuple(claims.get("jurisdiction_ids", [])),
        roles=tuple(claims.get("roles", [])),
        persona_id=str(claims["persona_id"]) if "persona_id" in claims else None,
    )
