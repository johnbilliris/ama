from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TypedDict

from ..models.chain import Assumption, CausalChain, ThreatToValidity


class _Capability(TypedDict):
    capability_id: str
    spec: str
    requirement: str
    name: str
    claim: str
    kpis: list[str]


CAPABILITIES: tuple[_Capability, ...] = (
    {
        "capability_id": "communication-agent",
        "spec": "specs/008-communication-agent/spec.md",
        "requirement": "FR-005",
        "name": "Communication Agent",
        "claim": "Reviewed multilingual alerts may improve public-information reach.",
        "kpis": ["public_info_alert_reach"],
    },
    {
        "capability_id": "evacuation-agent",
        "spec": "specs/009-evacuation-agent/spec.md",
        "requirement": "FR-014",
        "name": "Evacuation Agent",
        "claim": "Capacity-aware evacuation planning may increase usable evacuation lead time.",
        "kpis": ["evac_lead_lagging"],
    },
    {
        "capability_id": "monitoring-agent",
        "spec": "specs/010-monitoring-agent/spec.md",
        "requirement": "FR-010",
        "name": "Monitoring Agent",
        "claim": "Timely, confidence-bearing signal handoffs may reduce incident control time.",
        "kpis": ["response_time_p1"],
    },
    {
        "capability_id": "resource-allocation-agent",
        "spec": "specs/011-resource-allocation-agent/spec.md",
        "requirement": "FR-011",
        "name": "Resource Allocation Agent",
        "claim": "Constraint-aware demand matching may improve measured logistics efficiency.",
        "kpis": ["logistics_efficiency"],
    },
    {
        "capability_id": "risk-assessment-agent",
        "spec": "specs/012-risk-assessment-agent/spec.md",
        "requirement": "FR-011",
        "name": "Risk Assessment Agent",
        "claim": "Multi-source correlation may improve harm-reduction recommendations.",
        "kpis": ["lives_saved_lagging", "econ_loss_lagging"],
    },
    {
        "capability_id": "foundry-rag-client",
        "spec": "specs/036-foundry-rag-grounding/spec.md",
        "requirement": "FR-RAG-AG-04",
        "name": "Foundry RAG Client",
        "claim": "Jurisdiction-grounded retrieval may reduce unsupported decision context.",
        "kpis": ["lives_saved_leading"],
    },
    {
        "capability_id": "telemetry-injection-agent",
        "spec": "specs/036-sim-agent-extend/spec.md",
        "requirement": "FR-009",
        "name": "Telemetry-Injection Agent",
        "claim": "Provenance-complete synthetic signals may improve replay measurement fidelity.",
        "kpis": ["evac_warning_leading"],
    },
)


def seed_chains() -> list[CausalChain]:
    created_at = datetime.now(UTC)
    return [
        CausalChain(
            id=secrets.token_hex(13),
            capability_id=capability["capability_id"],
            capability_name=capability["name"],
            version=1,
            claim=capability["claim"],
            kpis_moved=capability["kpis"],
            magnitude_status="hypothesis",
            assumptions=[
                Assumption(
                    id=f"{capability['capability_id']}-integration",
                    text="The capability is connected to the measured scenario event stream.",
                    validation_method="Resolve emitted signal IDs in a persisted baseline/assisted replay.",
                    evidence_required="Replay trace containing source event, capability version, and KPI value IDs.",
                    owner_role="observer-auditor",
                ),
                Assumption(
                    id=f"{capability['capability_id']}-decision",
                    text="A human-approved decision uses the capability output before the measured outcome.",
                    validation_method="Walk recommendation and approval IDs in the audit trace.",
                    evidence_required="Named approver, decision timestamp, recommendation ID, and outcome ID.",
                    owner_role="incident-commander",
                ),
            ],
            threats_to_validity=[
                ThreatToValidity(
                    text="Scenario mix or event quality may explain an observed change.",
                    severity="high",
                    mitigation=(
                        "Compare identical seeded baseline and assisted event sets and disclose missing sources."
                    ),
                ),
                ThreatToValidity(
                    text="The observed result may not transfer from a prototype exercise to a live incident.",
                    severity="high",
                    mitigation="Keep the claim advisory and require independent operational evidence.",
                ),
            ],
            originating_spec_path=capability["spec"],
            originating_requirement=capability["requirement"],
            created_at=created_at,
        )
        for capability in CAPABILITIES
    ]
