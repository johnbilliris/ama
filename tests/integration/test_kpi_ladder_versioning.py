# Atomic KPI ladder versioning and historical retrieval tests.

from __future__ import annotations

import pytest
from app.services.evidence._clients import get_registry, reset_registry
from app.services.evidence.kpi_ladder.repository import (
    VersionMonotonicityError,
    get_by_id,
    get_version,
    latest_version_for,
    list_published,
    list_versions,
    publish,
)
from app.services.evidence.kpi_ladder.seed import _make


def _indicator(version: int, name: str):
    indicator = _make(kpi_id="resp_p1", name=name, kind="lagging", sc="SC-CAP-015-002")
    return indicator.model_copy(update={"version": version})


def test_publish_supersedes_prior_but_preserves_every_version():
    reset_registry()
    first = _indicator(1, "response v1")
    second = _indicator(2, "response v2")
    third = _indicator(3, "response v3")
    publish(first)
    publish(second)
    publish(third)

    assert latest_version_for("resp_p1") == 3
    assert [row.version for row in list_versions("resp_p1")] == [1, 2, 3]
    assert get_version("resp_p1", 1).id == first.id
    assert get_by_id(first.id).superseded_by == second.id
    assert get_by_id(second.id).superseded_by == third.id
    latest = [row for row in list_published() if row.kpi_id == "resp_p1"]
    assert [row.id for row in latest] == [third.id]


def test_failed_replacement_is_atomic_in_memory(monkeypatch):
    reset_registry()
    first = _indicator(1, "response v1")
    second = _indicator(2, "response v2")
    publish(first)
    container = get_registry().get("kpi_ladder")

    def fail_batch(replacements, created):
        raise RuntimeError("synthetic test replacement failure")

    monkeypatch.setattr(container, "replace_and_create", fail_batch)
    with pytest.raises(RuntimeError, match="synthetic test replacement failure"):
        publish(second)

    current = [row for row in list_published() if row.kpi_id == "resp_p1"]
    assert [row.id for row in current] == [first.id]
    assert get_by_id(first.id).superseded_by is None
    assert get_by_id(second.id) is None


def test_equal_or_older_versions_are_rejected():
    reset_registry()
    publish(_indicator(1, "response v1"))
    with pytest.raises(VersionMonotonicityError):
        publish(_indicator(1, "racing response v1"))
