from __future__ import annotations

import re
from pathlib import Path

import yaml

from apps.api.app.services.evidence.measurement.renderer import (
    MeasurementMethod,
    MeasurementMethodDefinition,
)
from apps.api.app.services.evidence.models.audit import AuditEntry, AuditTrace
from apps.api.app.services.evidence.models.benchmark import BenchmarkEntry, CitationRef
from apps.api.app.services.evidence.models.chain import (
    Assumption,
    CausalChain,
    ThreatToValidity,
)
from apps.api.app.services.evidence.models.kpi import (
    ConfidenceBandRule,
    IndicatorDefinition,
    KpiLadderGroup,
    KpiLadderView,
    RiskAdjustment,
)
from apps.api.app.services.evidence.models.scorecard import (
    DeltaScorecard,
    DeterminismCheck,
    KpiDelta,
    RunProvenance,
)
from apps.api.app.services.evidence.models.signal import (
    CanonicalEventChain,
    ConfidenceScore,
    Signal,
    SignalIngressRequest,
)
from apps.api.app.services.evidence.public_information import (
    AuslanAsset,
    PublicInformationChannel,
    PublicInformationRender,
)
from apps.api.app.services.evidence.simulation.router import ReplayRequest
from packages.domain.src.domain.models import evidence_init as domain
from scripts.generate_evidence_openapi import build_evidence_openapi

OPENAPI_PATH = Path("specs/040-success-criteria/contracts/openapi.evidence-harness.yaml")
TS_TWIN_PATH = Path("packages/domain/src/evidence/index.ts")

MODELS = {
    model.__name__: model
    for model in (
        Assumption,
        AuditEntry,
        AuditTrace,
        AuslanAsset,
        BenchmarkEntry,
        CanonicalEventChain,
        CausalChain,
        CitationRef,
        ConfidenceBandRule,
        ConfidenceScore,
        DeltaScorecard,
        DeterminismCheck,
        IndicatorDefinition,
        KpiDelta,
        KpiLadderGroup,
        KpiLadderView,
        MeasurementMethod,
        MeasurementMethodDefinition,
        PublicInformationChannel,
        PublicInformationRender,
        ReplayRequest,
        RiskAdjustment,
        RunProvenance,
        Signal,
        SignalIngressRequest,
        ThreatToValidity,
    )
}


def _load_openapi() -> dict:
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


def _interface_blocks(source: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for match in re.finditer(r"export\s+interface\s+(\w+)[^{]*\{", source):
        depth = 1
        cursor = match.end()
        while cursor < len(source) and depth:
            if source[cursor] == "{":
                depth += 1
            elif source[cursor] == "}":
                depth -= 1
            cursor += 1
        blocks[match.group(1)] = source[match.end() : cursor - 1]
    return blocks


def _ts_fields(block: str) -> dict[str, tuple[bool, str]]:
    fields: dict[str, tuple[bool, str]] = {}
    for match in re.finditer(
        r"^\s*(\w+)(\?)?\s*:\s*([^;]+);",
        block,
        re.MULTILINE,
    ):
        fields[match.group(1)] = (match.group(2) is None, match.group(3).strip())
    return fields


def test_stored_openapi_is_generated_from_registered_routes():
    assert _load_openapi() == build_evidence_openapi()


def test_python_domain_twins_match_application_fields_and_requiredness():
    mismatches: list[str] = []
    for name, app_model in MODELS.items():
        domain_model = getattr(domain, name)
        app_fields = {field_name: field.is_required() for field_name, field in app_model.model_fields.items()}
        domain_fields = {field_name: field.is_required() for field_name, field in domain_model.model_fields.items()}
        if app_fields != domain_fields:
            mismatches.append(f"{name}: app={app_fields!r}, domain={domain_fields!r}")
    assert not mismatches, "\n".join(mismatches)


def test_typescript_twin_matches_openapi_fields_requiredness_and_nullability():
    schemas = _load_openapi()["components"]["schemas"]
    blocks = _interface_blocks(TS_TWIN_PATH.read_text(encoding="utf-8"))
    mismatches: list[str] = []

    for name in MODELS:
        schema_name = {
            "ConfidenceScore": "ConfidenceScore-Output",
            "IndicatorDefinition": "IndicatorDefinition-Output",
        }.get(name, name)
        schema = schemas[schema_name]
        ts_fields = _ts_fields(blocks[name])
        openapi_fields = schema.get("properties", {})
        required = set(schema.get("required", []))
        if set(ts_fields) != set(openapi_fields):
            mismatches.append(
                f"{name}: TS-only={sorted(set(ts_fields) - set(openapi_fields))}, "
                f"OpenAPI-only={sorted(set(openapi_fields) - set(ts_fields))}"
            )
            continue
        for field_name, field_schema in openapi_fields.items():
            ts_required, ts_type = ts_fields[field_name]
            if ts_required != (field_name in required):
                mismatches.append(
                    f"{name}.{field_name}: TS required={ts_required}, OpenAPI required={field_name in required}"
                )
            openapi_nullable = _is_nullable(field_schema)
            ts_nullable = "null" in ts_type
            if openapi_nullable != ts_nullable:
                mismatches.append(
                    f"{name}.{field_name}: TS nullable={ts_nullable}, OpenAPI nullable={openapi_nullable}"
                )
    assert not mismatches, "\n".join(mismatches)


def test_openapi_uses_canonical_public_contract_names():
    schemas = _load_openapi()["components"]["schemas"]
    citation = schemas["CitationRef"]["properties"]
    public_channel = schemas["PublicInformationChannel"]["properties"]

    assert "organisation" in citation
    assert "org" not in citation
    assert "body" in public_channel
    assert "content" not in public_channel


def _is_nullable(schema: dict) -> bool:
    if schema.get("type") == "null":
        return True
    return any(_is_nullable(option) for option in schema.get("anyOf", []))
