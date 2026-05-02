"""Append-only audit helper for the spec-034 Python tooling.

Coverage-trace, gap-register, review-log, and known-good CLIs all mutate
markdown source-of-truth files and shadow the operation into an audit JSONL
file under ``specs/034-webapp-capstone-coverage/_evidence/audit/``.

The shadow is append-only and timestamped to the minute so a tribunal review
can replay every state change deterministically.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def append_audit(audit_root: Path, audit_type: str, payload: dict[str, Any]) -> Path:
    """Append a JSONL row and return the path written to.

    File layout: ``{audit_root}/{YYYY-MM-DD}/{HH}.jsonl``.
    Mirrors the Blob storage layout described in
    ``contracts/gap-register-entry.schema.json`` description.
    """

    now = datetime.now(UTC)
    day = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")
    bucket = audit_root / day
    bucket.mkdir(parents=True, exist_ok=True)
    target = bucket / f"{hour}.jsonl"
    line = json.dumps(
        {
            "audit_type": audit_type,
            "emitted_at": now.isoformat(timespec="seconds"),
            "payload": payload,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    with target.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
        fh.write("\n")
    return target
