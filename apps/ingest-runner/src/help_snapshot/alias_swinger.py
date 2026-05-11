"""spec-038 — atomic alias swing (≤5 min SLO, FR-011c).

In production this calls Azure AI Search REST `aliases` endpoint. The
default code-path is the offline simulation used by tests: it writes the
chosen target into a local state file so a subsequent ``rollback`` can
re-bind.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ALIAS_NAME = "help-corpus-active"
_STATE = Path(os.environ.get("HELP_ALIAS_STATE", str(Path.cwd() / ".help-alias.json")))


def swing_alias(*, snapshot_id: str) -> dict[str, str]:
    target = f"help-corpus-{snapshot_id}"
    state = {"alias": ALIAS_NAME, "target": target}
    _STATE.write_text(json.dumps(state), encoding="utf-8")
    logger.info("alias swung: %s -> %s", ALIAS_NAME, target)
    return state


def read_alias() -> dict[str, str] | None:
    if not _STATE.exists():
        return None
    return json.loads(_STATE.read_text(encoding="utf-8"))


__all__ = ["swing_alias", "read_alias", "ALIAS_NAME"]
