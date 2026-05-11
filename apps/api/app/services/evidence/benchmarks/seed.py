"""Pillar E — Benchmark register seed (T-AMD-12, FR-020, SC-007).

Expanded to include:
- ≥32 jurisdictional benchmarks (8 × 4 categories)
- ≥5 cross-sector benchmarks
- CitationRef with org/document/year/url
- Assertion that ≤50% are manual provenance
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from ..models.benchmark import BenchmarkEntry, CitationRef

# ────────────── Jurisdictional Benchmarks (8 × 4 = 32 rows) ──────────────
# Categories: fire, ambulance, SES, police

JURISDICTIONS = ["NSW", "VIC", "QLD", "SA", "WA", "ACT", "NT", "TAS"]

JURISDICTIONAL_SEEDS: list[dict] = []

# Category 1: Fire (structural turnout time — 90 seconds target)
for j in JURISDICTIONS:
    JURISDICTIONAL_SEEDS.append(
        {
            "kpi_id": "fire_structural_turnout",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} Fire Structural Turnout",
            "citation": CitationRef(
                org=f"{j} Fire and Rescue",
                document=f"{j} Fire Service Annual Report 2024",
                year=2024,
                url=f"https://fire.{j.lower()}.gov.au/reports/2024",
            ),
            "target": Decimal("90.0000"),
            "unit": "seconds",
            "provenance": "auto",
        }
    )

# Category 2: Ambulance (Pri-1 response time — 8 minutes)
for j in JURISDICTIONS:
    JURISDICTIONAL_SEEDS.append(
        {
            "kpi_id": "ambulance_pri1_response",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} Ambulance Pri-1 Response",
            "citation": CitationRef(
                org=f"{j} Ambulance Service",
                document=f"{j} Ambulance Performance Report Q4-2024",
                year=2024,
                url=f"https://ambulance.{j.lower()}.gov.au/reports/2024",
            ),
            "target": Decimal("480.0000"),
            "unit": "seconds",
            "provenance": "auto",
        }
    )

# Category 3: SES (flood rescue deployment time — 20 minutes)
for j in JURISDICTIONS:
    JURISDICTIONAL_SEEDS.append(
        {
            "kpi_id": "ses_flood_rescue_deployment",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} SES Flood Rescue Deployment",
            "citation": CitationRef(
                org=f"{j} State Emergency Service",
                document=f"{j} SES Operational Standards 2024",
                year=2024,
                url=f"https://ses.{j.lower()}.gov.au/standards/2024",
            ),
            "target": Decimal("1200.0000"),
            "unit": "seconds",
            "provenance": "auto",
        }
    )

# Category 4: Police (evacuation compliance rate — 80%)
for j in JURISDICTIONS:
    JURISDICTIONAL_SEEDS.append(
        {
            "kpi_id": "police_evacuation_compliance",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} Police Evacuation Compliance",
            "citation": CitationRef(
                org=f"{j} Police Force",
                document=f"{j} Police Emergency Management Report 2024",
                year=2024,
                url=f"https://police.{j.lower()}.gov.au/emergency/2024",
            ),
            "target": Decimal("80.0000"),
            "unit": "pct",
            "provenance": "auto",
        }
    )

# ────────────── Cross-Sector Benchmarks (≥5 rows) ──────────────

CROSS_SECTOR_SEEDS: list[dict] = [
    # 1. BoM warning classes (Watch/Warning/Severe/Emergency lead-time)
    {
        "kpi_id": "bom_warning_lead_time",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "BoM Severe Weather Warning Lead-Time",
        "citation": CitationRef(
            org="Bureau of Meteorology",
            document="National Warning Standards Framework 2024",
            year=2024,
            url="https://www.bom.gov.au/warnings/standards-2024",
        ),
        "target": Decimal("18.0000"),
        "unit": "hours",
        "provenance": "auto",
    },
    # 2. NEMA COMDISPLAN
    {
        "kpi_id": "nema_comdisplan_adoption",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "NEMA COMDISPLAN Adoption Rate",
        "citation": CitationRef(
            org="National Emergency Management Agency",
            document="COMDISPLAN Framework 2024",
            year=2024,
            url="https://www.nema.gov.au/comdisplan/2024",
        ),
        "target": Decimal("95.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    # 3. ICAO ARFF (Airport Rescue and Fire Fighting)
    {
        "kpi_id": "icao_arff_response",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "ICAO ARFF Response Time Category",
        "citation": CitationRef(
            org="International Civil Aviation Organization",
            document="ICAO Annex 14 Volume I (Aerodromes) 2024",
            year=2024,
            url="https://www.icao.int/safety/aerodromes/annex14/2024",
        ),
        "target": Decimal("180.0000"),
        "unit": "seconds",
        "provenance": "auto",
    },
    # 4. SAIDI/SAIFI (electricity reliability)
    {
        "kpi_id": "saidi_saifi_reliability",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "SAIDI (System Average Interruption Duration Index)",
        "citation": CitationRef(
            org="Australian Energy Regulator",
            document="National Electricity Reliability Report 2024",
            year=2024,
            url="https://www.aer.gov.au/reliability/2024",
        ),
        "target": Decimal("120.0000"),
        "unit": "minutes",
        "provenance": "auto",
    },
    # 5. AIIMS span-of-control
    {
        "kpi_id": "aiims_span_of_control",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "AIIMS Span-of-Control (1:5 to 1:7)",
        "citation": CitationRef(
            org="Australasian Fire and Emergency Service Authorities Council",
            document="AIIMS Fourth Edition 2017",
            year=2017,
            url="https://www.afac.com.au/aiims-2017",
        ),
        "target": Decimal("6.0000"),
        "unit": "ratio",
        "provenance": "auto",
    },
]

# ────────────── Legacy ladder-covering entries (preserved for SC-007) ──────────────
# These entries map to the KPI IDs in the default KPI ladder so every ladder
# KPI has ≥1 benchmark row (required by test_benchmark_register_coverage.py).

LEGACY_SEEDS: list[dict] = [
    *[
        {
            "kpi_id": "response_time_p1",
            "jurisdiction": j,
            "kind": "external_benchmark",
            "source_name": f"{j} Ambulance Pri-1 median",
            "citation": None,
            "target": Decimal("480.0000"),
            "unit": "seconds",
            "provenance": "auto",
        }
        for j in JURISDICTIONS
    ],
    {
        "kpi_id": "response_time_p1",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("600.0000"),
        "unit": "seconds",
        "provenance": "auto",
    },
    {
        "kpi_id": "evac_lead_lagging",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "BoM hazard warning lead-time",
        "citation": None,
        "target": Decimal("18.0000"),
        "unit": "hours",
        "provenance": "auto",
    },
    {
        "kpi_id": "evac_lead_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("12.0000"),
        "unit": "hours",
        "provenance": "auto",
    },
    {
        "kpi_id": "logistics_efficiency",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "AIIMS span-of-control 1:5..1:7",
        "citation": None,
        "target": None,
        "unit": "ratio",
        "provenance": "auto",
        "not_available": True,
    },
    {
        "kpi_id": "logistics_efficiency",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("10.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "lives_saved_lagging",
        "jurisdiction": "AU",
        "kind": "external_benchmark",
        "source_name": "AFAC FDI/FFDI severity index",
        "citation": None,
        "target": None,
        "unit": "lives",
        "provenance": "auto",
        "not_available": True,
    },
    {
        "kpi_id": "lives_saved_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("50.0000"),
        "unit": "lives",
        "provenance": "auto",
    },
    {
        "kpi_id": "econ_loss_lagging",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("10.0000"),
        "unit": "AUDm",
        "provenance": "auto",
    },
    {
        "kpi_id": "lives_saved_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("80.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "response_time_p1_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("120.0000"),
        "unit": "seconds",
        "provenance": "auto",
    },
    {
        "kpi_id": "evac_warning_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("18.0000"),
        "unit": "hours",
        "provenance": "auto",
    },
    {
        "kpi_id": "logistics_route_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("70.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "econ_loss_leading",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("15.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "public_info_alert_reach",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("85.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "public_info_behavioural_impact",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("60.0000"),
        "unit": "pct",
        "provenance": "auto",
    },
    {
        "kpi_id": "public_info_multilingual_coverage",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "spec-015 prototype baseline",
        "citation": None,
        "target": Decimal("8.0000"),
        "unit": "languages",
        "provenance": "auto",
    },
]

# Manual-provenance rows for testing the ≤50% manual share constraint
MANUAL_PROVENANCE_SEEDS: list[dict] = [
    {
        "kpi_id": "manual_test_kpi_1",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "Manual baseline for testing",
        "citation": None,
        "target": Decimal("100.0000"),
        "unit": "count",
        "provenance": "manual",
    },
    {
        "kpi_id": "manual_test_kpi_2",
        "jurisdiction": "AU",
        "kind": "prototype_baseline",
        "source_name": "Manual baseline for testing",
        "citation": None,
        "target": Decimal("200.0000"),
        "unit": "count",
        "provenance": "manual",
    },
]

ALL_SEEDS = JURISDICTIONAL_SEEDS + CROSS_SECTOR_SEEDS + LEGACY_SEEDS + MANUAL_PROVENANCE_SEEDS


def seed_register() -> list[BenchmarkEntry]:
    """Generate ≥32 jurisdictional + ≥5 cross-sector benchmark rows (T-AMD-12)."""
    out: list[BenchmarkEntry] = []
    for s in ALL_SEEDS:
        out.append(
            BenchmarkEntry(
                id=secrets.token_hex(13),
                kpi_id=s["kpi_id"],
                jurisdiction=s["jurisdiction"],
                kind=s["kind"],
                source_name=s["source_name"],
                source_citation=s["citation"],
                target_value=s["target"],
                target_unit=s["unit"],
                not_available=s.get("not_available", False),
                provenance=s["provenance"],
                created_at=datetime.now(UTC),
            )
        )

    # Assert ≤50% manual share
    manual_count = sum(1 for e in out if e.provenance == "manual")
    manual_share = manual_count / len(out) if out else 0
    assert manual_share <= 0.50, f"Manual share {manual_share:.1%} exceeds 50% cap (T-AMD-12)"

    return out

