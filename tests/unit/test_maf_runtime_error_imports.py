"""T074b — package-wide error-import-discipline gate (Polish phase, FR-004).

Scans every Python module under ``apps/agents/maf_runtime/`` and asserts no
locally-defined ``Exception`` subclass exists outside the canonical
``errors.py`` module. All error types used inside the package MUST be
imported from ``apps.agents.maf_runtime.errors``.

Runs in the Polish phase so all downstream modules (Phases 2-6) have had
their chance to wire imports before the gate runs (per the T011b note).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAF_PKG = REPO_ROOT / "apps" / "agents" / "maf_runtime"
ALLOWED = MAF_PKG / "errors.py"


def _collects_exception_subclasses(source: str) -> list[str]:
    """Return the names of any Exception-subclass classes defined in *source*."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name in {"Exception", "BaseException"}:
                found.append(node.name)
                break
            if base_name.endswith("Error") or base_name.endswith("Failure"):
                found.append(node.name)
                break
    return found


def test_no_locally_defined_exception_subclasses_outside_errors_py() -> None:
    offenders: list[str] = []
    for fp in sorted(MAF_PKG.rglob("*.py")):
        if fp.resolve() == ALLOWED.resolve():
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        local = _collects_exception_subclasses(text)
        for cls_name in local:
            offenders.append(f"{fp.relative_to(REPO_ROOT).as_posix()}::{cls_name}")
    assert not offenders, (
        "FR-004 violation: error classes outside apps/agents/maf_runtime/errors.py. "
        "All maf_runtime modules MUST import errors from errors.py. Offenders:\n  "
        + "\n  ".join(offenders)
    )
