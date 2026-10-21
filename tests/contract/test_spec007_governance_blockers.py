from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec007_isolation


def test_spec007_has_exactly_three_governance_blocked_findings() -> None:
    feature = Path("specs/007-simulation-tenant-isolation")
    payload = json.loads((feature / "04-governance-constraints.json").read_text(encoding="utf-8"))
    report = (feature / "implementation-review-tasks.md").read_text(encoding="utf-8")

    assert payload["status"] == "GOVERNANCE-BLOCKED"
    assert payload["discovery"]["portalParity"] == "UNVERIFIED"
    assert payload["discovery"]["managementGroupInheritedAssignments"] == "UNVERIFIED"
    assert payload["discovery"]["subscriptionScopedAssignments"] == 0
    assert payload["discovery"]["restApiTotalAssignments"] == 0

    blocked = {row["id"] for row in payload["blockedFindings"]}
    unchecked = set(re.findall(r"(?m)^- \[ \] (AUD-\d{3})", report))
    checked = set(re.findall(r"(?m)^- \[x\] (AUD-\d{3})", report))
    assert blocked == {"AUD-004", "AUD-019", "AUD-022"}
    assert unchecked == blocked
    assert len(checked) == 28
