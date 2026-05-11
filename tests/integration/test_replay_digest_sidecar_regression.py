"""Spec-038 T161 — Phase-7 regression lock for replay digest sidecars.

Walks every committed ``fixtures/sim_replays/*.ndjson`` and asserts that:

1. A sibling ``<file>.sha256`` sidecar exists.
2. The sidecar's recorded digest equals the SHA-256 of the file on disk
   (proves the working tree has not drifted from what was committed).
3. Re-encoding the scenario via the simulator CLI
   (``apps.api.app.services.simulation.feeds.replay --check``) reproduces
   the same digest byte-for-byte (proves the generator + canonical encoder
   chain still emit the same bytes that were committed in Phase 5/6).

Mapping: FR-022 (byte-identical replay), SC-005 (byte-identical replay),
plan R3 (canonical NDJSON / SHA-256 stream digest).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAYS = REPO_ROOT / "fixtures" / "sim_replays"

# Lazy import — avoids hard coupling to the simulator package at collection.
sys.path.insert(0, str(REPO_ROOT))
from apps.api.app.services.simulation.replay.digest import (  # noqa: E402
    compute_sha256,
    verify_sidecar,
)


def _replay_files() -> list[Path]:
    files = sorted(REPLAYS.glob("*.ndjson"))
    assert files, f"no replay fixtures discovered under {REPLAYS}"
    return files


@pytest.mark.parametrize("ndjson", _replay_files(), ids=lambda p: p.stem)
def test_committed_replay_matches_sidecar(ndjson: Path) -> None:
    """File on disk == digest recorded in sidecar (no working-tree drift)."""
    sidecar = ndjson.with_suffix(ndjson.suffix + ".sha256")
    assert sidecar.exists(), f"missing sidecar for {ndjson.name}"
    actual = verify_sidecar(ndjson)  # raises on mismatch
    assert len(actual) == 64


@pytest.mark.parametrize("ndjson", _replay_files(), ids=lambda p: p.stem)
def test_replay_cli_check_reproduces_digest(ndjson: Path) -> None:
    """Re-running the simulator CLI in --check mode must succeed for every fixture."""
    scenario = ndjson.stem
    committed_digest = compute_sha256(ndjson)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "apps.api.app.services.simulation.feeds.replay",
            "--scenario",
            scenario,
            "--seed",
            "42",
            "--check",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, (
        f"replay --check failed for {scenario}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    # The CLI prints "OK <scenario> sha256=<digest> ..." on success.
    assert committed_digest in proc.stdout, (
        f"expected digest {committed_digest} in CLI stdout for {scenario}\n"
        f"stdout={proc.stdout}"
    )


def test_at_least_21_replays_present() -> None:
    """13 simulator-feed scenarios + 8 demo scenarios = 21 fixtures (Phase 5/6)."""
    files = _replay_files()
    assert len(files) >= 21, (
        f"expected ≥21 replay fixtures (13 feeds + 8 demos), got {len(files)}: "
        f"{[p.name for p in files]}"
    )
