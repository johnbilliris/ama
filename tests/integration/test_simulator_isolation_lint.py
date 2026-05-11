"""Spec-039 T044: ``check_simulator_isolation.py`` MUST fail when a production
module string-references the simulator package.

SC-007.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "tools" / "lint" / "check_simulator_isolation.py"


@pytest.fixture
def repo_with_violation(tmp_path: Path) -> Path:
    """Stand up a minimal tree mirroring the production layout."""
    api = tmp_path / "apps" / "api" / "app" / "services"
    api.mkdir(parents=True)
    (api / "__init__.py").write_text("", encoding="utf-8")
    sim = api / "simulation"
    (sim / "feeds").mkdir(parents=True)
    (sim / "__init__.py").write_text("", encoding="utf-8")
    (sim / "feeds" / "__init__.py").write_text("", encoding="utf-8")

    # The forbidden import — production code referencing simulator.
    (api / "rogue_router.py").write_text(
        "from apps.api.app.services.simulation.feeds import bom_severe_weather\n",
        encoding="utf-8",
    )
    (api / "__init__.py").write_text("", encoding="utf-8")
    return tmp_path


def test_simulator_isolation_string_grep_fails(repo_with_violation: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(LINT),
            "--repo-root",
            str(repo_with_violation),
            "--no-import-linter",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_with_violation),
    )
    assert result.returncode != 0, (
        f"lint should detect production import of simulator.\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "rogue_router.py" in (result.stdout + result.stderr)
