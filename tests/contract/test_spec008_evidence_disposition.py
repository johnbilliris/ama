from __future__ import annotations

import json
import re
from pathlib import Path

FEATURE = Path("specs/008-communication-agent")


def test_spec008_has_exactly_four_open_findings() -> None:
    report = (FEATURE / "implementation-review-tasks.md").read_text(encoding="utf-8")

    checked = set(re.findall(r"(?m)^- \[x\] (AUD-008-\d{3})", report))
    unchecked = set(re.findall(r"(?m)^- \[ \] (AUD-008-\d{3})", report))

    assert len(checked) == 34
    assert unchecked == {"AUD-008-031", "AUD-008-035", "AUD-008-036", "AUD-008-037"}


def test_spec008_governance_and_approval_evidence_do_not_overclaim() -> None:
    governance = json.loads((FEATURE / "04-governance-constraints.json").read_text(encoding="utf-8"))
    approvals = json.loads((FEATURE / "evidence/template-approval-manifest.json").read_text(encoding="utf-8"))
    resolution = json.loads((FEATURE / "contracts/contract-resolution.v2.json").read_text(encoding="utf-8"))

    assert governance["status"] == "GOVERNANCE-BLOCKED"
    assert governance["discovery"]["portalParity"] == "UNVERIFIED"
    assert governance["blockedFindings"] == [
        {
            "id": "AUD-008-031",
            "requiredChange": (
                "Integrate the communication runtime and apply policy-cleared least-privilege identity, "
                "Cosmos, Service Bus, scaling, and regional configuration"
            ),
        }
    ]
    assert approvals["approvalStatus"] == "UNVERIFIED"
    assert approvals["nativeLanguageReview"] == "UNVERIFIED"
    assert resolution["approval"]["humanGovernanceApproval"] == "UNVERIFIED"


def test_spec008_hypotheses_remain_unpromoted() -> None:
    for hypothesis in ("HYP-006.md", "HYP-027.md", "HYP-028.md", "HYP-029.md"):
        text = (FEATURE / "evidence" / hypothesis).read_text(encoding="utf-8")
        assert re.search(r"(?m)^## Status\n(?:\n)?Not tested$", text)
