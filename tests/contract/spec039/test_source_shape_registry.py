"""Spec-039 T017: contract test for the source-shape registry (FR-020, FR-027)."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY = REPO_ROOT / "apps" / "api" / "app" / "services" / "simulation" / "feeds" / "source_shapes.json"
SHAPE_ID_RE = re.compile(r"^[a-z0-9_.-]+\.v\d+$")
EXPECTED_FAMILIES = {
    "bom",
    "ga",
    "epa",
    "traffic",
    "utility",
    "ambulance",
    "social",
    "sensor",
    "synthetic",
}
# 13 shapes per plan §"P3 simulator" / tasks T080–T092.
EXPECTED_COUNT = 13


def _load() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_exists_and_parses():
    doc = _load()
    assert "shapes" in doc
    assert doc.get("schema_version") == "1.0.0"


def test_registry_has_thirteen_shapes():
    doc = _load()
    assert len(doc["shapes"]) == EXPECTED_COUNT, (
        f"FR-020/T017: expected {EXPECTED_COUNT} shapes, got {len(doc['shapes'])}"
    )


def test_each_shape_id_matches_versioned_pattern():
    doc = _load()
    for shape in doc["shapes"]:
        sid = shape["id"]
        assert SHAPE_ID_RE.match(sid), f"shape id {sid!r} does not match pattern"


def test_shape_ids_are_unique():
    doc = _load()
    ids = [s["id"] for s in doc["shapes"]]
    assert len(ids) == len(set(ids))


def test_all_expected_families_present():
    doc = _load()
    families = {s["family"] for s in doc["shapes"]}
    missing = EXPECTED_FAMILIES - families
    assert not missing, f"missing source-shape families: {missing}"


def test_warning_shapes_match_simulator_feed_schema_pattern():
    """FR-046 — warning-class shapes must be the three the schema expects:
    bom.severe_weather_warning, bom.cyclone_track, ga.tsunami_threat."""
    doc = _load()
    warnings = {s["id"] for s in doc["shapes"] if s.get("kind") == "warning"}
    assert warnings == {
        "bom.severe_weather_warning.v1",
        "bom.cyclone_track.v1",
        "ga.tsunami_threat.v1",
    }
