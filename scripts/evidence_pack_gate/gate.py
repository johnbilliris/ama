"""Spec-037 evidence-pack publication gate — implementation.

Citations: RES-04, FR-008, FR-009, FR-037, FR-038, SC-002, SC-011.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# manual_row_ratio recompute (T018, FR-037)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RatioRecomputeResult:
    manual_row_count: int
    total_row_count: int
    manual_row_ratio: float
    declared_ratio: float | None
    matches_declared: bool


def recompute_manual_row_ratio(sidecar: Path) -> RatioRecomputeResult:
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    manual = sum(
        1
        for r in rows
        if isinstance(r, dict)
        and isinstance(r.get("provenance"), dict)
        and r["provenance"].get("tag") == "manual"
    )
    total = len(rows)
    actual = (manual / total) if total else 0.0
    meta = payload.get("metadata", {})
    declared = meta.get("manual_row_ratio")
    matches = declared is not None and abs(float(declared) - actual) < 1e-9
    return RatioRecomputeResult(
        manual_row_count=manual,
        total_row_count=total,
        manual_row_ratio=actual,
        declared_ratio=declared,
        matches_declared=matches,
    )


# ---------------------------------------------------------------------------
# Cap enforcement (T019/T020, FR-038)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CapResult:
    passed: bool
    reason: str = ""


_REQUIRED_SIGNOFF_FIELDS = ("name", "role", "signoff_date_utc", "basis")


def enforce_cap(sidecar: Path) -> CapResult:
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    meta = payload.get("metadata", {})
    ratio = float(meta.get("manual_row_ratio", 0.0))
    threshold = float(meta.get("manual_row_ratio_threshold", 0.5))
    if ratio <= threshold:
        return CapResult(passed=True)
    signoff = meta.get("auditor_signoff")
    if not isinstance(signoff, dict):
        return CapResult(
            passed=False,
            reason=f"manual_row_ratio={ratio} > {threshold}; auditor_signoff missing (FR-038)",
        )
    missing = [f for f in _REQUIRED_SIGNOFF_FIELDS if not signoff.get(f)]
    if missing:
        return CapResult(
            passed=False,
            reason=f"auditor_signoff incomplete; missing {missing} (FR-038)",
        )
    if len(str(signoff.get("basis", ""))) < 8:
        return CapResult(passed=False, reason="auditor_signoff.basis too short")
    return CapResult(passed=True)


# ---------------------------------------------------------------------------
# Link check (T021, FR-008)
# ---------------------------------------------------------------------------
@dataclass
class LinkCheckResult:
    passed: bool
    broken_links: list[str] = field(default_factory=list)


_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_links(root: Path) -> LinkCheckResult:
    """Scan every *.md under `root` for relative links and verify they resolve."""
    broken: list[str] = []
    for md in root.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in _MD_LINK_RE.finditer(text):
            link = m.group(1)
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = link.split("#", 1)[0]
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{md}: -> {target}")
    return LinkCheckResult(passed=not broken, broken_links=broken)


# ---------------------------------------------------------------------------
# Schema validation (T045, FR-009)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SchemaCheckResult:
    passed: bool
    errors: list[str]


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _REPO_ROOT / "packages" / "schemas" / "spec_037"
_ARTEFACT_TO_SCHEMA = {
    "risk_register": "risk-register.schema.json",
    "adoption_roadmap": "adoption-roadmap.schema.json",
    "executive_kpi_surface": "executive-kpi-surface.schema.json",
    "rai_register": "responsible-ai-register.schema.json",
    "feature_value_ledger": "feature-value-ledger.schema.json",
}


def _registry():
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    resources = []
    for name in _ARTEFACT_TO_SCHEMA.values():
        path = _SCHEMA_DIR / name
        if path.exists():
            resources.append(
                (name, Resource(contents=json.loads(path.read_text(encoding="utf-8")),
                                specification=DRAFT202012))
            )
    pgm = _SCHEMA_DIR / "publication-gate-metadata.schema.json"
    if pgm.exists():
        resources.append(
            (
                "publication-gate-metadata.schema.json",
                Resource(contents=json.loads(pgm.read_text(encoding="utf-8")),
                         specification=DRAFT202012),
            )
        )
    return Registry().with_resources(resources)


def validate_schema(sidecar: Path) -> SchemaCheckResult:
    from jsonschema import Draft202012Validator

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    artefact_id = payload.get("artefact_id")
    schema_name = _ARTEFACT_TO_SCHEMA.get(artefact_id)
    if not schema_name:
        return SchemaCheckResult(False, [f"unknown artefact_id={artefact_id!r}"])
    schema = json.loads((_SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, registry=_registry())
    errs = [
        f"{'/'.join(map(str, e.absolute_path))}: {e.message}"
        for e in validator.iter_errors(payload)
    ]
    return SchemaCheckResult(passed=not errs, errors=errs)


# ---------------------------------------------------------------------------
# Orchestration entry point (T045, T046)
# ---------------------------------------------------------------------------
@dataclass
class GateRunResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    artefacts_seen: int = 0


_DEFAULT_ARTEFACT_ROOTS = (
    "docs/risk-register",
    "docs/governance-hub/adoption-roadmap",
    "docs/governance-hub/executive-kpi",
    "docs/governance-hub/rai-register",
    "specs/shared",  # for feature-value-ledger.{md,json}
)


def run_gate(repo_root: Path | None = None, *, dry_run: bool = False) -> GateRunResult:
    repo_root = (repo_root or _REPO_ROOT).resolve()
    failures: list[str] = []
    artefacts: list[Path] = []
    discovered_ids: list[str] = []

    for rel in _DEFAULT_ARTEFACT_ROOTS:
        root = repo_root / rel
        if not root.exists():
            continue
        for sidecar in root.rglob("*.json"):
            try:
                payload = json.loads(sidecar.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                failures.append(f"{sidecar}: invalid JSON: {e}")
                continue
            artefact_id = payload.get("artefact_id")
            if artefact_id in _ARTEFACT_TO_SCHEMA:
                discovered_ids.append(artefact_id)
                artefacts.append(sidecar)

    expected_ids = set(_ARTEFACT_TO_SCHEMA)
    counts = {artefact_id: discovered_ids.count(artefact_id) for artefact_id in expected_ids}
    missing = sorted(artefact_id for artefact_id, count in counts.items() if count == 0)
    duplicates = sorted(artefact_id for artefact_id, count in counts.items() if count > 1)
    if missing:
        failures.append(f"POPULATION missing canonical artefacts: {', '.join(missing)}")
    if duplicates:
        failures.append(f"POPULATION duplicate canonical artefacts: {', '.join(duplicates)}")

    for art in artefacts:
        s = validate_schema(art)
        if not s.passed:
            failures.append(f"SCHEMA {art}: {s.errors}")
        r = recompute_manual_row_ratio(art)
        if not r.matches_declared:
            failures.append(
                f"RATIO {art}: declared={r.declared_ratio} actual={r.manual_row_ratio}"
            )
        c = enforce_cap(art)
        if not c.passed:
            failures.append(f"CAP {art}: {c.reason}")

    # Link check across the artefact roots' Markdown files.
    for rel in _DEFAULT_ARTEFACT_ROOTS:
        root = repo_root / rel
        if root.exists():
            lc = check_links(root)
            if not lc.passed:
                failures.append(f"LINKS {rel}: {lc.broken_links}")

    return GateRunResult(passed=not failures, failures=failures, artefacts_seen=len(artefacts))
