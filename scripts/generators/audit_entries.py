"""Spec-038 T113 — append-only audit entries generator (FR-050).

Includes deliberate compliance-gap rows so downstream audit-replay tests
have something interesting to enforce against.
"""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "audit_entries"
GENERATOR_VERSION = "1.0.0"

_ACTIONS = ("scenario.created", "scenario.advanced", "decision.recorded",
            "approval.granted", "approval.denied", "data.exported",
            "rbac.role.assigned", "config.changed")
_ACTORS = ("incident-commander", "operations-officer", "executive-leader",
           "observer-auditor", "system")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        # Every 10th record is a deliberate compliance-gap example.
        is_gap = (i % 10 == 9)
        body = {
            "action": _ACTIONS[rng.randrange(len(_ACTIONS))],
            "actor": _ACTORS[rng.randrange(len(_ACTORS))],
            "ts_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 5) % 24:02d}:{(i * 7) % 60:02d}:00Z",
            "outcome": "denied" if is_gap else "ok",
            "compliance_gap": is_gap,
            "compliance_gap_reason": "FICTITIOUS — missing approval citation" if is_gap else None,
            "summary": f"FICTITIOUS audit row {i:04d} — TEST DATA",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"audit-{i:06d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
