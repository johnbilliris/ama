"""T039 — Integration test: licence inventory drift detection (FR-RAG-IDX-07).

Asserts that ``tools/lint/check_licence_inventory.py`` correctly detects:

1. A clean repo state (current `INDEXING-LICENCE-INVENTORY.md` is in sync).
2. A row missing from the inventory ⇒ exit 1.
3. A row referencing a non-existent ``source.json`` ⇒ exit 1.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT_SCRIPT = REPO_ROOT / "tools" / "lint" / "check_licence_inventory.py"
INVENTORY = REPO_ROOT / "docs" / "corpus" / "INDEXING-LICENCE-INVENTORY.md"
_SCRATCH_BASE = REPO_ROOT / "artifacts" / "test-scratch"


@contextlib.contextmanager
def _scratch_dir():
    _SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=_SCRATCH_BASE) as d:
        yield Path(d)


def _run_lint(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(LINT_SCRIPT), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )


def test_lint_script_exists() -> None:
    assert LINT_SCRIPT.exists(), f"missing lint script {LINT_SCRIPT}"
    assert INVENTORY.exists(), f"missing inventory {INVENTORY}"


def test_lint_passes_on_clean_repo() -> None:
    result = _run_lint()
    assert result.returncode == 0, f"lint failed unexpectedly:\nstdout={result.stdout}\nstderr={result.stderr}"


def test_lint_detects_inventory_row_missing() -> None:
    """Drop the last row from the inventory ⇒ lint must fail."""
    if not LINT_SCRIPT.exists() or not INVENTORY.exists():
        pytest.skip("lint script or inventory missing")

    with _scratch_dir() as scratch:
        backup = scratch / "inventory.bak.md"
        shutil.copy(INVENTORY, backup)
        try:
            text = INVENTORY.read_text(encoding="utf-8")
            lines = text.splitlines()
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith("| ") and "/" in lines[i] and "---" not in lines[i]:
                    del lines[i]
                    break
            else:  # pragma: no cover - inventory must have at least one row
                pytest.fail("could not find a data row to drop")
            INVENTORY.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = _run_lint()
            assert result.returncode != 0, f"lint should have failed on inventory drift:\nstdout={result.stdout}"
        finally:
            shutil.copy(backup, INVENTORY)


def test_lint_detects_orphan_inventory_row() -> None:
    """Add a row pointing at a non-existent source.json ⇒ lint must fail."""
    if not LINT_SCRIPT.exists() or not INVENTORY.exists():
        pytest.skip("lint script or inventory missing")

    with _scratch_dir() as scratch:
        backup = scratch / "inventory.bak2.md"
        shutil.copy(INVENTORY, backup)
        try:
            text = INVENTORY.read_text(encoding="utf-8").rstrip()
            text += "\n| nonexistent | nonexistent-topic | excluded | TEST-SYNTHETIC | https://example/non.pdf |\n"
            INVENTORY.write_text(text, encoding="utf-8")
            result = _run_lint()
            assert result.returncode != 0, f"lint should have failed on orphan row:\nstdout={result.stdout}"
        finally:
            shutil.copy(backup, INVENTORY)
