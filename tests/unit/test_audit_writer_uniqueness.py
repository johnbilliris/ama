"""Static-analysis test enforcing single-writer invariant for audit_entries (T020b, NN-3)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAF_PKG = REPO_ROOT / "apps" / "agents" / "maf_runtime"
ALLOWED_WRITER = MAF_PKG / "middleware" / "audit_middleware.py"


_AUDIT_CONTAINER_REF = re.compile(
    r"""(?:get_container_client\s*\(\s*['"]audit_entries['"]\s*\))""",
    re.IGNORECASE,
)


def test_only_audit_middleware_writes_to_audit_entries() -> None:
    offenders: list[str] = []
    for fp in sorted(MAF_PKG.rglob("*.py")):
        if fp.resolve() == ALLOWED_WRITER.resolve():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        if _AUDIT_CONTAINER_REF.search(text):
            offenders.append(fp.relative_to(REPO_ROOT).as_posix())
    assert not offenders, (
        "NN-3 violation: only `apps/agents/maf_runtime/middleware/audit_middleware.py` "
        "may open a Cosmos container client against `audit_entries`. Offenders: "
        + ", ".join(offenders)
    )
