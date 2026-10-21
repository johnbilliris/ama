"""Spec-007 AUD-029 — the isolation gate selector must stay complete and gated."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tools.lint.check_spec007_isolation_selector import run

pytestmark = pytest.mark.spec007_isolation

ROOT = Path(__file__).resolve().parents[2]


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".github/workflows").mkdir(parents=True)
    shutil.copyfile(ROOT / ".github/workflows/ci.yml", repo / ".github/workflows/ci.yml")
    for relative in sorted(ROOT.joinpath("tests").rglob("*.py")):
        text = relative.read_text(encoding="utf-8", errors="ignore")
        if "pytest.mark.spec007_isolation" not in text:
            continue
        target = repo / relative.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return repo


def test_repository_selector_is_complete_and_gated() -> None:
    assert run(ROOT) == []


def test_unselected_marked_module_fails(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    orphan = repo / "tests/unit/test_spec007_orphan_marked.py"
    orphan.write_text("import pytest\n\npytestmark = pytest.mark.spec007_isolation\n", encoding="utf-8")

    failures = run(repo)

    assert any("tests/unit/test_spec007_orphan_marked.py" in failure for failure in failures)


def test_stale_selector_entry_fails(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    dropped = repo / "tests/integration/test_tenant_isolation.py"
    text = dropped.read_text(encoding="utf-8")
    dropped.write_text(text.replace("pytestmark = pytest.mark.spec007_isolation\n", "", 1), encoding="utf-8")

    failures = run(repo)

    assert any("selects a module without pytest.mark.spec007_isolation" in failure for failure in failures)


def test_missing_nonzero_expectation_fails(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    workflow = repo / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace('SPEC007_MIN_CASES: "', 'SPEC007_MIN_CASES_DISABLED: "', 1), encoding="utf-8")

    failures = run(repo)

    assert any("does not declare SPEC007_MIN_CASES" in failure for failure in failures)


def test_marker_filter_removal_fails(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    workflow = repo / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text.replace("-m spec007_isolation", "-q"), encoding="utf-8")

    failures = run(repo)

    assert any("no longer filters on '-m spec007_isolation'" in failure for failure in failures)
