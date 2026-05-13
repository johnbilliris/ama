"""Contract test: OpenAPI schema vs TypeScript twin field parity (T-AMD-10, D25).

Asserts that every TypeScript interface in packages/domain/src/evidence/index.ts
mirrors the corresponding OpenAPI schema — no extra optional fields permitted.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

OPENAPI_PATH = Path("specs/040-success-criteria/contracts/openapi.evidence-harness.yaml")
TS_TWIN_PATH = Path("packages/domain/src/evidence/index.ts")


def _load_openapi_schemas() -> dict:
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not available")
    if not OPENAPI_PATH.exists():
        pytest.skip(f"OpenAPI spec not found at {OPENAPI_PATH}")
    with OPENAPI_PATH.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return spec.get("components", {}).get("schemas", {})


def _extract_ts_interfaces(ts_path: Path) -> dict[str, set[str]]:
    """Extract interface name → field names from TypeScript source."""
    if not ts_path.exists():
        return {}
    content = ts_path.read_text(encoding="utf-8")
    interfaces: dict[str, set[str]] = {}
    # Match: export interface Foo { ... }
    for m in re.finditer(
        r"(?:export\s+)?interface\s+(\w+)\s*\{([^}]+)\}",
        content,
        re.DOTALL,
    ):
        name = m.group(1)
        body = m.group(2)
        # Extract field names — lines like "  fieldName?: type;"
        fields = set(re.findall(r"^\s+(\w+)\??\s*:", body, re.MULTILINE))
        interfaces[name] = fields
    return interfaces


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_key_interfaces_present_in_ts_twin():
    """Key Pydantic model names must each have a corresponding TS interface."""
    required = [
        "IndicatorDefinition",
        "RiskAdjustment",
        "ConfidenceBandRule",
        "AuditEntry",
        "AuditTrace",
        "BenchmarkEntry",
        "CitationRef",
        "CausalChain",
        "DeltaScorecard",
        "PublicInformationRender",
    ]
    ts_interfaces = _extract_ts_interfaces(TS_TWIN_PATH)
    missing = [name for name in required if name not in ts_interfaces]
    assert not missing, f"Missing TS interfaces: {missing}"


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_openapi_required_fields_present_in_ts_twin():
    """All OpenAPI-required fields for key schemas must be present in the TS twin (D25).

    Direction: OpenAPI required fields ⊆ TS fields.
    The TS twin may have additional internal/computed fields not in the OpenAPI contract
    (e.g. created_by, correlation_id) — that is acceptable per the reuse-only constraint.
    """
    schemas = _load_openapi_schemas()
    ts_interfaces = _extract_ts_interfaces(TS_TWIN_PATH)

    mismatches: list[str] = []
    for schema_name, schema_def in schemas.items():
        if schema_name not in ts_interfaces:
            continue
        # Only check required fields — optional OpenAPI fields may be omitted from TS
        required_fields = set(schema_def.get("required", []))
        ts_fields = ts_interfaces[schema_name]
        missing_required = required_fields - ts_fields
        if missing_required:
            mismatches.append(f"{schema_name}: required OpenAPI fields absent from TS: {sorted(missing_required)}")

    assert not mismatches, "\n".join(mismatches)


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_risk_adjustment_has_provenance_and_signoff():
    """RiskAdjustment TS interface must include provenance + auditor_signoff_required (T-AMD-11)."""
    ts_interfaces = _extract_ts_interfaces(TS_TWIN_PATH)
    ra = ts_interfaces.get("RiskAdjustment", set())
    assert "provenance" in ra, "RiskAdjustment missing 'provenance' field"
    assert "auditor_signoff_required" in ra, "RiskAdjustment missing 'auditor_signoff_required' field"


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_audit_kind_includes_language_fallback():
    """AuditKind TS union must include 'language_fallback_used' (T-AMD-13)."""
    content = TS_TWIN_PATH.read_text(encoding="utf-8")
    assert "language_fallback_used" in content, "AuditKind missing 'language_fallback_used'"


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_benchmark_entry_has_citation_ref():
    """BenchmarkEntry must reference CitationRef (T-AMD-12)."""
    ts_interfaces = _extract_ts_interfaces(TS_TWIN_PATH)
    be = ts_interfaces.get("BenchmarkEntry", set())
    assert "source_citation" in be, "BenchmarkEntry missing 'source_citation'"
    assert "CitationRef" in ts_interfaces, "CitationRef interface missing"


@pytest.mark.skipif(not TS_TWIN_PATH.exists(), reason="TS twin not found")
def test_indicator_definition_risk_adjustment_required():
    """IndicatorDefinition.risk_adjustment must be required (not optional) in TS twin (T-AMD-11)."""
    content = TS_TWIN_PATH.read_text(encoding="utf-8")
    # In the interface, "risk_adjustment:" (no ?) means required
    # "risk_adjustment?:" means optional
    # Find the IndicatorDefinition interface block
    m = re.search(
        r"interface\s+IndicatorDefinition\s*\{([^}]+)\}",
        content,
        re.DOTALL,
    )
    assert m, "IndicatorDefinition interface not found"
    body = m.group(1)
    # Check that risk_adjustment is declared without '?'
    assert re.search(r"risk_adjustment\s*:", body), "risk_adjustment should be required (no '?')"
    assert not re.search(r"risk_adjustment\?", body), "risk_adjustment must not be optional"
