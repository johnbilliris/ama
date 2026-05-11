"""Spec-038 T162 — combined Two-Path Rule gate.

Defence-in-depth composite test that asserts all three Two-Path Rule
enforcement layers are simultaneously green:

(a) ``import-linter`` contracts — including ``simulator_not_imported_by_production``
    and ``seed_not_imported_by_runtime``.
(b) ``tools/lint/check_simulator_isolation.py`` — string-grep + AST pass over
    every production module.
(c) ``tools/lint/check_test_data_manifest.py`` — manifest ``category`` ↔ ``path``
    location mapping (``PATH_RULES``).

Mapping: Two-Path Rule (plan §"Two-Path Rule"), SC-007 (zero production
imports of simulator), FR-016, FR-024, FR-054.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kw,
    )


def test_layer_a_import_linter_contracts_pass() -> None:
    """All 5 import-linter contracts must be KEPT."""
    if shutil.which("lint-imports") is None:
        pytest.skip("lint-imports not installed in this environment")
    proc = _run(["lint-imports", "--config", "pyproject.toml"])
    assert proc.returncode == 0, (
        f"import-linter contracts broken:\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    out = proc.stdout
    assert "simulator_not_imported_by_production KEPT" in out
    assert "seed_not_imported_by_runtime KEPT" in out


def test_layer_b_simulator_isolation_lint_clean() -> None:
    """``check_simulator_isolation.py`` must exit 0 against the live tree."""
    proc = _run(
        [sys.executable, "tools/lint/check_simulator_isolation.py"]
    )
    assert proc.returncode == 0, (
        f"simulator-isolation lint dirty:\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_layer_c_manifest_path_category_mapping_clean() -> None:
    """``check_test_data_manifest.py`` enforces category↔path mapping."""
    proc = _run(
        [sys.executable, "tools/lint/check_test_data_manifest.py"]
    )
    assert proc.returncode == 0, (
        f"manifest lint dirty:\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )


def test_two_path_rule_all_three_layers_green() -> None:
    """Composite: every layer must be green for the Two-Path Rule to hold."""
    layers: dict[str, subprocess.CompletedProcess] = {}
    if shutil.which("lint-imports") is not None:
        layers["import-linter"] = _run(
            ["lint-imports", "--config", "pyproject.toml"]
        )
    layers["simulator-isolation"] = _run(
        [sys.executable, "tools/lint/check_simulator_isolation.py"]
    )
    layers["manifest-mapping"] = _run(
        [sys.executable, "tools/lint/check_test_data_manifest.py"]
    )
    failures = {name: p.returncode for name, p in layers.items() if p.returncode != 0}
    assert not failures, (
        "Two-Path Rule layers failing: "
        + ", ".join(f"{n}={rc}" for n, rc in failures.items())
    )
