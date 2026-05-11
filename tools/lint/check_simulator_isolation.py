"""Spec-039 / T055 — Simulator isolation lint (SC-007, R2).

Defence-in-depth complement to the ``import-linter`` contracts declared in
``pyproject.toml`` (``simulator_not_imported_by_production``,
``seed_not_imported_by_runtime``).

This script catches **string-based** references that ``import-linter``
cannot see (DI lookups, ``importlib.import_module(...)`` strings, etc.):

1. AST-string grep over ``apps/api/app/**`` (excluding
   ``apps/api/app/services/simulation/**``) and ``apps/agents/**`` for any
   string literal containing ``apps.api.app.services.simulation``.
2. Optional shell-out to ``lint-imports --config pyproject.toml`` for the
   structural check.

Run::

    python tools/lint/check_simulator_isolation.py
    python tools/lint/check_simulator_isolation.py --no-import-linter
    python tools/lint/check_simulator_isolation.py --repo-root .

Exit code 0 → clean, 1 → violation, 2 → IO error.
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Match the import-linter ``simulator_not_imported_by_production`` contract
# in ``pyproject.toml``: only the ``feeds``/``replay``/``generators``
# sub-packages are isolated. Other ``services/simulation/*`` modules (e.g.
# ``dispatch_status``, ``cancellation``, ``outcome_signed_url``) are
# legitimate runtime services and routes may reference them.
SIM_PKGS = (
    "apps.api.app.services.simulation.feeds",
    "apps.api.app.services.simulation.replay",
    "apps.api.app.services.simulation.generators",
)
SCAN_ROOTS = (
    "apps/api/app",
    "apps/agents",
)
EXCLUDE_SUBSTR = (
    "apps/api/app/services/simulation",
    "apps\\api\\app\\services\\simulation",
)


def _files(repo_root: Path) -> list[Path]:
    out: list[Path] = []
    for root in SCAN_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            posix = p.as_posix()
            if any(ex in posix for ex in (e.replace("\\", "/") for e in EXCLUDE_SUBSTR)):
                continue
            if "__pycache__" in p.parts:
                continue
            out.append(p)
    return sorted(out)


def _ast_string_hits(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, snippet)`` for any string mentioning the simulator."""
    try:
        src = path.read_text(encoding="utf-8")
    except OSError:
        return []
    hits: list[tuple[int, str]] = []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        # Fall back to plain grep — a syntactically broken file should still
        # be flagged if it contains the pattern.
        for i, line in enumerate(src.splitlines(), start=1):
            if any(pkg in line for pkg in SIM_PKGS):
                hits.append((i, line.strip()))
        return hits
    for node in ast.walk(tree):
        # String literal constants.
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(pkg in node.value for pkg in SIM_PKGS):
                hits.append((node.lineno, node.value[:120]))
        # ``from apps.api.app.services.simulation.{feeds,replay,generators}.. import ...``
        if isinstance(node, ast.ImportFrom):
            if node.module and any(pkg in node.module for pkg in SIM_PKGS):
                hits.append((node.lineno, f"from {node.module} import ..."))
        # ``import apps.api.app.services.simulation.{feeds,replay,generators}..``
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(pkg in alias.name for pkg in SIM_PKGS):
                    hits.append((node.lineno, f"import {alias.name}"))
    # Deduplicate by (lineno, snippet).
    return sorted(set(hits))


def check(repo_root: Path, run_import_linter: bool) -> int:
    issues: list[str] = []
    files = _files(repo_root)
    for fp in files:
        for lineno, snippet in _ast_string_hits(fp):
            rel = fp.relative_to(repo_root).as_posix()
            issues.append(f"sim-leak: {rel}:{lineno}: {snippet}")

    summary: dict[str, object] = {
        "files_scanned": len(files),
        "issues": len(issues),
        "import_linter_invoked": False,
    }

    if run_import_linter:
        cli = shutil.which("lint-imports")
        if cli is None:
            print(
                "WARN: lint-imports CLI not found on PATH; structural check skipped (string-grep still ran).",
                file=sys.stderr,
            )
        else:
            cfg = repo_root / "pyproject.toml"
            args = [cli, "--config", str(cfg)]
            try:
                proc = subprocess.run(args, capture_output=True, text=True, cwd=str(repo_root))
            except OSError as e:
                print(f"WARN: lint-imports invocation failed: {e}", file=sys.stderr)
            else:
                summary["import_linter_invoked"] = True
                summary["import_linter_returncode"] = proc.returncode
                if proc.returncode != 0:
                    issues.append("import-linter contract failure (see lint-imports output)")
                    print(proc.stdout)
                    print(proc.stderr, file=sys.stderr)

    if issues:
        print("simulator-isolation drift detected:")
        for issue in issues:
            print(f"  - {issue}")
        print(json.dumps(summary, indent=2), file=sys.stderr)
        return 1

    print(
        f"simulator-isolation clean — {len(files)} files scanned, "
        f"import-linter={'invoked' if summary['import_linter_invoked'] else 'skipped'}."
    )
    print(json.dumps(summary, indent=2), file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", default=".", type=Path)
    p.add_argument(
        "--no-import-linter",
        action="store_true",
        help="Skip the lint-imports invocation (string-grep only).",
    )
    args = p.parse_args(argv)
    return check(args.repo_root.resolve(), run_import_linter=not args.no_import_linter)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
