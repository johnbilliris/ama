from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from ..models.benchmark import BenchmarkEntry, CitationRef

JURISDICTIONS = ("ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA")

_SOURCES: dict[str, dict[str, tuple[str, str, int, str]]] = {
    "fire": {
        "ACT": (
            "ACT Government / ACT Fire & Rescue",
            "Emergency services - ACT Wellbeing Framework",
            2026,
            "https://www.act.gov.au/wellbeing/explore-overall-wellbeing/safety/emergency-services",
        ),
        "NSW": (
            "NSW Government / Data.NSW",
            "90th percentile response time to structure fires",
            2026,
            "https://data.nsw.gov.au/data/en/dataset/90th-percentile-response-time-to-structure-fires",
        ),
        "NT": (
            "NT Fire and Emergency Services",
            "NT Fire & Emergency Services annual report 2024-2025",
            2025,
            "https://territorystories.nt.gov.au/10070/1017602/0",
        ),
        "QLD": (
            "Queensland Fire and Emergency Services",
            "QFES 2022-23 Annual Report - Key performance measures",
            2023,
            "https://www.fire.qld.gov.au/sites/default/files/2023-09/08-QFES-2022-23-Annual-Report-Performance-Key-performance-measures.pdf",
        ),
        "SA": (
            "South Australian Metropolitan Fire Service",
            "South Australian Metropolitan Fire Service 2022-2023 Performance Report",
            2023,
            "https://www.mfs.sa.gov.au/__data/assets/pdf_file/0009/1096164/2023-10-20-MFS-Performance-Report-2022-2023-FINAL.pdf",
        ),
        "TAS": (
            "Department of Police, Fire and Emergency Management",
            "DPFEM Annual Report 2024-25",
            2025,
            "https://www.police.tas.gov.au/uploads/DPFEM-Annual-Report-2024-25-ACCESSIBLE.pdf",
        ),
        "VIC": ("Fire Rescue Victoria", "Response times", 2026, "https://www.frv.vic.gov.au/response-times"),
        "WA": (
            "WA State Emergency Management Committee / DFES",
            "State Hazard Plan - Fire",
            2025,
            "https://www.wa.gov.au/government/publications/state-hazard-plan-fire",
        ),
    },
    "ambulance": {
        "ACT": (
            "ACT Government / ACT Ambulance Service",
            "Emergency services - ACT Wellbeing Framework",
            2026,
            "https://www.act.gov.au/wellbeing/explore-overall-wellbeing/safety/emergency-services",
        ),
        "NSW": (
            "Audit Office of New South Wales / NSW Ambulance",
            "Ambulance services in regional New South Wales",
            2024,
            "https://www.audit.nsw.gov.au/our-work/reports/ambulance-services-in-regional-new-south-wales",
        ),
        "NT": (
            "NT Health",
            "Ambulance Service Structural Review",
            2024,
            "https://health.nt.gov.au/news/2024/ambulance-service-structural-review",
        ),
        "QLD": (
            "Queensland Ambulance Service",
            "Performance data",
            2026,
            "https://www.ambulance.qld.gov.au/about/performance-data",
        ),
        "SA": (
            "SA Health / SA Ambulance Service",
            "Ambulance waiting times",
            2026,
            "https://www.sahealth.sa.gov.au/wps/wcm/connect/public+content/sa+health+internet/about+us/our+performance/ambulance+waiting+times",
        ),
        "TAS": (
            "Productivity Commission",
            "Report on Government Services 2026 - Ambulance services",
            2026,
            "https://www.pc.gov.au/ongoing/report-on-government-services/health/ambulance-services/",
        ),
        "VIC": (
            "Ambulance Victoria / DataVic",
            "Ambulance Victoria LGA Response Time Performance",
            2025,
            "https://discover.data.vic.gov.au/dataset/ambulance-victoria-lga-response-time-performance",
        ),
        "WA": (
            "WA Department of Health / Parliament of Western Australia",
            "St John WA Ambulance Performance Annual Report to Parliament 2024-25",
            2025,
            "https://www.parliament.wa.gov.au/publications/tabledpapers.nsf/displaypaper/4211128c8475c37146e35ff948258def0007212f/$file/tp-1128.pdf",
        ),
    },
    "ses": {
        "ACT": (
            "ACT Justice and Community Safety Directorate / ACTSES",
            "Justice and Community Safety Directorate Annual Report 2024-25",
            2025,
            "https://www.act.gov.au/__data/assets/pdf_file/0011/2931347/Report-Justice-and-Community-Safety-2024-25-Annual-Report.PDF",
        ),
        "NSW": (
            "NSW State Emergency Service",
            "NSW State Emergency Service Annual Report 2024-25",
            2025,
            "https://www.parliament.nsw.gov.au/fileapi/parlfiles/getartifact?serverRelativeUrl=/tp/files/192031/NSW%20State%20Emergency%20Service%20Annual%20Report%202024-25.pdf",
        ),
        "NT": (
            "Northern Territory Emergency Service",
            "NT Emergency Service",
            2026,
            "https://nt.gov.au/emergency/emergencies/about-emergency-services/nt-emergency-service",
        ),
        "QLD": (
            "Queensland State Emergency Service",
            "State Emergency Service Quarterly Figures",
            2026,
            "https://www.data.qld.gov.au/dataset/state-emergency-service-quarterly-figures",
        ),
        "SA": (
            "Government of South Australia",
            "State Emergency Management Plan 2025",
            2025,
            "https://dpc.sa.gov.au/__data/assets/pdf_file/0008/1209833/State-Emergency-Management-Plan-2025.pdf",
        ),
        "TAS": (
            "Tasmania Fire Service and SES",
            "TFS and SES Strategic Plan 2024-2028",
            2023,
            "https://www.fire.tas.gov.au/wp-content/uploads/2023/12/TFS-SES-Strategic-Plan-2024%E2%80%932028.pdf",
        ),
        "VIC": (
            "Victoria State Emergency Service",
            "Victoria State Emergency Service Authority Annual Report 2024-25",
            2025,
            "https://www.ses.vic.gov.au/documents/d/www/victoria-state-emergency-service-authority-annual-report-2024-25",
        ),
        "WA": (
            "Department of Fire and Emergency Services",
            "Publications - Annual reports",
            2026,
            "https://publications.dfes.wa.gov.au/?corporate=Annual+reports",
        ),
    },
    "police": {
        "ACT": (
            "ACT Policing",
            "ACT Policing Annual Report 2024-25",
            2025,
            "https://police.act.gov.au/__data/assets/pdf_file/0005/301739/ACTP-Annual-Report-24-25_accessible_resized_FINAL.pdf",
        ),
        "NSW": (
            "NSW Government",
            "Evacuation Management Guideline",
            2026,
            "https://data.nsw.gov.au/data/dataset/3-19097-evacuation-management-guideline-",
        ),
        "NT": (
            "NT Police, Fire and Emergency Services",
            "Emergency Management",
            2026,
            "https://pfes.nt.gov.au/emergency-service/emergency-management",
        ),
        "QLD": (
            "Queensland Government",
            "The Disaster Management Guideline",
            2026,
            "https://www.disaster.qld.gov.au/disaster-management-guideline",
        ),
        "SA": (
            "Government of South Australia",
            "State Emergency Management Plan - Annex A: Evacuation",
            2021,
            "https://dpc.sa.gov.au/responsibilities/security-emergency-and-recovery-management/state-emergency-management-plan/SEMP-Part-3-Annex-A-Evacuation-2021-Approved.pdf",
        ),
        "TAS": (
            "Tasmania Police / State Emergency Management Committee",
            "Emergency Evacuation Framework",
            2018,
            "https://d2tv960yzi0spr.cloudfront.net/uploads/2018/10/Emergency-Evacuation-Framework-Package.pdf",
        ),
        "VIC": (
            "Emergency Management Victoria",
            "State Emergency Management Plan",
            2024,
            "https://www.emv.vic.gov.au/responsibilities/state-emergency-management-plan-semp",
        ),
        "WA": (
            "State Emergency Management Committee",
            "Western Australia Community Evacuation in Emergencies Guideline",
            2023,
            "https://www.wa.gov.au/system/files/2023-11/wa_community_evacuation_in_emergencies_guideline.pdf",
        ),
    },
}

