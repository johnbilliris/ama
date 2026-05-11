"""Shared fixtures for spec-039 contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root and apps/api are on sys.path so `from app...` and
# `from packages...` imports resolve in test runs that don't go through an
# editable install of every package.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = _REPO_ROOT / "apps" / "api"

for _p in (_REPO_ROOT, _API_ROOT):
    sp = str(_p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
