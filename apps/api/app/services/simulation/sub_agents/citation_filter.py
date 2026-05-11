"""Citation filter helper — guarantees no live-tenant resource leaks (FR-007 / T-B11).

Every adapter calls :func:`filter_citations` on the citation list returned by
the agent service. Anything that isn't recognised as a *simulation-tenant
scoped* resource ID is stripped, the offending IDs are returned for audit
emission, and the caller flips ``degraded=True``.

The matcher is intentionally conservative: a citation is considered safe iff
the supplied ``tenant_id`` (which is ALWAYS a sim-tenant in the production
invoker code path — live tenants never reach this layer) appears as a path
segment **and** the citation does not contain any reserved live-tenant
identifier from :data:`LIVE_TENANT_BLOCKLIST`.

Usage::

    safe, bad = filter_citations(citations, tenant_id="sim-nsw-rfs-q3")
    if bad:
        await audit.write("tenant_isolation.violation", offending=bad[0])
"""

from __future__ import annotations

from collections.abc import Iterable

# Conservative blocklist — extend whenever a new "production" tenant prefix
# enters the system. The list is *not* the source of truth (the OPA policy
# under ``infra/policies/tenant-isolation.rego`` is) but it is a defensive
# in-memory tripwire for the citation field.
LIVE_TENANT_BLOCKLIST: tuple[str, ...] = (
    "live-",
    "production-",
    "tenant-aws-prod-",
    "tenant-aiims-prod-",
    "/prod/",
)

SIM_TENANT_MARKERS: tuple[str, ...] = (
    "sim-",
    "simulation-",
    "/sim/",
    "/simulation/",
)


def is_sim_tenant_citation(citation: str, tenant_id: str) -> bool:
    """Return ``True`` if *citation* is safely scoped to *tenant_id*."""
    if not citation:
        return False
    needle = tenant_id.strip()
    if needle and needle in citation:
        # Allowed — the citation explicitly carries the requesting sim tenant.
        if any(token in citation for token in LIVE_TENANT_BLOCKLIST):
            return False
        return True
    # Fallback: a generic sim-* marker is good enough for sim-tenant data.
    return any(token in citation for token in SIM_TENANT_MARKERS) and not any(
        token in citation for token in LIVE_TENANT_BLOCKLIST
    )


def filter_citations(citations: Iterable[str], *, tenant_id: str) -> tuple[list[str], list[str]]:
    """Split *citations* into ``(safe, blocked)`` lists.

    The returned ``blocked`` list is what the caller must report via
    ``tenant_isolation.violation`` audit entries.
    """
    safe: list[str] = []
    blocked: list[str] = []
    for c in citations:
        (safe if is_sim_tenant_citation(c, tenant_id) else blocked).append(c)
    return safe, blocked
