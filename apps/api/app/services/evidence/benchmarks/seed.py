"""Pillar E — Benchmark register seed (T-E06, FR-020, SC-007)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from ..models.benchmark import BenchmarkEntry

# Subset of FR-020 enumeration — sufficient for SC-007 coverage:
# every kpi_id in the seeded ladder gets ≥1 entry.
SEEDS: list[dict] = [
    # response_time_p1 — eight jurisdictions for ambulance Pri-1 (FR-020)
    *[
        {
            "kpi_id": "response_time_p1",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} Ambulance Pri-1 median",
            "source_citation": f"https://benchmarks.example/{j.lower()}",
            "target": Decimal("480.0000"),
            "unit": "seconds",
            "not_available": False,
        }
        for j in ("NSW", "VIC", "QLD", "SA", "WA", "ACT", "NT", "TAS")
    ],
    # response_time_p1 — prototype baseline for AU
    {
        "kpi_id": "response_time_p1",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("600.0000"),
        "unit": "seconds",
        "not_available": False,
    },
    # evac_lead_lagging — BoM warning lead-time
    {
        "kpi_id": "evac_lead_lagging",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "BoM hazard warning lead-time",
        "source_citation": "https://www.bom.gov.au/",
        "target": Decimal("18.0000"),
        "unit": "hours",
        "not_available": False,
    },
    {
        "kpi_id": "evac_lead_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("12.0000"),
        "unit": "hours",
        "not_available": False,
    },
    # logistics_efficiency — AIIMS span-of-control proxy
    {
        "kpi_id": "logistics_efficiency",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "AIIMS span-of-control 1:5..1:7",
        "source_citation": "AIIMS-2017",
        "target": None,
        "unit": "ratio",
        "not_available": True,
    },
    {
        "kpi_id": "logistics_efficiency",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("10.0000"),
        "unit": "pct",
        "not_available": False,
    },
    # lives_saved_lagging — AFAC FDI/FFDI proxy
    {
        "kpi_id": "lives_saved_lagging",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "AFAC FDI/FFDI severity index",
        "source_citation": "https://www.afac.com.au/",
        "target": None,
        "unit": "lives",
        "not_available": True,
    },
    {
        "kpi_id": "lives_saved_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("50.0000"),
        "unit": "lives",
        "not_available": False,
    },
    # econ_loss_lagging
    {
        "kpi_id": "econ_loss_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("10.0000"),
        "unit": "AUDm",
        "not_available": False,
    },
    # leading-indicator coverage rows
    {
        "kpi_id": "lives_saved_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("80.0000"),
        "unit": "pct",
        "not_available": False,
    },
    {
        "kpi_id": "response_time_p1_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("120.0000"),
        "unit": "seconds",
        "not_available": False,
    },
    {
        "kpi_id": "evac_warning_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("18.0000"),
        "unit": "hours",
        "not_available": False,
    },
    {
        "kpi_id": "logistics_route_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("70.0000"),
        "unit": "pct",
        "not_available": False,
    },
    {
        "kpi_id": "econ_loss_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("15.0000"),
        "unit": "pct",
        "not_available": False,
    },
    # Public Information KPI rows (US7)
    {
        "kpi_id": "public_info_alert_reach",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("85.0000"),
        "unit": "pct",
        "not_available": False,
    },
    {
        "kpi_id": "public_info_behavioural_impact",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("60.0000"),
        "unit": "pct",
        "not_available": False,
    },
    {
        "kpi_id": "public_info_multilingual_coverage",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "source_citation": "specs/015-capstone-success-criteria/spec.md",
        "target": Decimal("8.0000"),
        "unit": "languages",
        "not_available": False,
    },
]


def seed_register() -> list[BenchmarkEntry]:
    out: list[BenchmarkEntry] = []
    for s in SEEDS:
        out.append(
            BenchmarkEntry(
                id=secrets.token_hex(13),
                kpi_id=s["kpi_id"],
                jurisdiction=s["jurisdiction"],
                kind=s["kind"],
                source_name=s["source_name"],
                source_citation=s["source_citation"],
                target_value=s["target"],
                target_unit=s["unit"],
                not_available=s["not_available"],
                created_at=datetime.now(UTC),
            )
        )
    return out
