"""T-B11: citation filter unit tests (FR-007)."""

from __future__ import annotations

from apps.api.app.services.simulation.sub_agents.citation_filter import (
    filter_citations,
    is_sim_tenant_citation,
)


def test_sim_tenant_marker_pass() -> None:
    assert is_sim_tenant_citation("/sim/foo/bar", "sim-tenant-a")
    assert is_sim_tenant_citation("sim-tenant-a/doc/123", "sim-tenant-a")


def test_live_tenant_blocked() -> None:
    assert not is_sim_tenant_citation("/prod/secret/data", "sim-tenant-a")
    assert not is_sim_tenant_citation("live-tenant-x/doc", "sim-tenant-a")


def test_filter_citations_split() -> None:
    safe, bad = filter_citations(
        [
            "/sim/x/1",
            "live-tenant-x/y",
            "sim-tenant-a/doc/1",
            "tenant-aws-prod-vic/doc",
        ],
        tenant_id="sim-tenant-a",
    )
    assert "/sim/x/1" in safe
    assert "sim-tenant-a/doc/1" in safe
    assert "live-tenant-x/y" in bad
    assert "tenant-aws-prod-vic/doc" in bad


def test_empty_citation_blocked() -> None:
    assert not is_sim_tenant_citation("", "sim-tenant-a")
