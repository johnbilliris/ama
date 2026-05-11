"""Pillar B — Measurement-Method renderer (T-B03, FR-007/009)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from .._summariser import summarise_blocks
from ..kpi_ladder.repository import list_published

CAPSTONE_DEFINITIONS: dict[str, dict[str, str]] = {
    "SC-CAP-015-001": {
        "name": "Lives saved",
        "plain": "Estimated lives preserved versus the prototype-baseline run.",
        "start": "Triage decision recorded",
        "end": "Patient outcome recorded (12-h horizon)",
        "missing_rule": "Forward-impute next-adjacent canonical event; row excluded from CI.",
        "calibration": "Bootstrap-95% CI vs historical mortality benchmark.",
    },
    "SC-CAP-015-002": {
        "name": "Response time",
        "plain": "Median elapsed time from call-received to on-scene arrival.",
        "start": "call_received_at",
        "end": "arrived_at",
        "missing_rule": "Forward-impute from controlled_at/dispatched_at.",
        "calibration": "Bootstrap-95% CI vs jurisdiction Pri-1 ambulance benchmark.",
    },
    "SC-CAP-015-003": {
        "name": "Evacuation lead time",
        "plain": "Hours between hazard warning issuance and evacuation completion.",
        "start": "Warning issued",
        "end": "Evacuation completion confirmed",
        "missing_rule": "Forward-impute from BoM warning timestamp.",
        "calibration": "Bootstrap-95% CI vs BoM hazard warning lead-time.",
    },
    "SC-CAP-015-004": {
        "name": "Logistics efficiency",
        "plain": "Asset-utilisation uplift (% optimised routes accepted).",
        "start": "Resource request raised",
        "end": "Resource on-task",
        "missing_rule": "Forward-impute from dispatched_at.",
        "calibration": "Bootstrap-95% CI vs spec-015 prototype baseline.",
    },
    "SC-CAP-015-005": {
        "name": "Economic loss reduction",
        "plain": "Estimated AUDm avoided versus the prototype-baseline run.",
        "start": "Risk-exposure snapshot at T-0",
        "end": "Post-event loss assessment",
        "missing_rule": "Forward-impute from controlled_at; CI excludes imputed rows.",
        "calibration": "Bootstrap-95% CI vs spec-015 prototype baseline + AFAC FDI.",
    },
}


def build_definitions() -> list[dict]:
    indicators = list_published()
    out = []
    for sc, base in CAPSTONE_DEFINITIONS.items():
        sample_indicator = next((i for i in indicators if i.capstone_sc_id == sc), None)
        rule = sample_indicator.confidence_band_rule if sample_indicator else None
        out.append(
            {
                "capstone_sc_id": sc,
                "plain_language_definition": base["plain"],
                "start_signal": base["start"],
                "end_signal": base["end"],
                "missing_timestamp_rule": base["missing_rule"],
                "calibration_method": base["calibration"],
                "confidence_band_rule": (
                    rule.model_dump()
                    if rule
                    else {
                        "method": "bootstrap_p2_5_p97_5",
                        "min_resamples": 1000,
                    }
                ),
            }
        )
    return out


def render(format: Literal["json", "markdown"] = "json") -> dict | str:
    defs = build_definitions()
    payload = {
        "version": "1",
        "generated_at": datetime.now(UTC).isoformat(),
        "definitions": defs,
        "ama_advisory_only": True,
    }
    if format == "json":
        return payload
    blocks = ["# Measurement Method (spec 038)\n"]
    for d in defs:
        sc = d["capstone_sc_id"]
        info = CAPSTONE_DEFINITIONS[sc]
        blocks.append(
            f"## {sc} — {info['name']}\n\n"
            f"{d['plain_language_definition']}\n\n"
            f"- **Start signal**: {d['start_signal']}\n"
            f"- **End signal**: {d['end_signal']}\n"
            f"- **Missing-timestamp rule**: {d['missing_timestamp_rule']}\n"
            f"- **Calibration method**: {d['calibration_method']}\n"
        )
    blocks.append("> Advisory only — no autonomous action. (FR-030)\n")
    return summarise_blocks(blocks, max_chars=8000)
