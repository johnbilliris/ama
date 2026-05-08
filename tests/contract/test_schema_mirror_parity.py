"""T005 — Schema-mirror parity test (Spec 036 / data-model.md §Schema-mirror).

Asserts byte-identical equality between:
- ``specs/036-foundry-rag-grounding/contracts/<schema>.json``
- ``packages/schemas/spec_036/<schema>.json``

If the contract is updated in ``specs/036-foundry-rag-grounding/contracts/``,
the developer MUST re-mirror to ``packages/schemas/spec_036/`` (and vice versa
is forbidden — the spec contracts are the source of truth).

Run: ``pytest tests/contract/test_schema_mirror_parity.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC_CONTRACTS = ROOT / "specs" / "036-foundry-rag-grounding" / "contracts"
PACKAGE_SCHEMAS = ROOT / "packages" / "schemas" / "spec_036"

MIRRORED_SCHEMAS = (
    "citation-envelope.json",
    "audit-record-llm-call.json",
    "offline-cache-manifest.json",
    # Spec 036 amend-loop additions (Phase F):
    "chunk-metadata.schema.json",
    "cultural-authority-registry.schema.json",
)


@pytest.mark.parametrize("filename", MIRRORED_SCHEMAS)
def test_schema_mirror_byte_equal(filename: str) -> None:
    """packages/schemas/spec_036/<f> MUST byte-equal specs/.../contracts/<f>.

    Any drift means a developer updated one copy without re-mirroring.
    """
    spec_bytes = (SPEC_CONTRACTS / filename).read_bytes()
    pkg_bytes = (PACKAGE_SCHEMAS / filename).read_bytes()
    assert spec_bytes == pkg_bytes, (
        f"schema mirror drift for {filename!r}: "
        f"specs/036-foundry-rag-grounding/contracts/{filename} "
        f"!= packages/schemas/spec_036/{filename}. "
        f"Re-run: cp {SPEC_CONTRACTS / filename} {PACKAGE_SCHEMAS / filename}"
    )


def test_all_schemas_mirrored() -> None:
    """The five contracts MUST exist in both locations."""
    for filename in MIRRORED_SCHEMAS:
        assert (SPEC_CONTRACTS / filename).exists(), f"missing spec {filename}"
        assert (PACKAGE_SCHEMAS / filename).exists(), f"missing mirror {filename}"
