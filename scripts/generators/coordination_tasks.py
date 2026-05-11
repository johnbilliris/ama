"""Spec-039 T111 — coordination tasks generator (FR-050)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "coordination_tasks"
GENERATOR_VERSION = "1.0.0"

_TASK_TYPES = ("evacuation", "resupply", "welfare-check", "traffic-mgmt",
               "shelter-stand-up", "perimeter-control", "rescue", "mortuary",
               "comms-restoration")
_OWNER_GROUPS = ("operational", "fire", "police", "ses", "ambulance",
                 "marine-aviation", "commonwealth", "cross-sector")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    for i in range(count):
        body = {
            "task_type": _TASK_TYPES[rng.randrange(len(_TASK_TYPES))],
            "owner_group": _OWNER_GROUPS[rng.randrange(len(_OWNER_GROUPS))],
            "priority": rng.choice(["P1", "P2", "P3", "P4"]),
            "status": rng.choice(["open", "in-progress", "blocked", "complete"]),
            "due_iso": f"2026-01-{(1 + i % 28):02d}T{(i * 2) % 24:02d}:30:00Z",
            "summary": f"FICTITIOUS coordination task {i:04d} — TEST DATA",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"coord-task-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
