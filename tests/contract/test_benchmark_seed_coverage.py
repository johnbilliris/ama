"""Contract test: Benchmark seed coverage (T-AMD-22, T-AMD-12)."""
from __future__ import annotations


def test_benchmark_seed_has_32_plus_jurisdictional_rows():
    """Benchmark seed includes ≥32 jurisdictional rows (8 × 4) (T-AMD-22, T-AMD-12)."""
    from apps.api.app.services.evidence.benchmarks.seed import seed_register

    entries = seed_register()
    jurisdictional = [e for e in entries if e.jurisdiction in ("NSW", "VIC", "QLD", "SA", "WA", "ACT", "NT", "TAS")]
    assert len(jurisdictional) >= 32, f"Expected ≥32 jurisdictional rows, got {len(jurisdictional)}"


def test_benchmark_seed_has_5_plus_cross_sector_rows():
    """Benchmark seed includes ≥5 cross-sector rows (AU jurisdiction) (T-AMD-22, T-AMD-12)."""
    from apps.api.app.services.evidence.benchmarks.seed import seed_register

    entries = seed_register()
    cross_sector = [
        e
        for e in entries
        if e.jurisdiction == "AU"
        and e.kind == "external_benchmark"
        and e.kpi_id
        in (
            "bom_warning_lead_time",
            "nema_comdisplan_adoption",
            "icao_arff_response",
            "saidi_saifi_reliability",
            "aiims_span_of_control",
        )
    ]
    assert len(cross_sector) >= 5, f"Expected ≥5 cross-sector rows, got {len(cross_sector)}"


def test_benchmark_seed_manual_share_lte_50_percent():
    """Benchmark seed has ≤50% manual provenance (T-AMD-22, T-AMD-12)."""
    from apps.api.app.services.evidence.benchmarks.seed import seed_register

    entries = seed_register()
    manual_count = sum(1 for e in entries if e.provenance == "manual")
    manual_share = manual_count / len(entries) if entries else 0
    assert manual_share <= 0.50, f"Manual share {manual_share:.1%} exceeds 50% cap"


def test_benchmark_seed_citations_present():
    """Benchmark seed auto-provenance rows have CitationRef (T-AMD-22, T-AMD-12)."""
    from apps.api.app.services.evidence.benchmarks.seed import seed_register

    entries = seed_register()
    auto_entries = [e for e in entries if e.provenance == "auto"]
    for entry in auto_entries[:10]:  # Check first 10 auto entries
        assert entry.source_citation is not None, f"Auto entry {entry.id} missing citation"
        assert entry.source_citation.org, f"Auto entry {entry.id} citation missing org"
        assert entry.source_citation.document, f"Auto entry {entry.id} citation missing document"
        assert entry.source_citation.year, f"Auto entry {entry.id} citation missing year"
        assert entry.source_citation.url, f"Auto entry {entry.id} citation missing url"