_VERIFIED_TARGETS: dict[tuple[str, str], tuple[Decimal, str, str]] = {
    ("fire", "ACT"): (Decimal("600"), "seconds", "90% of structure fires, including call-taking"),
    ("fire", "VIC"): (
        Decimal("462"),
        "seconds",
        "Dispatch to first vehicle arrival; current page states no percentile",
    ),
    ("ambulance", "SA"): (Decimal("480"), "seconds", "Metropolitan Priority 1 arrival; no percentile stated"),
    ("ambulance", "VIC"): (Decimal("900"), "seconds", "Code 1 statewide target: 85% within 15 minutes"),
    ("ambulance", "WA"): (Decimal("900"), "seconds", "Metropolitan Priority 1 target: 90% within 15 minutes"),
}

_LADDER_PROTOTYPES = {
    "lives_saved_leading": (Decimal("80"), "pct"),
    "lives_saved_lagging": (Decimal("50"), "lives"),
    "response_time_p1_leading": (Decimal("120"), "seconds"),
    "response_time_p1": (Decimal("600"), "seconds"),
    "evac_warning_leading": (Decimal("18"), "hours"),
    "evac_lead_lagging": (Decimal("12"), "hours"),
    "logistics_route_leading": (Decimal("70"), "pct"),
    "logistics_efficiency": (Decimal("10"), "pct"),
    "econ_loss_leading": (Decimal("15"), "pct"),
    "econ_loss_lagging": (Decimal("10"), "AUDm"),
    "public_info_alert_reach": (Decimal("85"), "pct"),
    "public_info_behavioural_impact": (Decimal("60"), "pct"),
    "public_info_multilingual_coverage": (Decimal("8"), "languages"),
}


