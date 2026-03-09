from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    agency_id: str
    jurisdiction_ids: tuple[str, ...]
    persona_id: str | None = None

    @property
    def scope_key(self) -> str:
        jurisdictions = ".".join(sorted(self.jurisdiction_ids))
        return f"{self.agency_id}:{jurisdictions}"
