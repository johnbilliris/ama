from __future__ import annotations

from enum import StrEnum


class TenantMode(StrEnum):
    live = "live"
    rehearsal = "rehearsal"


def classify_tenant_mode(tenant_id: str | None) -> TenantMode:
    """Classify tenancy mode with an exact-live allowlist.

    Only the exact tenant id ``live`` is treated as live.
    Every other value (including empty or unknown) is rehearsal.
    """

    return TenantMode.live if tenant_id == TenantMode.live.value else TenantMode.rehearsal


def is_live_tenant(tenant_id: str | None) -> bool:
    return classify_tenant_mode(tenant_id) is TenantMode.live


def is_rehearsal_tenant(tenant_id: str | None) -> bool:
    return classify_tenant_mode(tenant_id) is TenantMode.rehearsal
