from __future__ import annotations

from decimal import Decimal

from .._clients import get_registry
from ..instrumentation import audit_manager
from .scorecard_builder import NamedAuditorSignoff


class AuditImputationSignoffResolver:
    def resolve(
        self,
        *,
        scenario_id: str,
        run_pair_id: str,
        scenario_content_hash: str | None,
        imputation_share: Decimal,
    ) -> NamedAuditorSignoff | None:
        rows = get_registry().get("evidence_audit").all()
        expected_share = str(imputation_share.normalize())
        for row in reversed(rows):
            payload = row.get("payload", {})
            if (
                row.get("kind") == "auditor_signoff_recorded"
                and row.get("actor") not in {"system", "seed", "anonymous"}
                and payload.get("authenticated") is True
                and payload.get("signoff_type") == "imputation"
                and payload.get("scenario_id") == scenario_id
                and payload.get("run_pair_id") == run_pair_id
                and payload.get("scenario_content_hash") == scenario_content_hash
                and payload.get("imputation_share") == expected_share
                and payload.get("auditor_id") == row.get("actor")
                and payload.get("approval_id")
            ):
                return NamedAuditorSignoff(
                    approval_id=str(payload["approval_id"]),
                    auditor_id=str(payload["auditor_id"]),
                )
        return None


def record_imputation_signoff(
    *,
    scenario_id: str,
    run_pair_id: str,
    scenario_content_hash: str | None,
    imputation_share: Decimal,
    auditor_id: str,
    approval_id: str,
    basis: str,
    correlation_id: str,
) -> None:
    if auditor_id in {"", "system", "seed", "anonymous"}:
        raise PermissionError("authenticated named auditor identity is required")
    if not approval_id.strip() or len(basis.strip()) < 8:
        raise ValueError("approval_id and a substantive basis are required")
    audit_manager.record(
        kind="auditor_signoff_recorded",
        value_id=f"imputation:{run_pair_id}",
        actor=auditor_id,
        payload={
            "authenticated": True,
            "signoff_type": "imputation",
            "scenario_id": scenario_id,
            "run_pair_id": run_pair_id,
            "scenario_content_hash": scenario_content_hash,
            "imputation_share": str(imputation_share.normalize()),
            "auditor_id": auditor_id,
            "approval_id": approval_id,
            "basis": basis,
        },
        correlation_id=correlation_id,
    )
