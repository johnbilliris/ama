"""T-G01 — jurisdiction boundary service integration test."""

from __future__ import annotations

import time
from pathlib import Path

from apps.api.app.services.simulation.jurisdiction_boundary_service import (
    JurisdictionBoundaryService,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "jurisdiction_boundaries"


def _fixture_service() -> JurisdictionBoundaryService:
    svc = JurisdictionBoundaryService()
    svc.load_from_directory(FIXTURE_ROOT, dataset_version="fixture-v1")
    assert svc.metrics.polygons_loaded >= 2, "Fixture must commit at least 2 polygons (ACT + NSW + VIC)"
    return svc


def test_loader_reads_wkt_and_geojson_fixtures() -> None:
    svc = _fixture_service()
    codes = sorted({p.code for p in svc.polygons})
    assert codes == sorted(["ACT", "NSW", "VIC"])


def test_infer_resolves_canberra_to_act() -> None:
    """Canberra (-35.30, 149.13) lies in the ACT polygon."""
    svc = _fixture_service()
    assert svc.infer(-35.30, 149.13) == "ACT"


def test_infer_resolves_sydney_to_nsw() -> None:
    """Sydney (-33.87, 151.21) lies in the NSW polygon (outside ACT)."""
    svc = _fixture_service()
    assert svc.infer(-33.87, 151.21) == "NSW"


def test_infer_resolves_melbourne_to_vic() -> None:
    """Melbourne (-37.81, 144.96) → VIC (geojson fixture)."""
    svc = _fixture_service()
    assert svc.infer(-37.81, 144.96) == "VIC"


def test_infer_returns_none_for_offshore_point() -> None:
    """A point in the Pacific (-30, 170) MUST NOT match any AU polygon."""
    svc = _fixture_service()
    assert svc.infer(-30.0, 170.0) is None


def test_lookup_p95_under_50ms_for_10k_points() -> None:
    """FR-021: 10K-point benchmark p95 < 50 ms."""
    svc = _fixture_service()
    samples: list[float] = []
    for i in range(10_000):
        # Walk a deterministic raster across AU-mainland latitudes.
        lat = -28.0 - (i % 100) * 0.05
        lng = 142.0 + (i // 100) * 0.001
        start = time.perf_counter()
        svc.infer(lat, lng)
        samples.append(time.perf_counter() - start)
    samples.sort()
    p95 = samples[int(0.95 * len(samples)) - 1]
    assert p95 < 0.05, f"p95 {p95 * 1000:.2f} ms — must be < 50 ms"


def test_metrics_capture_dataset_version() -> None:
    svc = _fixture_service()
    assert svc.metrics.dataset_version == "fixture-v1"
    assert svc.metrics.last_loaded_at > 0
