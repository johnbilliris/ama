#!/usr/bin/env python3
"""Validate docs/architecture diagram inventory, pairing, and hash manifest integrity.

Usage:
    python tools/lint/check_diagram_manifest.py [--root REPO_ROOT]

Exit 0: all checks pass.
Exit 1: one or more checks fail.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HASH_LINE_RE = re.compile(r"^([0-9a-f]{64})  (docs/architecture/.+\.drawio)$")

NAMED_DRAWIO: set[str] = {
    "accessibility/ops-dashboard-user-journey.drawio",
    "c4/agent-runtime-llm-gateway.drawio",
    "c4/component-agents.drawio",
    "c4/component-api.drawio",
    "c4/component-ingest.drawio",
    "c4/component-web.drawio",
    "c4/container.drawio",
    "c4/system.drawio",
    "data/cross-sector-touchpoints.drawio",
    "data/ingestion-data-flow.drawio",
    "data/integration-point-map.drawio",
    "data/jurisdiction-filter.drawio",
    "data/multi-jurisdiction-tenancy.drawio",
    "deployment/azure-resource-topology.drawio",
    "deployment/cicd-pipeline.drawio",
    "deployment/cosmos-partitioning.drawio",
    "governance/waf-pillar-mapping.drawio",
    "operational/aiims-system-context.drawio",
    "operational/escalation-paths.drawio",
    "operational/pprr-phase-overlay.drawio",
    "operational/risk-register-lifecycle.drawio",
    "quality/test-pyramid.drawio",
    "security/au-residency-data-classification.drawio",
    "security/rbac-matrix.drawio",
    "security/sli-slo-model.drawio",
    "security/trust-boundary.drawio",
    "sequence/alert-approval-publication.drawio",
    "sequence/audit-provenance.drawio",
    "sequence/cross-agency-recommendation.drawio",
    "sequence/evacuation-five-stage.drawio",
    "sequence/graceful-degradation.drawio",
    "sequence/recovery-transition.drawio",
}

ALLOWED_EXTRA_DRAWIO: set[str] = {
    "governance/adoption-roadmap.drawio",
    "governance/adoption-roadmap-executive.drawio",
}


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(manifest_path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    entries: list[tuple[str, str]] = []
    failures: list[str] = []
    if not manifest_path.exists():
        return entries, [f"missing manifest: {manifest_path}"]

    for line_number, raw in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            failures.append(f"manifest line {line_number}: blank lines are not allowed")
            continue
        match = HASH_LINE_RE.match(line)
        if not match:
            failures.append(
                f"manifest line {line_number}: must match '<64-lowercase-hex><two spaces>docs/architecture/...drawio'"
            )
            continue
        entries.append((match.group(1), match.group(2)))
    return entries, failures


def _relative_to_arch(path: Path, arch_dir: Path) -> str:
    return path.relative_to(arch_dir).as_posix()


def _validate_provenance(drawio_path: Path, root: ET.Element) -> list[str]:
    issues: list[str] = []
    if root.tag != "mxfile":
        issues.append(f"{drawio_path}: root element must be <mxfile>")
        return issues

    host = root.attrib.get("host", "").strip()
    agent = root.attrib.get("agent", "").strip()
    if not host:
        issues.append(f"{drawio_path}: missing mxfile@host provenance attribute")
    if not agent:
        issues.append(f"{drawio_path}: missing mxfile@agent provenance attribute")

    diagram = root.find("diagram")
    if diagram is None:
        issues.append(f"{drawio_path}: missing <diagram> element")
    else:
        if not (diagram.attrib.get("name") or "").strip():
            issues.append(f"{drawio_path}: <diagram> is missing a name attribute")
        if not (diagram.attrib.get("id") or "").strip():
            issues.append(f"{drawio_path}: <diagram> is missing an id attribute")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory (default: current working directory).",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    arch_dir = root / "docs" / "architecture"
    manifest_path = arch_dir / ".diagram-hashes"
    failures: list[str] = []

    if not arch_dir.exists():
        print(f"FAIL: missing architecture directory: {arch_dir}")
        return 1

    manifest_entries, manifest_failures = _load_manifest(manifest_path)
    failures.extend(manifest_failures)

    manifest_paths = [path for _, path in manifest_entries]
    sorted_manifest_paths = sorted(manifest_paths)
    if manifest_paths != sorted_manifest_paths:
        failures.append("manifest entries must be lexicographically sorted by path")

    duplicate_manifest_paths = sorted({p for p in manifest_paths if manifest_paths.count(p) > 1})
    for duplicate_path in duplicate_manifest_paths:
        failures.append(f"duplicate manifest path: {duplicate_path}")

    drawio_files = sorted(arch_dir.rglob("*.drawio"))
    png_files = sorted(arch_dir.rglob("*.png"))

    drawio_paths = {f"docs/architecture/{_relative_to_arch(path, arch_dir)}" for path in drawio_files}
    png_paths = {f"docs/architecture/{_relative_to_arch(path, arch_dir)}" for path in png_files}
    manifest_path_set = set(manifest_paths)

    missing_manifest_entries = sorted(drawio_paths - manifest_path_set)
    extra_manifest_entries = sorted(manifest_path_set - drawio_paths)
    for missing in missing_manifest_entries:
        failures.append(f"missing manifest entry for drawio source: {missing}")
    for extra in extra_manifest_entries:
        failures.append(f"manifest references missing drawio source: {extra}")

    for drawio_path in drawio_files:
        rel = f"docs/architecture/{_relative_to_arch(drawio_path, arch_dir)}"
        expected_png = rel.removesuffix(".drawio") + ".png"
        if expected_png not in png_paths:
            failures.append(f"missing png sibling for drawio source: {rel}")

        # Validate XML parseability and basic provenance metadata.
        try:
            root_element = ET.fromstring(drawio_path.read_text(encoding="utf-8"))
        except ET.ParseError as exc:
            failures.append(f"xml parse error in {rel}: {exc}")
            continue
        failures.extend(_validate_provenance(drawio_path, root_element))

        expected_hash = _sha256_hex(drawio_path)
        declared_hash = next((h for h, p in manifest_entries if p == rel), None)
        if declared_hash and declared_hash != expected_hash:
            failures.append(f"hash mismatch for {rel}: manifest={declared_hash} actual={expected_hash}")

    for png_path in png_files:
        rel = f"docs/architecture/{_relative_to_arch(png_path, arch_dir)}"
        expected_drawio = rel.removesuffix(".png") + ".drawio"
        if expected_drawio not in drawio_paths:
            failures.append(f"missing drawio sibling for png export: {rel}")

    observed_drawio_inventory = {path.removeprefix("docs/architecture/") for path in drawio_paths}
    missing_named = sorted(NAMED_DRAWIO - observed_drawio_inventory)
    for missing in missing_named:
        failures.append(f"missing required named diagram source: docs/architecture/{missing}")

    allowed_inventory = NAMED_DRAWIO | ALLOWED_EXTRA_DRAWIO
    unexpected = sorted(observed_drawio_inventory - allowed_inventory)
    for extra in unexpected:
        failures.append(
            f"unexpected diagram source outside named inventory and allowed extras: docs/architecture/{extra}"
        )

    if failures:
        print("FAIL: diagram manifest validation failed")
        for issue in failures:
            print(f"  - {issue}")
        return 1

    print(
        "OK: diagram manifest validation passed "
        f"({len(drawio_files)} drawio, {len(png_files)} png, {len(manifest_entries)} manifest entries)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
