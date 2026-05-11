"""Shared fixtures for spec-039 unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = _REPO_ROOT / "apps" / "api"

for _p in (_REPO_ROOT, _API_ROOT):
    sp = str(_p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
