"""HITL non-bypassability static-analysis test (T047, NN-1).

Asserts the ONLY module that calls ``Workflow.send_response`` (or its
local-equivalent ``HitlDecisionListener.on_decision_received`` resume path) is
``apps/agents/maf_runtime/workflow/hitl_request_port.py``.

Note: the GA Python MAF SDK at 1.2.2 does not expose ``Workflow.send_response``
publicly — see ADR-033-03. The non-bypassability invariant for this feature
therefore guards against ANY module re-implementing the resume path:

1. No module under ``apps/agents/maf_runtime/`` outside ``hitl_request_port.py``
   may import or reference ``HitlDecisionListener.on_decision_received``.
2. No module may publish to spec-008's ``commander-approval-queue`` outside the
   single allowed publisher inside ``hitl_request_port.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAF_PKG = REPO_ROOT / "apps" / "agents" / "maf_runtime"
HITL_FILE = MAF_PKG / "workflow" / "hitl_request_port.py"


_RESUME_REF = re.compile(r"on_decision_received|HitlDecisionListener")
_PUBLISH_QUEUE = re.compile(r"['\"]commander-approval-queue['\"]")


def test_only_hitl_module_resumes_workflows() -> None:
    offenders: list[str] = []
    for fp in sorted(MAF_PKG.rglob("*.py")):
        if fp.resolve() == HITL_FILE.resolve():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        if _RESUME_REF.search(text):
            offenders.append(fp.relative_to(REPO_ROOT).as_posix())
    assert not offenders, (
        "NN-1 violation: only `apps/agents/maf_runtime/workflow/hitl_request_port.py` "
        "may reference `HitlDecisionListener` / `on_decision_received`. Offenders: " + ", ".join(offenders)
    )


def test_only_hitl_module_publishes_to_commander_queue() -> None:
    offenders: list[str] = []
    for fp in sorted(MAF_PKG.rglob("*.py")):
        if fp.resolve() == HITL_FILE.resolve():
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        if _PUBLISH_QUEUE.search(text):
            offenders.append(fp.relative_to(REPO_ROOT).as_posix())
    assert not offenders, (
        "NN-1 violation: only `apps/agents/maf_runtime/workflow/hitl_request_port.py` "
        "may publish to `commander-approval-queue`. Offenders: " + ", ".join(offenders)
    )
