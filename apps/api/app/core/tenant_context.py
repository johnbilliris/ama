from contextvars import ContextVar, Token
from dataclasses import dataclass

from packages.domain.src.domain.tenant_mode import is_live_tenant


@dataclass(frozen=True)
class TenantContext:
    agency_id: str
    jurisdiction_ids: tuple[str, ...]
    persona_id: str | None = None
    tenant_id: str = "live"

    @property
    def is_simulation(self) -> bool:
        return not is_live_tenant(self.tenant_id)

    @property
    def scope_key(self) -> str:
        jurisdictions = ".".join(sorted(self.jurisdiction_ids))
        return f"{self.tenant_id}:{self.agency_id}:{jurisdictions}"


_tenant_context_var: ContextVar[TenantContext] = ContextVar("tenant_context")


def get_current_tenant() -> TenantContext:
    return _tenant_context_var.get()


def set_current_tenant(ctx: TenantContext) -> Token[TenantContext]:
    return _tenant_context_var.set(ctx)


def reset_current_tenant(token: Token[TenantContext]) -> None:
    _tenant_context_var.reset(token)
