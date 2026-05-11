"""Pillar D — Causal chain seed (T-D06, SC-006).

Seeds one chain per AMA capability listed in the spec (specs 008-012, 036,
036-sim-agent-extend). Real text would be sourced from each origin spec; we
stub representative content so SC-006 (every capability has ≥1 chain) holds.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from decimal import Decimal

from ..models.chain import Assumption, CausalChain, ThreatToValidity

CAPABILITIES: list[dict] = [
    {
        "capability_id": "risk-assessment-agent",
        "spec": "specs/008-risk-assessment-agent/spec.md",
        "name": "Risk Assessment Agent",
        "kpis": ["lives_saved_lagging", "econ_loss_lagging"],
        "magnitude": Decimal("15.0000"),
        "unit": "pct uplift",
    },
    {
        "capability_id": "evacuation-agent",
        "spec": "specs/009-evacuation-agent/spec.md",
        "name": "Evacuation Agent",
        "kpis": ["evac_lead_lagging"],
        "magnitude": Decimal("24.0000"),
        "unit": "hours",
    },
    {
        "capability_id": "communication-agent",
        "spec": "specs/010-communication-agent/spec.md",
        "name": "Communication Agent",
        "kpis": ["public_info_alert_reach"],
        "magnitude": Decimal("20.0000"),
        "unit": "pct reach",
    },
    {
        "capability_id": "resource-allocation-agent",
        "spec": "specs/011-resource-allocation-agent/spec.md",
        "name": "Resource Allocation Agent",
        "kpis": ["logistics_efficiency"],
        "magnitude": Decimal("30.0000"),
        "unit": "pct uplift",
    },
    {
        "capability_id": "monitoring-agent",
        "spec": "specs/012-monitoring-agent/spec.md",
        "name": "Monitoring Agent",
        "kpis": ["response_time_p1"],
        "magnitude": Decimal("45.0000"),
        "unit": "pct reduction",
    },
    {
        "capability_id": "foundry-rag-client",
        "spec": "specs/036-foundry-rag-client/spec.md",
        "name": "Foundry RAG Client",
        "kpis": ["lives_saved_leading"],
        "magnitude": Decimal("10.0000"),
        "unit": "pct uplift",
    },
    {
        "capability_id": "telemetry-injection-agent",
        "spec": "specs/036-sim-agent-extend/spec.md",
        "name": "Telemetry-Injection Agent",
        "kpis": ["evac_warning_leading"],
        "magnitude": Decimal("12.0000"),
        "unit": "minutes earlier",
    },
]


def seed_chains() -> list[CausalChain]:
    out: list[CausalChain] = []
    for cap in CAPABILITIES:
        out.append(
            CausalChain(
                id=secrets.token_hex(13),
                capability_id=cap["capability_id"],
                capability_name=cap["name"],
                version=1,
                kpis_moved=cap["kpis"],
                expected_magnitude_value=cap["magnitude"],
                expected_magnitude_unit=cap["unit"],
                assumptions=[
                    Assumption(text=f"{cap['name']} integrates with AIIMS function", resolved=True),
                    Assumption(text="Operator accepts agent recommendation in <60s", resolved=False),
                ],
                threats_to_validity=[
                    ThreatToValidity(text="Telemetry source lag > 60s", severity="medium"),
                    ThreatToValidity(text="Out-of-domain scenario regression", severity="low"),
                ],
                originating_spec_path=cap["spec"],
                created_at=datetime.now(UTC),
            )
        )
    return out
