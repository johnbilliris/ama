"""End-to-end publish: schema → ratio → cosmos/blob/audit (T034 + T035 wiring).

Citations: FR-005, FR-035, NN-2, PD-037-04.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def test_publish_emits_audit_and_no_pii(tmp_path: Path):
    from app.services.governance.evidence_pack_writer import publish_artefact

    sidecar = tmp_path / "risk-register.json"
    sidecar.write_text(
        json.dumps(
            {
                "artefact_id": "risk_register",
                "schema_version": "1.0.0",
                "metadata": {"link_check_status": "passed"},
                "rows": [
                    {"provenance": {"tag": "automated"}},
                    {"provenance": {"tag": "manual"}},
                ],
            }
        ),
        encoding="utf-8",
    )

    cosmos_calls: list[dict] = []
    blob_calls: list[dict] = []
    audit_calls: list[dict] = []

    def cosmos(payload):
        cosmos_calls.append(payload)

    def blob(*, artefact_id, publication_id, payload):
        blob_calls.append({"id": artefact_id, "pub": publication_id})

    def audit(**kwargs):
        audit_calls.append(kwargs)

    res = publish_artefact(
        sidecar,
        published_by="00000000-0000-0000-0000-aaaaaaaaaaaa",  # Entra OID, no PII
        cosmos_writer=cosmos,
        blob_writer=blob,
        audit_writer=audit,
    )
    assert res.manual_row_ratio == 0.5
    assert len(cosmos_calls) == 1
    assert len(blob_calls) == 1
    assert len(audit_calls) == 1
    assert audit_calls[0]["event_type"] == "evidence_pack.publish"

    # NN-2: no PII pattern (email or phone) in any audit payload.
    serialised = json.dumps(audit_calls)
    assert not re.search(r"[\w.-]+@[\w.-]+\.\w+", serialised), "audit must not contain emails"
    assert not re.search(r"\+?\d{8,}", serialised.replace("00000000", "X")), "audit must not contain phone numbers"
