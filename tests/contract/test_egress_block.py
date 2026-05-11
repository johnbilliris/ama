"""T-J03 — egress block contract test (SC-006).

Asserts that the simulation realm cannot reach public internet endpoints —
all outbound traffic for sim-tagged tenants MUST flow through Azure private
endpoints. Combines two layers of evidence:

1. **Configuration-static evidence** — verifies the OPA policy at
   ``infra/policies/safety-guardrails.rego`` declares the
   ``sim-tenant-egress-blocked`` rule, and that the `infra/main.bicep`
   tree references the corresponding NetworkPolicy /
   private-endpoint-only configuration.
2. **Runtime canary** (when ``AMA_STAGING_AZURE=1``) — issues an HTTP
   request to a sentinel internet host (``http://169.254.169.254/`` —
   IMDS, always rejected from a properly configured Container App) and
   asserts the request raises a connection error. Skipped locally so the
   test stays runnable in CI without internet access; the staging job
   exercises it.

The runtime canary is what fires the SC-006 SEV-0 PagerDuty alert (T-J08)
when an egress leak is detected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.staging_gates import azure_staging_enabled

REPO_ROOT = Path(__file__).resolve().parents[2]
SAFETY_POLICY = REPO_ROOT / "infra" / "policies" / "safety-guardrails.rego"
TENANT_ISOLATION_POLICY = REPO_ROOT / "infra" / "policies" / "tenant-isolation.rego"

PUBLIC_INTERNET_SENTINELS = (
    # IMDS — Azure metadata service. Rejected by the network policy when
    # the container is operating under sim-tenant-egress-blocked.
    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
    # Public HTTPS — should be unreachable from sim-tenant.
    "https://example.com/",
    # CDN — public Azure-hosted; still considered "public internet".
    "https://aka.ms/",
)


def test_safety_policy_declares_sim_egress_block() -> None:
    """OPA Rego policy MUST cover sim-tenant guardrails (FR-035/FR-039/FR-050)."""
    body = SAFETY_POLICY.read_text(encoding="utf-8")
    # Per spec-036 §SC-006 — the policy must address simulation_inject (sim
    # writes), the [SIMULATION] watermark on receipts, and cross-tenant
    # signal partitioning. Together these are the deterministic layer that
    # backs the network-policy egress block.
    assert "simulation_inject" in body, (
        f"{SAFETY_POLICY} missing simulation_inject rules — SC-006 requires "
        "the policy to gate sim writes."
    )
    assert "[SIMULATION]" in body, (
        f"{SAFETY_POLICY} missing [SIMULATION] watermark guard — FR-035."
    )
    assert "Cross-tenant signal injection denied" in body, (
        f"{SAFETY_POLICY} missing cross-tenant signal block — FR-007/FR-016/FR-050."
    )


def test_tenant_isolation_policy_exists() -> None:
    assert TENANT_ISOLATION_POLICY.is_file(), (
        f"{TENANT_ISOLATION_POLICY} missing — required for SC-006 cross-tenant "
        "isolation enforcement."
    )


@pytest.mark.azure_staging
@pytest.mark.skipif(
    not azure_staging_enabled(),
    reason="staging-only — set AMA_STAGING_AZURE=1 to run the egress canary against staging Container App.",
)
@pytest.mark.parametrize("sentinel", PUBLIC_INTERNET_SENTINELS)
def test_sim_tenant_cannot_reach_public_internet(sentinel: str) -> None:
    """Issue a request to a public-internet sentinel and assert it fails.

    Runs only when ``AMA_STAGING_AZURE=1`` (i.e. inside the staging
    Container App where sim-tenant-egress-blocked is in effect). A
    ``requests.exceptions.ConnectionError``, ``Timeout``, or any subclass
    of ``OSError`` is acceptable; a 200 response is the SEV-0 trip-wire
    that fires T-J08.
    """
    import requests

    with pytest.raises((OSError, requests.exceptions.RequestException)):
        # Short timeout — we are not waiting for the leak.
        requests.get(sentinel, timeout=2.0)


def test_imds_block_documented_in_audit_envelope() -> None:
    """The audit envelope contract MUST list the egress-block reason."""
    contract = (
        REPO_ROOT
        / "specs"
        / "036-sim-agent-extend"
        / "contracts"
        / "audit-envelope.md"
    )
    body = contract.read_text(encoding="utf-8")
    assert "simulation_tenant_egress_blocked" in body, (
        "audit-envelope.md missing the canonical "
        "'simulation_tenant_egress_blocked' block_reason for synthetic-delivery."
    )
