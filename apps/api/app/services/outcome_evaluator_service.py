"""Outcome evaluator service (cycle-1 amendment, spec 034 — T180).

Deterministic counterfactual evaluator for the FR-028 contract. Covers the
five capstone outcomes (SC-001..SC-005); requests outside that range raise
``EvaluatorError(400)`` per Pass 5 Q29. The service:

  • reads ``metric_inputs`` against ``bootstrap_seed_data().scenarios[scenario_id].baseline``
    (data-model §6) — no DB write, pure read;
  • appends an ``AuditRow`` to a process-local in-memory ledger (the routes
    are dual-guarded by ``AMA_TEST_SUPPORT == "1"`` so this only ever sees
    Playwright traffic — see ``app.middleware.test_support_guard``);
  • is idempotent on the tuple
    ``(sc_id, scenario_id, persona_id, correlation_id)`` — a repeat call
    returns the same ``audit_id`` and verdict (data-model §13 invariant).

The audit-list endpoint (T179) reads from this same ledger.

Contract: ``specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md``.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packages.domain.src.domain.seed.bootstrap import bootstrap_seed_data

# ---------------------------------------------------------------------------
# Process-local state. All mutations go through ``_LOCK`` so concurrent
# evaluations from the test suite see consistent state.
# ---------------------------------------------------------------------------

_LOCK = threading.Lock()
_AUDIT_ROWS: list[dict[str, Any]] = []
_IDEMPOTENCY: dict[tuple[str, str, str, str], dict[str, Any]] = {}
_PERSONA_INDEX: dict[str, dict[str, Any]] | None = None

# Routable range (Q29). sc-006..sc-011 are owned by CI artefacts, NOT this
# evaluator — see ``CI_OWNER_BY_SC`` for the owner table the 400 response
# names so the suite can route the user to the right job.
ROUTABLE_SC_IDS: frozenset[str] = frozenset({"sc-001", "sc-002", "sc-003", "sc-004", "sc-005"})

CI_OWNER_BY_SC: dict[str, str] = {
    "sc-006": "web-coverage-gate",
    "sc-007": "web-coverage-gate",
    "sc-008": "web-coverage-gate",
    "sc-009": "gap-register-validate",
    "sc-010": "verify-trace-determinism",
    "sc-011": "web-coverage-shard",
}

# Per-sc_id ``metric_inputs`` field (the only required key in the embedded
# request schema). Centralised so the FastAPI route can produce a stable 422
# message and the unit tests can drive the table.
METRIC_FIELD: dict[str, str] = {
    "sc-001": "lives_at_risk",
    "sc-002": "signal_to_action_ms",
    "sc-003": "evac_lead_hours",
    "sc-004": "logistics_clicks",
    "sc-005": "economic_loss_aud",
}


# ---------------------------------------------------------------------------
# Errors. Routes translate these to HTTPException; service callers can also
# catch them directly (e.g. unit tests).
# ---------------------------------------------------------------------------


class EvaluatorError(Exception):
    """Service-layer error carrying both an HTTP status and a JSON envelope.

    The route layer maps ``status_code`` + ``payload`` straight to
    FastAPI's response model. Suite-side error handling matches on
    ``payload["error"]``.
    """

    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("error", "evaluator_error"))
        self.status_code = status_code
        self.payload = payload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_root() -> Path:
    """Match the layout used by ``app.api.routes.test_support``."""

    return Path(__file__).resolve().parents[4] / "packages" / "domain" / "src" / "domain" / "seed"


def _now_iso() -> str:
    """ISO-8601 UTC timestamp ending in 'Z' to match the contract."""

    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _persona_index() -> dict[str, dict[str, Any]]:
    """Cached persona-id → identity record map (ASM-011 enforcement)."""

    global _PERSONA_INDEX
    if _PERSONA_INDEX is None:
        seed = bootstrap_seed_data(_seed_root())
        identities = seed.get("identities") or []
        if not isinstance(identities, list):  # pragma: no cover - defensive
            return {}
        _PERSONA_INDEX = {
            ident["persona_id"]: ident
            for ident in identities
            if isinstance(ident, dict) and "persona_id" in ident
        }
    return _PERSONA_INDEX


def _evaluate_metric(
    sc_id: str,
    baseline: dict[str, Any],
    metric_inputs: dict[str, Any],
) -> tuple[str, float | None, float | None]:
    """Compute the (status, metric_value, threshold) triple for the sc_id.

    Status is one of ``pass | fail | gap``; ``gap`` is reserved for cases
    where the baseline lacks the field needed to score (rare — would mean
    the seed JSON is missing a key — and triggers a GAP in the suite).
    """

    if sc_id == "sc-001":
        baseline_lives = float(baseline.get("lives_at_risk", 0))
        observed = float(metric_inputs.get("lives_at_risk", 0))
        lives_saved = baseline_lives - observed
        threshold = 1000.0
        return ("pass" if lives_saved >= threshold else "fail", lives_saved, threshold)

    if sc_id == "sc-002":
        baseline_ms = float(baseline.get("signal_to_action_ms", 0))
        observed = float(metric_inputs.get("signal_to_action_ms", 0))
        if baseline_ms == 0:
            return ("gap", None, None)
        ratio = observed / baseline_ms
        threshold = 0.5  # 50% faster
        return ("pass" if ratio <= threshold else "fail", ratio, threshold)

    if sc_id == "sc-003":
        observed = float(metric_inputs.get("evac_lead_hours", 0))
        threshold = 24.0
        return ("pass" if observed >= threshold else "fail", observed, threshold)

    if sc_id == "sc-004":
        observed = float(metric_inputs.get("logistics_clicks", 0))
        # Per spec.md SC-004 + depth-profile: ≤ 7 clicks for L1 capstone.
        # The L2 mutual-aid threshold (≤ 12) is asserted on a separate
        # workflow path; the routable evaluator only scores L1.
        threshold = 7.0
        return ("pass" if observed <= threshold else "fail", observed, threshold)

    if sc_id == "sc-005":
        baseline_aud = float(baseline.get("economic_loss_aud", 0))
        observed = float(metric_inputs.get("economic_loss_aud", 0))
        if baseline_aud == 0:
            return ("gap", None, None)
        reduction = (baseline_aud - observed) / baseline_aud
        threshold = 0.30
        return ("pass" if reduction >= threshold else "fail", reduction, threshold)

    return ("gap", None, None)  # pragma: no cover - guarded upstream


# ---------------------------------------------------------------------------
# Public service API
# ---------------------------------------------------------------------------


def evaluate(
    sc_id: str,
    scenario_id: str,
    persona_id: str,
    correlation_id: str,
    metric_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Run the FR-028 deterministic counterfactual evaluation.

    Raises ``EvaluatorError`` on any contract violation:

      • 400 ``evaluator_not_routable`` — sc_id ∉ sc-001..sc-005 (Q29)
      • 404 ``scenario_not_found`` — scenario_id missing in seed
      • 422 ``persona_not_resolvable`` — persona_id not in identities (ASM-011)
      • 422 ``metric_inputs_invalid`` — wrong field for sc_id

    Returns a dict matching ``EvaluatorResponse`` (data-model §13).
    """

    if sc_id not in ROUTABLE_SC_IDS:
        raise EvaluatorError(
            400,
            {
                "error": "evaluator_not_routable",
                "sc_id": sc_id,
                "ci_job": CI_OWNER_BY_SC.get(sc_id, "unknown"),
                "suggested_action": (
                    "see SC-XXX ownership in spec.md FR-028 / Pass 5 Q29 — "
                    "derived from CI artefacts (web-coverage-gate, gap-register, "
                    "verify-trace-determinism), not from a workflow-state "
                    "evaluator endpoint"
                ),
            },
        )

    seed = bootstrap_seed_data(_seed_root())
    scenarios = seed.get("scenarios") or {}
    if not isinstance(scenarios, dict) or scenario_id not in scenarios:
        raise EvaluatorError(
            404,
            {
                "error": "scenario_not_found",
                "scenario_id": scenario_id,
                "suggested_action": (
                    "register in bootstrap_seed_data() or update depth profile"
                ),
            },
        )

    if persona_id not in _persona_index():
        raise EvaluatorError(
            422,
            {
                "error": "persona_not_resolvable",
                "persona_id": persona_id,
                "suggested_action": (
                    "ASM-011: persona must resolve in bootstrap_seed_data().identities"
                ),
            },
        )

    required_field = METRIC_FIELD[sc_id]
    if required_field not in metric_inputs:
        raise EvaluatorError(
            422,
            {
                "error": "metric_inputs_invalid",
                "sc_id": sc_id,
                "required_field": required_field,
                "suggested_action": (
                    f"metric_inputs.{required_field} is required for {sc_id}"
                ),
            },
        )

    key = (sc_id, scenario_id, persona_id, correlation_id)
    with _LOCK:
        if key in _IDEMPOTENCY:
            return _IDEMPOTENCY[key]

        scenario = scenarios[scenario_id]
        baseline = (
            scenario.get("baseline", {})
            if isinstance(scenario, dict)
            else {}
        )
        status_, metric_value, threshold = _evaluate_metric(
            sc_id, baseline, metric_inputs,
        )

        audit_id = str(uuid.uuid4())
        audit_timestamp = _now_iso()
        row = {
            "audit_id": audit_id,
            "audit_timestamp": audit_timestamp,
            "correlation_id": correlation_id,
            "operator_identity": {"persona_id": persona_id},
            "rationale": (
                f"Counterfactual evaluation for {sc_id} on scenario "
                f"{scenario_id}: status={status_}"
            ),
            "confidence": 0.95 if status_ == "pass" else 0.85,
            "source_refs": [
                f"scenario:{scenario_id}",
                f"baseline:{json.dumps(baseline, sort_keys=True)}",
            ],
            "outcome": status_,
            "audit_type": f"outcome.evaluator.{sc_id}",
        }
        _AUDIT_ROWS.append(row)
        response = {
            "status": status_,
            "evidence_refs": [
                f"audit:{audit_id}",
                f"scenario:{scenario_id}",
            ],
            "metric_value": metric_value,
            "threshold": threshold,
            "audit_id": audit_id,
        }
        _IDEMPOTENCY[key] = response
        return response


