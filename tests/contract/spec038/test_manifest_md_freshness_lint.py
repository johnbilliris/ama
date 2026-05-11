"""Spec-038 A001 — manifest-md freshness lint contract.

Exercises the four sub-cases from plan §A.3:
  (a) clean state         → exit 0, no output
  (b) drift state         → exit 1, unified diff + remediation command
  (c) missing-manifest    → exit 0, stderr skip notice (CL-10)
  (d) CRLF tolerance      → exit 0 even when MANIFEST.md is CRLF-encoded

Refs: FR-036, SC-016, CL-9, CL-10.
Satisfies CHK005-CHK007, CHK010, CHK011, CHK013-CHK015, CHK017, CHK018.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.lint.render_test_data_manifest_md import render

REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "tools" / "lint" / "check_manifest_md_fresh.py"

# Minimal but schema-shaped fixture.
SAMPLE_DOC = {
    "schema_version": "1.0.0",
    "generated_at": "2026-05-11T00:00:00Z",
    "entries": [
        {
            "id": "x-001",
            "name": "X 1",
            "category": "mock",
            "path": "fixtures/x1.json",
            "version": "1.0.0",
            "content_hash": "0" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": ["incident-commander"],
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
            "id": "y-001",
            "name": "Y 1",
            "category": "synthetic",
            "path": "fixtures/y1.json",
            "version": "1.0.0",
            "content_hash": "1" * 64,
            "created_or_updated": "2026-05-11",
            "persona_bindings": ["operations-officer"],
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
            "cultural_review_required": False,
        },
    ],
}


def _isolated(tmp_path: Path) -> tuple[Path, Path]:
    docs = tmp_path / "docs" / "test-data"
    docs.mkdir(parents=True)
    return docs / "manifest.json", docs / "MANIFEST.md"


def _run(
    tmp_path: Path,
    manifest: Path,
    out: Path,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Wrapper imports ``tools.lint.render_test_data_manifest_md`` as a
    # namespace package — ensure repo root is on PYTHONPATH so the
    # subprocess (run from tmp_path) can resolve it.
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [
            sys.executable,
            str(WRAPPER),
            "--manifest",
            str(manifest),
            "--out",
            str(out),
            *extra,
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
    )


def _write_clean(manifest: Path, out: Path) -> None:
    manifest.write_text(json.dumps(SAMPLE_DOC, indent=2) + "\n", encoding="utf-8")
    out.write_bytes(render(SAMPLE_DOC).replace("\r\n", "\n").encode("utf-8"))


def test_wrapper_script_exists() -> None:
    """A005 naming-symmetry: CI invokes ``check_manifest_md_fresh.py``."""
    assert WRAPPER.exists(), f"missing wrapper: {WRAPPER}"


# ---------------------------------------------------------------------------
# Sub-case (a) — clean state
# ---------------------------------------------------------------------------
def test_clean_state_exits_zero(tmp_path: Path) -> None:
    manifest, out = _isolated(tmp_path)
    _write_clean(manifest, out)
    r = _run(tmp_path, manifest, out)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    # Quiet on success.
    assert r.stdout == ""


# ---------------------------------------------------------------------------
# Sub-case (b) — drift detection (three independent fixture variants)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "mutator_id",
    ["row-deleted", "header-altered", "row-reordered"],
)
def test_drift_exits_nonzero_with_diff_and_remediation(tmp_path: Path, mutator_id: str) -> None:
    manifest, out = _isolated(tmp_path)
    _write_clean(manifest, out)
    text = out.read_text(encoding="utf-8")
    if mutator_id == "row-deleted":
        # Drop the y-001 data row.
        text = "\n".join(line for line in text.splitlines() if "y-001" not in line) + "\n"
    elif mutator_id == "header-altered":
        text = text.replace(
            "# Test-Data Manifest (Spec 038)",
            "# Test-Data Manifest (Spec 038) -- HAND-EDITED",
        )
    elif mutator_id == "row-reordered":
        # Swap a column value to simulate column reordering / field drift.
        text = text.replace("`OFFICIAL`", "`OFFICIAL-DRIFT`", 1)
    out.write_text(text, encoding="utf-8")

    r = _run(tmp_path, manifest, out)
    assert r.returncode != 0, f"drift variant '{mutator_id}' should fail. stdout={r.stdout!r}\nstderr={r.stderr!r}"
    # Unified diff markers.
    assert "---" in r.stdout and "+++" in r.stdout, f"missing unified diff in stdout: {r.stdout!r}"
    # Remediation command in stderr.
    assert "build_test_data_manifest.py" in r.stderr, r.stderr
    assert "render_test_data_manifest_md.py" in r.stderr, r.stderr


# ---------------------------------------------------------------------------
# Sub-case (c) — missing manifest skip (CL-10)
# ---------------------------------------------------------------------------
def test_missing_manifest_skips_with_stderr_notice(tmp_path: Path) -> None:
    manifest, out = _isolated(tmp_path)
    # Intentionally do NOT create manifest.json.
    r = _run(tmp_path, manifest, out)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    assert "skip" in r.stderr.lower() or "N/A" in r.stderr, f"expected skip notice on stderr; got: {r.stderr!r}"


# ---------------------------------------------------------------------------
# Sub-case (d) — CRLF tolerance
# ---------------------------------------------------------------------------
def test_crlf_committed_md_still_passes(tmp_path: Path) -> None:
    manifest, out = _isolated(tmp_path)
    _write_clean(manifest, out)
    # Rewrite committed MANIFEST.md with CRLF line endings (Windows
    # core.autocrlf=true scenario).
    crlf = out.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    out.write_bytes(crlf)
    r = _run(tmp_path, manifest, out)
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


# ---------------------------------------------------------------------------
# Sub-case (b-extra) — diff truncation budget honoured
# ---------------------------------------------------------------------------
def test_max_diff_lines_truncates_output(tmp_path: Path) -> None:
    manifest, out = _isolated(tmp_path)
    _write_clean(manifest, out)
    # Replace the entire file with empty content → maximally large diff.
    out.write_text("", encoding="utf-8")
    r = _run(tmp_path, manifest, out, "--max-diff-lines", "3")
    assert r.returncode != 0
    assert "truncated" in r.stdout.lower()
