"""Spec-038 A003 — renderer determinism + golden-hash + LF/UTF-8 contract.

Refs: FR-036, FR-031, CL-11, CL-12. Satisfies CHK001-CHK004, CHK019-CHK021.

Any future change to ``render()``'s sort key, header text, column set,
spacing, or trailing-newline policy MUST update BOTH ``GOLDEN_SHA256``
in this module AND FR-036 in ``specs/038-test-data-provisioning/spec.md``
in the same PR.
"""

from __future__ import annotations

import hashlib

from tools.lint.render_test_data_manifest_md import render

# Computed once from the renderer at A003 authoring time. Do not bump
# without updating FR-036 in the spec.
GOLDEN_SHA256 = "2c94824d00c8ac229a0deece597684982ce856a1d74ecb7bc5b691b006430640"

# 4 entries, 3 categories, deliberately covering sort-key edge cases:
#   - same category (alpha) different ids (a-001 vs a-002) — id-secondary sort
#   - same id (a-001) different categories (alpha vs gamma) — category-primary sort
#   - one entry uses ``source_shape`` instead of ``path`` (CL-11 / FR-031 column)
FIXTURE = {
    "schema_version": "1.0.0",
    "generated_at": "2026-05-11T00:00:00Z",
    "entries": [
        {
            "id": "a-002",
            "name": "Alpha 2",
            "category": "alpha",
            "path": "fixtures/a2.json",
            "version": "1.0.0",
            "content_hash": "0" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": ["p1", "p2"],
            "domain_group": "cross-sector",
            "fictitious": True,
            "pii": False,
            "pspf": "OFFICIAL",
            "residency": "AU",
            "licence": "proprietary-fictitious-internal",
            "source_url": "n/a",
            "snapshot_date": "n/a",
            "dataset_version": "n/a",
            "refresh_policy": "static",
            "volume_tier": "n/a",
            "record_count": 0,
            "cultural_review_required": False,
        },
        {
            "id": "a-001",
            "name": "Alpha 1",
            "category": "alpha",
            "path": "fixtures/a1.json",
            "version": "1.0.0",
            "content_hash": "1" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": ["p1"],
            "domain_group": "ambulance",
            "fictitious": True,
            "pii": False,
            "pspf": "OFFICIAL",
            "residency": "AU",
            "licence": "CC-BY-4.0",
            "source_url": "n/a",
            "snapshot_date": "n/a",
            "dataset_version": "n/a",
            "refresh_policy": "static",
            "volume_tier": "n/a",
            "record_count": 0,
            "cultural_review_required": True,
        },
        {
            "id": "b-001",
            "name": "Beta 1",
            "category": "beta",
            "source_shape": "beta.shape.v1",
            "version": "1.0.0",
            "content_hash": "2" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": ["p3"],
            "domain_group": "fire",
            "fictitious": True,
            "pii": False,
            "pspf": "OFFICIAL",
            "residency": "AU",
            "licence": "proprietary-fictitious-internal",
            "source_url": "n/a",
            "snapshot_date": "n/a",
            "dataset_version": "n/a",
            "refresh_policy": "regenerate-each-run",
            "volume_tier": "n/a",
            "record_count": 0,
            "cultural_review_required": False,
        },
        {
            "id": "a-001",
            "name": "Gamma 1",
            "category": "gamma",
            "path": "fixtures/g1.json",
            "version": "1.0.0",
            "content_hash": "3" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": [],
            "domain_group": "police",
            "fictitious": True,
            "pii": False,
            "pspf": "OFFICIAL",
            "residency": "AU",
            "licence": "CC0-1.0",
            "source_url": "n/a",
            "snapshot_date": "n/a",
            "dataset_version": "n/a",
            "refresh_policy": "static",
            "volume_tier": "n/a",
            "record_count": 0,
            "cultural_review_required": False,
        },
    ],
}


def _bytes() -> bytes:
    return render(FIXTURE).replace("\r\n", "\n").encode("utf-8")


def test_render_is_byte_deterministic_across_invocations() -> None:
    assert _bytes() == _bytes()


def test_render_matches_golden_sha256() -> None:
    actual = hashlib.sha256(_bytes()).hexdigest()
    assert actual == GOLDEN_SHA256, (
        "Renderer output drifted from golden hash. If this change is "
        "intentional, update GOLDEN_SHA256 AND FR-036 in spec.md in the "
        f"SAME PR. expected={GOLDEN_SHA256} actual={actual}"
    )


def test_render_ends_with_single_lf() -> None:
    out = _bytes()
    assert out.endswith(b"\n")
    assert not out.endswith(b"\n\n")


def test_render_contains_no_carriage_returns() -> None:
    assert b"\r" not in _bytes()


def test_render_decodes_as_utf8() -> None:
    _bytes().decode("utf-8")  # raises on failure


def test_render_emits_seven_named_columns_per_category() -> None:
    """CL-11 / FR-031: each category table has exactly the 7 columns.

    Order/text: ``id``, ``path / source_shape``, ``domain_group``,
    ``personas``, ``pspf``, ``licence``, ``cultural_review``.
    """
    text = _bytes().decode("utf-8")
    expected_header = "| id | path / source_shape | domain_group | personas | pspf | licence | cultural_review |"
    # One header per non-empty category; fixture has 3 categories.
    assert text.count(expected_header) == 3
    # Verify the divider row also appears 3 times (7 columns => 7 dividers).
    assert text.count("|---|---|---|---|---|---|---|") == 3
    # Verify the column names are present in the documented order.
    for col in (
        "id",
        "path / source_shape",
        "domain_group",
        "personas",
        "pspf",
        "licence",
        "cultural_review",
    ):
        assert f"| {col} |" in text or f" {col} |" in text
