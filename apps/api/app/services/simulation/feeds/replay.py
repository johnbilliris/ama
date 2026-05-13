"""Spec-039 T078: replay CLI for the simulator feed shapes.

Run a deterministic end-to-end replay::

    python -m apps.api.app.services.simulation.feeds.replay \
        --scenario bom_severe_weather_warning_nsw --seed 42

Lookups:

  * The ``--scenario`` argument is a kebab-case ``<shape>_<jurisdiction>``
    identifier (e.g. ``bom_severe_weather_warning_nsw``) — this is the
    same naming committed under ``fixtures/sim_replays/``.
  * The seed defaults to the resolved value from
    :func:`scripts.generators._seed_contract.resolve_seed` (function-arg
    > CLI > env ``AMA_TEST_SEED`` > 0; default 0 emits a UserWarning).

Output (default):
  * ``fixtures/sim_replays/<scenario>.ndjson`` (overwritten) plus
    ``<scenario>.ndjson.sha256`` sidecar.
  * Prints ``OK <scenario> sha256=<digest> records=<n>`` to stdout.
  * Exits 0 on success, non-zero on schema/digest failure.

Use ``--out <path>`` to write somewhere other than ``fixtures/sim_replays``.
Use ``--check`` to re-encode and assert the digest matches an existing
sidecar (no file is written) — used by CI replay-pinning (T161).
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

# scripts is a top-level package in the repo root.
_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.generators._seed_contract import resolve_seed  # noqa: E402

from ._canonical import SimulatedClock  # noqa: E402

# Map single-feed scenario id -> (module_name, jurisdiction).
SCENARIOS: dict[str, tuple[str, str]] = {
    "bom_severe_weather_warning_nsw": ("bom_severe_weather_warning", "nsw"),
    "bom_cyclone_track_qld": ("bom_cyclone_track", "qld"),
    "bom_fire_weather_fdi_vic": ("bom_fire_weather_fdi", "vic"),
    "bom_flood_gauge_nsw": ("bom_flood_gauge", "nsw"),
    "ga_earthquake_event_wa": ("ga_earthquake_event", "wa"),
    "ga_tsunami_threat_nsw": ("ga_tsunami_threat", "nsw"),
    "epa_pm25_vic": ("epa_pm25", "vic"),
    "traffic_road_closure_nsw": ("traffic_road_closure", "nsw"),
    "utility_outage_qld": ("utility_outage", "qld"),
    "ambulance_cad_vic": ("ambulance_cad", "vic"),
    "social_chatter_au": ("social_chatter", "au"),
    "sensor_telemetry_nt": ("sensor_telemetry", "nt"),
    "synthetic_fallback_au": ("synthetic_fallback", "au"),
}

# Spec-039 Phase 6 demo scenarios (T130-T137). Each maps the snake-case
# CLI id to the corresponding ``feeds.scenarios.*`` module name.
DEMO_SCENARIOS: dict[str, str] = {
    "demo_operational_v1": "operational_demo",
    "demo_fire_v1": "fire_demo",
    "demo_police_v1": "police_demo",
    "demo_ambulance_v1": "ambulance_demo",
    "demo_ses_v1": "ses_demo",
    "demo_marine_aviation_v1": "marine_aviation_demo",
    "demo_commonwealth_v1": "commonwealth_demo",
    "demo_cross_sector_v1": "cross_sector_demo",
}


def _default_out_dir() -> Path:
    return _REPO / "fixtures" / "sim_replays"


def _emit_records(scenario: str, seed: int, count: int):
    if scenario in DEMO_SCENARIOS:
        # Demo scenario — orchestrator decides record count; ``count`` ignored.
        mod = importlib.import_module(f"apps.api.app.services.simulation.feeds.scenarios.{DEMO_SCENARIOS[scenario]}")
        return list(mod.emit(seed))
    if scenario not in SCENARIOS:
        raise SystemExit(
            f"unknown scenario {scenario!r}; known feeds: {sorted(SCENARIOS)}; demos: {sorted(DEMO_SCENARIOS)}"
        )
    module_name, jurisdiction = SCENARIOS[scenario]
    mod = importlib.import_module(f"apps.api.app.services.simulation.feeds.{module_name}")
    # Schema requires kebab-case scenario_id; the CLI uses snake_case for
    # consistency with the underlying module filename.
    scenario_id = scenario.replace("_", "-")
    clk = SimulatedClock(scenario_id, seed)
    return list(mod.emit(scenario_id, seed, jurisdiction=jurisdiction, count=count, clock=clk))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", required=True, choices=sorted(set(SCENARIOS) | set(DEMO_SCENARIOS)))
    p.add_argument("--seed", type=int, default=None, help="64-bit unsigned seed; falls back to AMA_TEST_SEED then 0.")
    p.add_argument("--count", type=int, default=8, help="Records to emit (default: 8).")
    p.add_argument(
        "--out", type=Path, default=None, help="Output ndjson path (default: fixtures/sim_replays/<scenario>.ndjson)."
    )
    p.add_argument(
        "--check", action="store_true", help="Re-encode and verify against committed sidecar; do not overwrite."
    )
    args = p.parse_args(argv)

    seed = resolve_seed(fn_arg=None, cli_arg=args.seed)
    records = _emit_records(args.scenario, seed, args.count)

    # Lazy imports so --help works even if the replay sub-package is being edited.
    from ..replay.digest import compute_sha256, verify_sidecar  # noqa: E402
    from ..replay.ndjson_writer import write_ndjson  # noqa: E402

    if args.check:
        # Re-encode to a temp path, then verify against committed sidecar.
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / f"{args.scenario}.ndjson"
            digest = write_ndjson(records, tmp)
            committed = _default_out_dir() / f"{args.scenario}.ndjson" if args.out is None else args.out
            if not committed.exists():
                print(f"FAIL {args.scenario}: committed fixture missing at {committed}", file=sys.stderr)
                return 2
            committed_digest = compute_sha256(committed)
            if digest != committed_digest:
                print(
                    f"FAIL {args.scenario}: digest drift — recomputed={digest} committed={committed_digest}",
                    file=sys.stderr,
                )
                return 1
            verify_sidecar(committed)
            print(f"OK {args.scenario} sha256={digest} records={len(records)} (verified)")
            return 0

    out_path = args.out or (_default_out_dir() / f"{args.scenario}.ndjson")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    digest = write_ndjson(records, out_path)
    verify_sidecar(out_path)
    print(f"OK {args.scenario} sha256={digest} records={len(records)} -> {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
