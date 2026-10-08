from __future__ import annotations

import json
import re
from pathlib import Path

REQUIRED_CLAIMS = {
    "T085-QUICKSTART-A-I": "UNVERIFIED",
    "PLAN-CONSTITUTION-PASS": "UNVERIFIED",
    "HYP-004-UPLIFT": "UNVERIFIED",
    "RISK-NEW-013-TREATMENT": "PARTIAL",
    "PROVIDER-ACCESS-VERIFICATION": "DEFERRED",
    "SOURCE-DOC-REVIEW-COMPLETENESS": "DEFERRED",
    "COUNTRY-GATES-FR-CAP-006-001-003": "DEFERRED",
    "PORTFOLIO-RUBRIC-POSTFEATURE": "VERIFIED",
}


def test_aud043_manifest_has_required_claim_rows_and_statuses() -> None:
    manifest_path = Path("specs/006-data-ingestion-storage/evidence/claim-manifest.aud-043.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    claims = {row["claimId"]: row for row in payload["claims"]}
    for claim_id, expected_status in REQUIRED_CLAIMS.items():
        assert claim_id in claims
        row = claims[claim_id]
        assert row["status"] == expected_status
        assert str(row.get("artifact", "")).strip()
        assert str(row.get("reason", "")).strip()


def test_hyp_044_stub_matches_six_heading_not_tested_contract() -> None:
    path = Path("specs/006-data-ingestion-storage/evidence/HYP-044.md")
    text = path.read_text(encoding="utf-8")

    required_headings = [
        "## Hypothesis",
        "## Preconditions",
        "## Measurement Window",
        "## Falsification Criterion",
        "## Status",
        "## Linked",
    ]
    for heading in required_headings:
        assert heading in text

    assert re.search(r"(?m)^## Status\s*\n+\s*Not tested\s*$", text)
    assert text.count("- ") >= 4
