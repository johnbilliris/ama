"""Shared gating helpers for spec-036 staging-only test markers.

Each helper returns ``True`` when the matching environment variable is set to
``"1"`` (or ``"true"``/``"yes"`` case-insensitively). Tests that genuinely
require a live Azure resource decorate themselves with ``pytest.mark.<X>`` AND
``pytest.mark.skipif(not <gate_fn>())`` so the body is reviewable but skipped
unless the operator opts in.

Per repo memory and `pyproject.toml` ``[tool.pytest.ini_options].markers``
the recognised gates are:

* ``AMA_STAGING_AZURE``         → APIM + Redis live telemetry
* ``AMA_STAGING_FOUNDRY``       → Azure OpenAI / Azure AI Inference
* ``AMA_STAGING_COSMOS``        → Cosmos DB w/ ETag optimistic concurrency
* ``AMA_STAGING_SPEECH``        → Azure AI Speech Services TTS
* ``AMA_STAGING_BLOB_WORM``     → Blob storage with immutability_policy
* ``AMA_STAGING_MEASUREMENT``   → 30-pair measurement harness execution

The ``ALL_GATES`` map is consumed by ``tests/devops/test_staging_gates_registered.py``
to ensure the documentation here stays in sync with the markers list.

Cycle 2 / T-AA17 — :data:`MIN_SAMPLES_PER_SLI_24H` codifies the 30-sample
CLT floor for the Z6 + Z7 trailing-24-hour SLIs (pass-2 Q4). The matching
:func:`assert_sli_thresholds` helper refuses staging promotion when EITHER
sample-size starvation OR a threshold breach is observed.

Cycle 3 / T-AA40 — :func:`assert_sli_thresholds` writes a typed
``staging_promotion.refused`` audit envelope (entry-26 per
``contracts/audit-envelope.md`` §3.26 / FR-071) BEFORE raising
:class:`StagingPromotionRefused`, so the gate decision is auditable per
Pass-1 Q3 + Pass-2 Q1 (gap-free, append-only, typed audit trail).
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger(__name__)

_TRUTHY = {"1", "true", "yes", "on", "y"}

#: Path to the SLI registry consumed by :func:`assert_sli_thresholds`. Cycle 3
#: / T-AA34 / HIGH-1 mitigation — reading ``breach_pct`` from the JSON
#: registry (single source of truth) avoids the "JSON-only threshold change"
#: drift class identified in the Cycle 3 analyze pass (Step 8aa). Mirrors
#: the established ``_SLI_PATH`` pattern at
#: ``tests/contract/test_sli_kql_schema_v2.py:25``.
_SLI_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent
    / "infra"
    / "observability"
    / "sli-kql.json"
)


@functools.lru_cache(maxsize=1)
def _sli_doc() -> Mapping[str, Any]:
    """Return the parsed ``infra/observability/sli-kql.json`` document.

    Cached so repeated gate invocations do not re-read the file. Reload via
    ``_sli_doc.cache_clear()`` in tests that mutate the fixture (none do
    today, but keep the cache busting affordance for future fixtures).
    """

    return json.loads(_SLI_PATH.read_text(encoding="utf-8"))


def _sli_entry(sli_id: str) -> Mapping[str, Any]:
    """Return the JSON entry for *sli_id* (raises :class:`KeyError` if missing)."""

    for entry in _sli_doc()["slis"]:
        if entry["id"] == sli_id:
            return entry
    raise KeyError(f"{sli_id} not found in {_SLI_PATH!s}")

#: Cycle 2 / T-AA17 / pass-2 Q4 — minimum sample count per SLI evaluated
#: over a 24 h trailing window. Below this the staging-promotion gate
#: refuses to evaluate the SLI (Central-Limit-Theorem floor; raise to
#: ``100`` if the false-positive rate exceeds 5 %). The synthetic
#: smoke-injection job in ``.github/workflows/staging-promotion.yml``
#: (T-AA19) maintains a 33 % safety margin (≥ 40 events / 24 h).
MIN_SAMPLES_PER_SLI_24H: Final[int] = 30


def _is_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in _TRUTHY


def azure_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_AZURE")


def foundry_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_FOUNDRY")


def cosmos_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_COSMOS")


def speech_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_SPEECH")


def blob_worm_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_BLOB_WORM")


def measurement_staging_enabled() -> bool:
    return _is_truthy("AMA_STAGING_MEASUREMENT")


ALL_GATES = {
    "azure_staging": azure_staging_enabled,
    "azure_foundry_staging": foundry_staging_enabled,
    "azure_cosmos_staging": cosmos_staging_enabled,
    "azure_speech_staging": speech_staging_enabled,
    "azure_blob_worm_staging": blob_worm_staging_enabled,
    "measurement_staging": measurement_staging_enabled,
}


# ---------------------------------------------------------------------------
# Cycle 2 / T-AA17 — SLI threshold-gate helper
# ---------------------------------------------------------------------------


class StagingPromotionRefused(AssertionError):
    """Raised when a staging-promotion gate refuses promotion.

    Raised by :func:`assert_sli_thresholds` on EITHER of:

    * sample-size starvation (``sample_count < MIN_SAMPLES_PER_SLI_24H``);
    * threshold breach (per ``contracts/sli-thresholds.md`` §1).

    Cycle 3 / T-AA40 — the helper writes a typed
    ``staging_promotion.refused`` audit envelope (entry-26) BEFORE raising,
    so the gate decision is auditable per Pass-1 Q3 + Pass-2 Q1. The
    refusal is structured: every breached SLI and every sample-floor
    underage observed across BOTH Z6 and Z7 is collected into a single
    envelope so a single-call refusal yields exactly one envelope (no
    coalescing across calls).
    """


#: Default audit-envelope sink. Tests may inject a different sink via the
#: ``envelope_sink`` keyword argument; production CI runs use
#: :func:`_default_envelope_sink` which logs the structured details and
#: appends to the path at ``STAGING_PROMOTION_AUDIT_PATH`` (when set) so
#: the workflow YAML can collect the envelope as a build artefact.
EnvelopeSink = Callable[[Mapping[str, Any]], None]


def _default_envelope_sink(envelope: Mapping[str, Any]) -> None:
    """Default sink — log + (optionally) append-to-file.

    The CI workflow at ``.github/workflows/staging-promotion.yml`` (T-AA35)
    sets ``STAGING_PROMOTION_AUDIT_PATH`` to a job-temp path so the file is
    uploaded as a build artefact; if unset, the envelope is logged only.
    """

    logger.warning(
        "staging_promotion.refused envelope correlation_id=%s "
        "build_label=%s breached_slis=%r sample_floor_underages=%r",
        envelope.get("correlation_id"),
        envelope.get("details", {}).get("build_label"),
        envelope.get("details", {}).get("breached_slis"),
        envelope.get("details", {}).get("sample_floor_underages"),
    )
    audit_path = os.environ.get("STAGING_PROMOTION_AUDIT_PATH")
    if audit_path:
        # Append-only, JSONL — preserves Cycle 1 ADR-036-007 gap-free
        # invariant when this sink is co-located with the Cosmos writer
        # (the file is a complementary forensic artefact, not a
        # replacement for the typed audit container).
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(envelope, sort_keys=True, default=str) + "\n")


def _build_refused_envelope(
    *,
    breached_slis: list[str],
    sample_floor_underages: list[Mapping[str, Any]],
    build_label: str | None = None,
) -> dict[str, Any]:
    """Build a ``staging_promotion.refused`` envelope per §3.26.

    The envelope's top-level ``correlation_id`` MUST equal
    ``details.staging_promotion_correlation_id`` (single-stream JOIN
    invariant per Pass-1 Q4 / Pass-2 Q1).
    """

    correlation_id = str(uuid.uuid4())
    resolved_build_label = (
        build_label
        if build_label is not None
        else os.environ.get("BUILD_LABEL", "unknown-build-label")
    )
    triggering_run_id = int(os.environ.get("GITHUB_RUN_ID", "1"))
    triggering_actor = os.environ.get("GITHUB_ACTOR", "unknown")
    gate_helper_version = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()

    details: dict[str, Any] = {
        "staging_promotion_correlation_id": correlation_id,
        "build_label": resolved_build_label,
        "triggering_workflow_run_id": triggering_run_id,
        "triggering_actor": triggering_actor,
        "breached_slis": sorted(breached_slis),
        "sample_floor_underages": list(sample_floor_underages),
        "refused_at": datetime.now(UTC).isoformat(),
        "gate_helper_version": gate_helper_version,
    }
    return {
        "entry_type": "staging_promotion.refused",
        "correlation_id": correlation_id,
        "details": details,
    }


def assert_sli_thresholds(
    *,
    sli_results: Mapping[str, Mapping[str, Any]],
    envelope_sink: EnvelopeSink | None = None,
    build_label: str | None = None,
) -> None:
    """Assert per-SLI 24 h trailing-window invariants for Z6 + Z7.

    Each value in ``sli_results`` is a mapping with at least:

    * ``sample_count`` — :class:`int` count of observations in window
    * for ``Z6``: ``p95_latency_ms`` (per ``model_deployment``)
    * for ``Z7``: ``drift_budget_pct``

    Cycle 3 / T-AA40 — every detected breach OR sample-floor underage
    is COLLECTED rather than triggering an immediate raise, so a single
    refused invocation produces exactly one
    ``staging_promotion.refused`` audit envelope (entry-26) with the
    aggregated breach list. The envelope is written via
    *envelope_sink* (default: :func:`_default_envelope_sink`) BEFORE
    :class:`StagingPromotionRefused` is raised; the failure mode is
    fail-closed (the raise propagates a non-zero workflow exit per
    FR-071).

    Two concurrent refused invocations produce two envelopes with
    distinct ``staging_promotion_correlation_id`` UUIDs (Pass-1 Q3
    no-coalescing invariant — exercised by
    :mod:`tests.integration.test_staging_promotion_concurrency`).

    Honours pass-2 Q4 (CLT 30-sample floor) + sli-thresholds.md
    rows 6 + 7 + Cycle 3 §3.26 envelope contract.
    """

    sink = envelope_sink if envelope_sink is not None else _default_envelope_sink

    # Cycle 3 / T-AA40 — accumulate breaches and underages across BOTH
    # Z6 and Z7 before deciding whether to raise. ``first_failure_message``
    # captures the message for the eventual raise; the exception is held
    # back until the audit envelope is written (Pass-1 Q3 ordering).
    breached_slis: list[str] = []
    sample_floor_underages: list[dict[str, Any]] = []
    failure_messages: list[str] = []

    for sli_id in ("SLI-Z6", "SLI-Z7"):
        result = sli_results.get(sli_id)
        if result is None:
            failure_messages.append(
                f"{sli_id} missing from sli_results — "
                "Cycle 2 staging-promotion gate requires Z6 + Z7."
            )
            breached_slis.append(sli_id)
            continue
        sample_count = int(result.get("sample_count", 0))
        if sample_count < MIN_SAMPLES_PER_SLI_24H:
            failure_messages.append(
                f"{sli_id} sample-size starvation: {sample_count} < "
                f"{MIN_SAMPLES_PER_SLI_24H} (CLT floor; pass-2 Q4). "
                "Run synthetic smoke-injection (T-AA19) before retrying."
            )
            sample_floor_underages.append(
                {
                    "sli_id": sli_id,
                    "observed_samples": sample_count,
                    "required_samples": MIN_SAMPLES_PER_SLI_24H,
                }
            )
            # Sample-floor underage short-circuits per-SLI evaluation —
            # threshold comparison on a starved sample is invalid.
            continue
        if sli_id == "SLI-Z6":
            # Per-model thresholds; expect either a flat dict or a
            # ``per_model`` sub-dict keyed by deployment name.
            per_model = result.get("per_model") or {
                result.get("model_deployment", "default"): {
                    "p95_latency_ms": result.get("p95_latency_ms"),
                }
            }
            for deployment, metrics in per_model.items():
                p95 = metrics.get("p95_latency_ms")
                if p95 is None:
                    failure_messages.append(
                        f"SLI-Z6 missing p95_latency_ms for {deployment}"
                    )
                    if "SLI-Z6" not in breached_slis:
                        breached_slis.append("SLI-Z6")
                    continue
                breach = (
                    5000 if "gpt-4o" in deployment and "mini" not in deployment else 2000
                )
                if p95 > breach:
                    failure_messages.append(
                        f"SLI-Z6 BREACH ({deployment}): p95={p95} ms > "
                        f"{breach} ms (sli-thresholds.md row 6)."
                    )
                    if "SLI-Z6" not in breached_slis:
                        breached_slis.append("SLI-Z6")
        elif sli_id == "SLI-Z7":
            drift_pct = result.get("drift_budget_pct")
            if drift_pct is None:
                failure_messages.append("SLI-Z7 missing drift_budget_pct")
                breached_slis.append("SLI-Z7")
                continue
            # Cycle 3 / T-AA34 / A3-06 / HIGH-1 — read ``breach_pct``
            # from the SLI registry JSON instead of hard-coding ``99.5``.
            # This eliminates the JSON-only-threshold-change drift class
            # identified in the Cycle 3 analyze pass (Step 8aa). The
            # Cycle 3 amendment pinned the breach band at 99.0 % (warn
            # band remains 99.5 %) — see contracts/sli-thresholds.md
            # §6b L271-274 and infra/observability/sli-kql.json `SLI-Z7`.
            z7_breach_pct = float(_sli_entry("SLI-Z7")["breach_pct"])
            if drift_pct < z7_breach_pct:
                failure_messages.append(
                    f"SLI-Z7 BREACH: drift_budget_pct={drift_pct} < "
                    f"{z7_breach_pct} (sli-thresholds.md row 7)."
                )
                breached_slis.append("SLI-Z7")

    if not breached_slis and not sample_floor_underages:
        # Green path — no envelope, no raise.
        return

    # Build the typed envelope and write it BEFORE raising. The envelope
    # writer must NOT swallow the failure; if the sink raises, the gate
    # fails closed (the unhandled sink exception propagates as the
    # workflow's failure cause — preferable to a silent-success).
    envelope = _build_refused_envelope(
        breached_slis=breached_slis,
        sample_floor_underages=sample_floor_underages,
        build_label=build_label,
    )
    sink(envelope)

    # Raise with the first collected failure message (back-compat with
    # Cycle 2 callers that pattern-match on ``StagingPromotionRefused``
    # message text); the full breach + underage set is carried in the
    # audit envelope for forensic reconstruction.
    raise StagingPromotionRefused(
        failure_messages[0]
        if failure_messages
        else "staging promotion refused"
    )


__all__ = [
    "ALL_GATES",
    "EnvelopeSink",
    "MIN_SAMPLES_PER_SLI_24H",
    "StagingPromotionRefused",
    "assert_sli_thresholds",
    "azure_staging_enabled",
    "blob_worm_staging_enabled",
    "cosmos_staging_enabled",
    "foundry_staging_enabled",
    "measurement_staging_enabled",
    "speech_staging_enabled",
]