def seed_register() -> list[BenchmarkEntry]:
    created_at = datetime.now(UTC)
    rows = [
        _jurisdiction_entry(category, jurisdiction, created_at)
        for category in ("fire", "ambulance", "ses", "police")
        for jurisdiction in JURISDICTIONS
    ]
    rows.extend(_cross_sector_entries(created_at))
    rows.extend(
        BenchmarkEntry(
            id=secrets.token_hex(13),
            kpi_id=kpi_id,
            jurisdiction="AU",
            category="cross_sector",
            kind="prototype_baseline",
            source_name="Spec 015 prototype measurement",
            source_citation=None,
            provenance="manual",
            benchmark_type="prototype_measurement",
            target_value=value,
            target_unit=unit,
            target_context="Prototype exercise value; not an external service standard",
            created_at=created_at,
        )
        for kpi_id, (value, unit) in _LADDER_PROTOTYPES.items()
    )
    return rows


def _jurisdiction_entry(
    category: str,
    jurisdiction: str,
    created_at: datetime,
) -> BenchmarkEntry:
    citation = _citation(*_SOURCES[category][jurisdiction])
    verified = _VERIFIED_TARGETS.get((category, jurisdiction))
    kpi_id = {
        "fire": "fire_structural_response",
        "ambulance": "response_time_p1",
        "ses": "ses_flood_response",
        "police": "police_evacuation_clearance",
    }[category]
    if verified:
        target, unit, context = verified
        return BenchmarkEntry(
            id=secrets.token_hex(13),
            kpi_id=kpi_id,
            jurisdiction=jurisdiction,
            category=category,  # type: ignore[arg-type]
            kind="external_benchmark",
            source_name=f"{jurisdiction} {category} published target",
            source_citation=citation,
            benchmark_type="performance_target",
            target_value=target,
            target_unit=unit,
            target_context=context,
            created_at=created_at,
        )
    return BenchmarkEntry(
        id=secrets.token_hex(13),
        kpi_id=kpi_id,
        jurisdiction=jurisdiction,
        category=category,  # type: ignore[arg-type]
        kind="external_benchmark",
        source_name=f"{jurisdiction} {category} public benchmark",
        source_citation=citation,
        benchmark_type="unavailable",
        target_value=None,
        target_unit="not published",
        target_context="No current public numeric target was verified in the cited source",
        not_available=True,
        created_at=created_at,
    )


