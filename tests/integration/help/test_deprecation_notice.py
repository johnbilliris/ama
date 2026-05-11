"""spec-038 T-AA198 — deprecation notice resolution."""

from __future__ import annotations

from app.services.help.deprecation_resolver import resolve_deprecation


def test_replacement_resolved() -> None:
    mapping = {"old-slug": {"replacement": "new-slug", "snapshot_id": "snap-1"}}
    res = resolve_deprecation(deep_link_slug="old-slug", snapshot_id="snap-1", deprecation_map=mapping)
    assert res.kind == "current_replacement"
    assert res.replacement_slug == "new-slug"


def test_withdrawn_no_replacement() -> None:
    mapping = {"gone": {"replacement": None, "snapshot_id": "snap-1"}}
    res = resolve_deprecation(
        deep_link_slug="gone",
        snapshot_id="snap-1",
        deprecation_map=mapping,
        tenant_handoff_destination="mailto:help@ama.gov.au",
    )
    assert res.kind == "withdrawn_no_replacement"
    assert res.replacement_slug is None
    assert res.handoff_destination == "mailto:help@ama.gov.au"


def test_unknown_slug_returns_current() -> None:
    res = resolve_deprecation(deep_link_slug="never-existed", snapshot_id="snap-1", deprecation_map={})
    assert res.kind == "current"