def list_audit(
    correlation_id: str | None = None,
    cycle: str = "current",
    limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """FR-029 audit-list with cycle filter + cursor pagination.

    The ``cycle=current`` filter compares ``audit_timestamp`` to
    ``bootstrap_seed_data().current_cycle_start`` (Q22). ``cycle=all`` is
    opt-in and reserved for FR-005 cross-cycle reads + FR-027 regression.
    """

    if cycle not in ("current", "all"):
        raise EvaluatorError(
            400,
            {
                "error": "invalid_cycle",
                "cycle": cycle,
                "allowed": ["current", "all"],
            },
        )
    if limit < 1 or limit > 500:
        raise EvaluatorError(
            400,
            {
                "error": "invalid_limit",
                "limit": limit,
                "max": 500,
            },
        )

    seed = bootstrap_seed_data(_seed_root())
    cycle_start_iso = seed.get("current_cycle_start", "1970-01-01T00:00:00+00:00")
    if isinstance(cycle_start_iso, str):
        cycle_start = datetime.fromisoformat(cycle_start_iso)
    else:  # pragma: no cover - defensive guard
        cycle_start = datetime.fromtimestamp(0, tz=UTC)

    with _LOCK:
        rows = list(_AUDIT_ROWS)

    if correlation_id is not None:
        rows = [r for r in rows if r.get("correlation_id") == correlation_id]
    if cycle == "current":
        def _ts(r: dict[str, Any]) -> datetime:
            ts = r.get("audit_timestamp", "")
            return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.fromtimestamp(0, tz=UTC)

        rows = [r for r in rows if _ts(r) >= cycle_start]
    rows.sort(key=lambda r: r.get("audit_timestamp", ""))

    start = int(cursor) if cursor and cursor.isdigit() else 0
    end = start + limit
    page = rows[start:end]
    next_cursor = str(end) if end < len(rows) else None
    return {
        "count": len(rows),
        "items": page,
        "next_cursor": next_cursor,
        "cycle": cycle,
    }


def reset_for_tests() -> None:
    """Test-only: clear in-memory state (audit rows + idempotency cache).

    Pytest fixtures invoke this between cases so the contract tests start
    from a clean ledger. Production code MUST NOT call this — the dual
    guard ensures the routes are unreachable outside dev/test anyway.
    """

    global _PERSONA_INDEX
    with _LOCK:
        _AUDIT_ROWS.clear()
        _IDEMPOTENCY.clear()
    _PERSONA_INDEX = None