def _cross_sector_entries(created_at: datetime) -> list[BenchmarkEntry]:
    source_rows: list[dict[str, Any]] = [
        {
            "kpi_id": "bom_flood_watch_window",
            "name": "BoM Flood Watch product horizon",
            "citation": (
                "Bureau of Meteorology",
                "Understanding Flood Watches and Flood Warnings",
                2025,
                "https://www.bom.gov.au/video/understanding-flood-watches-and-flood-warnings",
            ),
            "type": "trigger_window",
            "target": Decimal("96"),
            "unit": "hours",
            "context": "May be issued up to four days before expected flooding; this is not a guaranteed SLA",
        },
        {
            "kpi_id": "bom_cyclone_watch_window",
            "name": "BoM Tropical Cyclone Watch definition",
            "citation": (
                "Bureau of Meteorology",
                "Tropical cyclones: what you need to know",
                2020,
                "https://www.bom.gov.au/news-and-media/tropical-cyclones-what-you-need-to-know",
            ),
            "type": "trigger_window",
            "target": Decimal("48"),
            "unit": "hours",
            "context": "Upper bound of the 24-48 hour product definition; not a performance target",
        },
        {
            "kpi_id": "bom_cyclone_warning_window",
            "name": "BoM Tropical Cyclone Warning definition",
            "citation": (
                "Bureau of Meteorology",
                "Tropical cyclones: what you need to know",
                2020,
                "https://www.bom.gov.au/news-and-media/tropical-cyclones-what-you-need-to-know",
            ),
            "type": "trigger_window",
            "target": Decimal("24"),
            "unit": "hours",
            "context": "Gales expected within 24 hours or already occurring; not a performance target",
        },
        {
            "kpi_id": "bom_marine_warning_aim",
            "name": "BoM ocean wind warning operational aim",
            "citation": (
                "Bureau of Meteorology",
                "Ocean Wind Warnings",
                2026,
                "https://www.bom.gov.au/marine/about/warnings/marine-wind-warnings-ocean.shtml",
            ),
            "type": "operational_aim",
            "target": Decimal("24"),
            "unit": "hours",
            "context": "Initial warning aims for around 24 hours lead time",
        },
        {
            "kpi_id": "nema_comdisplan_deployment",
            "name": "COMDISPLAN activation-to-deployment",
            "citation": (
                "National Emergency Management Agency",
                "Australian Government Disaster Response Plan 2025 (COMDISPLAN)",
                2025,
                "https://www.nema.gov.au/sites/default/files/2025-07/Australian%20Government%20Disaster%20Response%20Plan%202025%20%28COMDISPLAN%29.pdf",
            ),
            "type": "unavailable",
            "target": None,
            "unit": "not published",
            "context": "The plan publishes no universal activation-to-deployment deadline",
        },
        {
            "kpi_id": "airservices_arff_response",
            "name": "Airservices ARFF response",
            "citation": (
                "Airservices Australia",
                "ARFF levels of service",
                2026,
                "https://www.airservicesaustralia.com/about-us/our-services/aviation-rescue-fire-fighting-service/arff-levels-of-service/",
            ),
            "type": "performance_target",
            "target": Decimal("180"),
            "unit": "seconds",
            "context": "Initial call to runway end or movement area",
        },
        {
            "kpi_id": "saidi",
            "name": "AER SAIDI metric definition",
            "citation": (
                "Australian Energy Regulator",
                "Distribution Reliability Measures Guideline",
                2024,
                "https://www.aer.gov.au/system/files/2024-12/AER%20-%20Distribution%20reliability%20measures%20guideline%20-%20August%202022%20%28updated%20December%202024%29.pdf",
            ),
            "type": "unavailable",
            "target": None,
            "unit": "minutes/customer/year",
            "context": "Metric definition only; no single national target",
        },
        {
            "kpi_id": "saifi",
            "name": "AER SAIFI metric definition",
            "citation": (
                "Australian Energy Regulator",
                "Distribution Reliability Measures Guideline",
                2024,
                "https://www.aer.gov.au/system/files/2024-12/AER%20-%20Distribution%20reliability%20measures%20guideline%20-%20August%202022%20%28updated%20December%202024%29.pdf",
            ),
            "type": "unavailable",
            "target": None,
            "unit": "interruptions/customer/year",
            "context": "Metric definition only; no single national target",
        },
        {
            "kpi_id": "aiims_span_of_control",
            "name": "AIIMS span of control",
            "citation": (
                "AFAC",
                "AIIMS 2025 Manual product page",
                2025,
                "https://www.afac.com.au/marketplace/9be97a80-5025-4ab7-b4ce-4fe7e68ec573",
            ),
            "type": "unavailable",
            "target": None,
            "unit": "direct reports",
            "context": "The current public page does not expose a 3-7 numeric band",
            "provenance": "manual",
        },
    ]
    return [
        BenchmarkEntry(
            id=secrets.token_hex(13),
            kpi_id=row["kpi_id"],
            jurisdiction="AU",
            category="cross_sector",
            kind="external_benchmark",
            source_name=row["name"],
            source_citation=_citation(*row["citation"]),
            provenance=row.get("provenance", "auto"),
            benchmark_type=row["type"],
            target_value=row["target"],
            target_unit=row["unit"],
            target_context=row["context"],
            not_available=row["type"] == "unavailable",
            created_at=created_at,
        )
        for row in source_rows
    ]


def _citation(
    organisation: str,
    document: str,
    year: int,
    url: str,
) -> CitationRef:
    return CitationRef.model_validate(
        {
            "organisation": organisation,
            "document": document,
            "year": year,
            "url": url,
        }
    )
