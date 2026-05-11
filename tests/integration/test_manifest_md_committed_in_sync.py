"""Spec-039 A002 — committed MANIFEST.md is in sync with manifest.json.

OBJ-001 root-cause regression test (105 vs 134 entries pre-A007).
Refs: FR-036, SC-016, CL-9. Satisfies CHK016.

Reads the REAL repo artefacts (read-only) and asserts:
1. Re-rendering ``manifest.json`` via ``render()`` produces bytes that,
   after CRLF→LF normalisation, byte-equal the committed ``MANIFEST.md``.
2. Per-category entry count in ``MANIFEST.md`` equals
   ``len(entries[category])`` from ``manifest.json`` (closes OBJ-001).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from tools.lint.render_test_data_manifest_md import render

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_JSON = REPO_ROOT / "docs" / "test-data" / "manifest.json"
MANIFEST_MD = REPO_ROOT / "docs" / "test-data" / "MANIFEST.md"


@pytest.fixture(scope="module")
def manifest_doc() -> dict:
    if not MANIFEST_JSON.exists():
        pytest.skip(f"{MANIFEST_JSON} not present — N/A on this branch.")
    return json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))


def test_committed_manifest_md_byte_equals_re_render(manifest_doc: dict) -> None:
    if not MANIFEST_MD.exists():
        pytest.skip(f"{MANIFEST_MD} not present — N/A on this branch.")
    rendered = render(manifest_doc).replace("\r\n", "\n").encode("utf-8")
    committed = MANIFEST_MD.read_bytes().replace(b"\r\n", b"\n")
    assert committed == rendered, (
        "docs/test-data/MANIFEST.md is stale relative to manifest.json. "
        "Remediate with: python tools/lint/build_test_data_manifest.py && "
        "python tools/lint/render_test_data_manifest_md.py"
    )


def test_per_category_entry_count_parity(manifest_doc: dict) -> None:
    """OBJ-001 closure: row count per category in MANIFEST.md == len(entries)."""
    if not MANIFEST_MD.exists():
        pytest.skip(f"{MANIFEST_MD} not present — N/A on this branch.")
    json_counts: Counter[str] = Counter(e["category"] for e in manifest_doc["entries"])

    md_text = MANIFEST_MD.read_text(encoding="utf-8").replace("\r\n", "\n")
    md_counts: Counter[str] = Counter()
    current_cat: str | None = None
    cat_re = re.compile(r"^## Category: `([^`]+)`")
    row_re = re.compile(r"^\| `[^`]+` \|")  # data row (id is backticked)
    for line in md_text.splitlines():
        m = cat_re.match(line)
        if m:
            current_cat = m.group(1)
            continue
        if current_cat and row_re.match(line):
            md_counts[current_cat] += 1

    assert md_counts == json_counts, (
        f"Per-category entry-count drift. json={dict(json_counts)} "
        f"md={dict(md_counts)}. Remediate with: "
        f"python tools/lint/build_test_data_manifest.py && "
        f"python tools/lint/render_test_data_manifest_md.py"
    )
