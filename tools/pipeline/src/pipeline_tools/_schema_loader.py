"""Schema loader (resolves package-shipped schemas + fallback to repo `contracts/`)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_CONTRACTS = Path(__file__).resolve().parents[3].parent / "contracts"


def load(name: str) -> dict[str, Any]:
    """Load a JSON schema by filename. Tries package-shipped copy first, then repo `contracts/`."""
    pkg_dir = Path(__file__).resolve().parent / "schemas"
    candidate = pkg_dir / name
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    repo_candidate = _REPO_CONTRACTS / name
    if repo_candidate.exists():
        return json.loads(repo_candidate.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"Schema '{name}' not found in package schemas/ or repo contracts/. "
        f"Tried: {candidate}, {repo_candidate}"
    )
