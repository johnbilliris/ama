"""Spec-038 FR-036 / CL-9 — thin wrapper over ``render_test_data_manifest_md --check``.

Naming-symmetry shim so CI invokes the freshness gate by the same
``check_*.py`` convention as the other spec-038 lints. All real logic lives
in ``tools/lint/render_test_data_manifest_md.py::main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as ``python tools/lint/check_manifest_md_fresh.py`` from the
# repo root: ensure the repo root (parents[2]) is on sys.path so the
# ``tools.lint`` namespace package can resolve.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.lint.render_test_data_manifest_md import main  # noqa: E402

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(["--check", *sys.argv[1:]]))
