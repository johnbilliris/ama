"""Pytest path bootstrap for apps/api/tests/.

When pytest is invoked with paths under ``apps/api/tests/`` (e.g. by the
spec-035-gate workflow's ``pytest apps/api/tests/contract/spec_035 ...`` step),
the repo-root ``tests/conftest.py`` is not loaded because it lives in a sibling
tree. This conftest mirrors that bootstrap so first-party imports resolve the
same way:

* ``ROOT`` — enables ``from packages.domain.src...`` style imports used by
  ``apps/api/app/repositories/governance_repository.py`` and friends. The
  ``packages/`` tree is consumed as a directory namespace package (no
  ``__init__.py``); it is not pip-installed editable.
* ``API_ROOT`` — already on ``sys.path`` via ``pip install -e apps/api``, but
  added defensively so the conftest is robust to environments without the
  editable install.
* ``AGENTS_ROOT`` — symmetry with ``tests/conftest.py``; harmless when
  ``apps/agents`` is not installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
AGENTS_ROOT = ROOT / "apps" / "agents"

for path in (ROOT, API_ROOT, AGENTS_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
