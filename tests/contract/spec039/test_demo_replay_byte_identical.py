"""Spec-039 Phase 6 — every committed demo replay matches its sidecar.

Mirror of the existing simulator-feed replay-byte-identical contract,
extended to the 8 demo scenarios (T130-T137). Re-runs each demo's
``emit()``, re-encodes the canonical NDJSON, and asserts the SHA-256
digest matches the committed ``.sha256`` sidecar.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
_API = _REPO / "apps" / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from apps.api.app.services.simulation.feeds.replay import (  # noqa: E402
    DEMO_SCENARIOS,
    _emit_records,
)
from apps.api.app.services.simulation.replay.digest import compute_sha256  # noqa: E402
from apps.api.app.services.simulation.replay.ndjson_writer import write_ndjson  # noqa: E402

REPLAY_DIR = _REPO / "fixtures" / "sim_replays"


@pytest.mark.parametrize("scenario", sorted(DEMO_SCENARIOS))
def test_demo_replay_matches_committed_sidecar(scenario: str, tmp_path: Path) -> None:
    records = _emit_records(scenario, seed=42, count=8)
    out = tmp_path / f"{scenario}.ndjson"
    digest = write_ndjson(records, out)
    committed = REPLAY_DIR / f"{scenario}.ndjson"
    assert committed.exists(), committed
    committed_digest = compute_sha256(committed)
    assert digest == committed_digest, (
        f"{scenario}: replay byte drift recomputed={digest} committed={committed_digest}"
    )
    sidecar = REPLAY_DIR / f"{scenario}.ndjson.sha256"
    assert sidecar.exists(), sidecar
    assert sidecar.read_text(encoding="utf-8").startswith(committed_digest)
