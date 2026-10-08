# Persistence helpers for idempotent delta scorecards.

from __future__ import annotations

import hashlib
import threading
from typing import Any

from .._clients import get_registry
from ..models.scorecard import DeltaScorecard

CONTAINER = "delta_scorecards"
_lock = threading.RLock()


def _model_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in row.items() if not key.startswith("_")}
    determinism = cleaned.get("determinism")
    if isinstance(determinism, dict):
        determinism = dict(determinism)
        determinism.pop("reproduction_rate", None)
        cleaned["determinism"] = determinism
    return cleaned


class RunPairIdentityConflict(ValueError):
    pass


def scorecard_id_for(run_pair_id: str) -> str:
    digest = hashlib.sha256(f"delta-scorecard|{run_pair_id}".encode()).hexdigest()
    return digest[:26]


def get_scorecard(scorecard_id: str) -> DeltaScorecard | None:
    try:
        row = get_registry().get(CONTAINER).read_item(scorecard_id)
    except KeyError:
        return None
    return DeltaScorecard.model_validate(_model_row(row))


def get_by_run_pair(run_pair_id: str) -> DeltaScorecard | None:
    expected_id = scorecard_id_for(run_pair_id)
    direct = get_scorecard(expected_id)
    if direct is not None and direct.run_pair_id == run_pair_id:
        return direct
    rows = get_registry().get(CONTAINER).all()
    matches = [row for row in rows if row.get("run_pair_id") == run_pair_id]
    if not matches:
        return None
    matches.sort(key=lambda row: (str(row.get("created_at", "")), str(row.get("id", ""))), reverse=True)
    return DeltaScorecard.model_validate(_model_row(matches[0]))


def _same_identity(existing: DeltaScorecard, candidate: DeltaScorecard) -> bool:
    return (
        existing.scenario_id == candidate.scenario_id
        and existing.seed == candidate.seed
        and existing.id == candidate.id
    )


def _resolve_existing(candidate: DeltaScorecard) -> DeltaScorecard | None:
    existing = get_by_run_pair(candidate.run_pair_id)
    if existing is None:
        return None
    if not _same_identity(existing, candidate):
        raise RunPairIdentityConflict(
            f"run_pair_id {candidate.run_pair_id} is already bound to another scenario or seed"
        )
    return existing


def persist_scorecard(scorecard: DeltaScorecard) -> DeltaScorecard:
    # A deterministic document identity makes retried and racing POST requests safe.
    with _lock:
        existing = _resolve_existing(scorecard)
        if existing is not None:
            return existing
        container = get_registry().get(CONTAINER)
        try:
            container.create_item(scorecard.model_dump(mode="json", exclude_computed_fields=True))
        except Exception:
            winner = _resolve_existing(scorecard)
            if winner is not None:
                return winner
            raise
        return scorecard


def list_scorecards(*, scenario_id: str | None = None) -> list[DeltaScorecard]:
    rows = get_registry().get(CONTAINER).all()
    if scenario_id is not None:
        rows = [row for row in rows if row.get("scenario_id") == scenario_id]
    rows.sort(key=lambda row: (str(row.get("created_at", "")), str(row.get("id", ""))), reverse=True)
    return [DeltaScorecard.model_validate(_model_row(row)) for row in rows]


def get_latest_scorecard(*, scenario_id: str | None = None) -> DeltaScorecard | None:
    scorecards = list_scorecards(scenario_id=scenario_id)
    return scorecards[0] if scorecards else None


def readback(scorecard_id: str) -> DeltaScorecard | None:
    return get_scorecard(scorecard_id)


def latest(*, scenario_id: str | None = None) -> DeltaScorecard | None:
    return get_latest_scorecard(scenario_id=scenario_id)
