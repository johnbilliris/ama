"""Spec-038 / T-A02 — KPI ladder versioning preserves prior versions."""

from __future__ import annotations

from app.services.evidence._clients import reset_registry
from app.services.evidence.kpi_ladder.repository import (
    get_by_id,
    latest_version_for,
    list_published,
    publish,
)
from app.services.evidence.kpi_ladder.seed import _make


def test_publish_supersedes_prior_version():
    reset_registry()
    v1 = _make(kpi_id="resp_p1", name="resp v1", kind="lagging", sc="SC-CAP-015-002")
    publish(v1)
    assert latest_version_for("resp_p1") == 1

    v2 = _make(kpi_id="resp_p1", name="resp v2", kind="lagging", sc="SC-CAP-015-002")
    v2 = v2.model_copy(update={"version": 2})
    publish(v2)
    assert latest_version_for("resp_p1") == 2

    # Prior remains retrievable by id.
    prior = get_by_id(v1.id)
    assert prior is not None
    assert prior.superseded_by == v2.id

    # Latest list shows only the new version.
    latest = list_published()
    kpis = [i.kpi_id for i in latest]
    assert kpis.count("resp_p1") == 1
