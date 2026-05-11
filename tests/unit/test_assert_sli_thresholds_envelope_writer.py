"""Cycle 3 / T-AA40 / A3-01 / FR-071 — unit test for the
``staging_promotion.refused`` audit-envelope writer in
``tests/staging_gates.py::assert_sli_thresholds``.

Asserts:

1. The envelope is written via *envelope_sink* BEFORE the
   :class:`StagingPromotionRefused` raise (sink-call-order invariant).
2. All eight ``details`` fields are populated per
   ``contracts/audit-envelope.md`` §3.26 schema:
   ``staging_promotion_correlation_id``, ``build_label``,
   ``triggering_workflow_run_id``, ``triggering_actor``,
   ``breached_slis``, ``sample_floor_underages``, ``refused_at``,
   ``gate_helper_version``.
3. The top-level envelope ``correlation_id`` equals
   ``details.staging_promotion_correlation_id`` (Pass-1 Q4 / Pass-2 Q1
   single-stream JOIN invariant).
4. ``breached_slis`` is lex-sorted (CHK149).
5. ``sample_floor_underages`` carries ``observed_samples`` <
   ``required_samples`` per row (CHK150).
6. ``gate_helper_version`` is a 64-char SHA-256 hex digest of the
   helper file (forensic-replay determinism).
"""

from __future__ import annotations

import re

import pytest

from tests.staging_gates import (
    MIN_SAMPLES_PER_SLI_24H,
    StagingPromotionRefused,
    _build_refused_envelope,
    assert_sli_thresholds,
)

_SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")
_UUID4_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _capturing_sink() -> tuple[list[dict], callable]:
    captured: list[dict] = []

    def sink(envelope):  # type: ignore[no-untyped-def]
        captured.append(dict(envelope))

    return captured, sink


def _z6_breach_results() -> dict:
    return {
        "SLI-Z6": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "per_model": {
                "gpt-4o": {"p95_latency_ms": 5500},  # > 5000 breach
                "gpt-4o-mini": {"p95_latency_ms": 1200},
            },
        },
        "SLI-Z7": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "drift_budget_pct": 99.7,
        },
    }


def _z7_breach_results() -> dict:
    return {
        "SLI-Z6": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "per_model": {"gpt-4o": {"p95_latency_ms": 3500}},
        },
        "SLI-Z7": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "drift_budget_pct": 98.5,
        },
    }


def _z7_starvation_results() -> dict:
    return {
        "SLI-Z6": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "per_model": {"gpt-4o": {"p95_latency_ms": 3500}},
        },
        "SLI-Z7": {
            "sample_count": 5,  # < MIN_SAMPLES_PER_SLI_24H
            "drift_budget_pct": 99.7,
        },
    }


def test_envelope_written_before_raise_z6_breach() -> None:
    """Sink is invoked BEFORE the ``StagingPromotionRefused`` raise."""

    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=_z6_breach_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.1",
        )
    assert len(captured) == 1, f"expected exactly one envelope on refused invocation; got {len(captured)}"


def test_envelope_carries_all_eight_details_fields() -> None:
    """Per §3.26 — eight required ``details`` fields populated."""

    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=_z6_breach_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.1",
        )
    envelope = captured[0]
    assert envelope["entry_type"] == "staging_promotion.refused"
    details = envelope["details"]
    required_keys = {
        "staging_promotion_correlation_id",
        "build_label",
        "triggering_workflow_run_id",
        "triggering_actor",
        "breached_slis",
        "sample_floor_underages",
        "refused_at",
        "gate_helper_version",
    }
    assert set(details.keys()) == required_keys, (
        f"§3.26 details keys mismatch: extras={set(details.keys()) - required_keys}, "
        f"missing={required_keys - set(details.keys())}"
    )
    assert details["build_label"] == "v0.36.3-rc.1"


def test_envelope_correlation_ids_match_top_and_nested() -> None:
    """Pass-1 Q4 — top-level ``correlation_id`` ≡ inner UUID."""

    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=_z6_breach_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.2",
        )
    envelope = captured[0]
    assert envelope["correlation_id"] == envelope["details"]["staging_promotion_correlation_id"], (
        "Pass-1 Q4 invariant — top-level correlation_id MUST equal "
        "details.staging_promotion_correlation_id (single-stream JOIN)"
    )
    assert _UUID4_RE.match(envelope["correlation_id"]), (
        f"correlation_id MUST be a UUID4 lowercase hex string; got {envelope['correlation_id']!r}"
    )


def test_envelope_breached_slis_lex_sorted() -> None:
    """``breached_slis`` is lex-sorted per §3.26 schema."""

    # Synthesise a multi-SLI breach (Z6 + Z7) so sorting is observable.
    res = _z7_breach_results()
    res["SLI-Z6"]["per_model"] = {"gpt-4o": {"p95_latency_ms": 5500}}
    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=res,
            envelope_sink=sink,
        )
    breached = captured[0]["details"]["breached_slis"]
    assert breached == sorted(breached), f"breached_slis MUST be lex-sorted; got {breached!r}"
    assert breached == ["SLI-Z6", "SLI-Z7"], f"both SLIs MUST appear in a single envelope; got {breached!r}"


def test_envelope_sample_floor_underages_carry_observed_lt_required() -> None:
    """``sample_floor_underages`` rows have ``observed < required``."""

    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=_z7_starvation_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.3",
        )
    underages = captured[0]["details"]["sample_floor_underages"]
    assert len(underages) == 1
    row = underages[0]
    assert row["sli_id"] == "SLI-Z7"
    assert row["observed_samples"] < row["required_samples"]
    assert row["required_samples"] == MIN_SAMPLES_PER_SLI_24H


def test_envelope_gate_helper_version_is_sha256_hex() -> None:
    """``gate_helper_version`` is a 64-char SHA-256 hex digest."""

    captured, sink = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=_z6_breach_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.4",
        )
    digest = captured[0]["details"]["gate_helper_version"]
    assert _SHA256_HEX_RE.match(digest), f"gate_helper_version MUST be a 64-char SHA-256 hex digest; got {digest!r}"


def test_no_envelope_on_green_path() -> None:
    """Green dataset → no envelope, no raise."""

    captured, sink = _capturing_sink()
    assert_sli_thresholds(
        sli_results={
            "SLI-Z6": {
                "sample_count": MIN_SAMPLES_PER_SLI_24H,
                "per_model": {"gpt-4o": {"p95_latency_ms": 3500}},
            },
            "SLI-Z7": {
                "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
                "drift_budget_pct": 99.7,
            },
        },
        envelope_sink=sink,
        build_label="v0.36.3-rc.green",
    )
    assert captured == [], "green path MUST NOT emit an envelope"


def test_two_concurrent_invocations_yield_distinct_uuids() -> None:
    """Pass-1 Q3 — two refused invocations → two distinct UUIDs."""

    captured_a, sink_a = _capturing_sink()
    captured_b, sink_b = _capturing_sink()
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(sli_results=_z6_breach_results(), envelope_sink=sink_a, build_label="v1")
    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(sli_results=_z6_breach_results(), envelope_sink=sink_b, build_label="v1")
    uuid_a = captured_a[0]["details"]["staging_promotion_correlation_id"]
    uuid_b = captured_b[0]["details"]["staging_promotion_correlation_id"]
    assert uuid_a != uuid_b, (
        "Pass-1 Q3 no-coalescing — two refused invocations MUST produce "
        f"two distinct correlation_ids; got {uuid_a!r} == {uuid_b!r}"
    )


def test_build_refused_envelope_helper_idempotent_shape() -> None:
    """The pure builder produces consistent shape regardless of inputs."""

    env_a = _build_refused_envelope(
        breached_slis=["SLI-Z6"],
        sample_floor_underages=[],
        build_label="vX",
    )
    env_b = _build_refused_envelope(
        breached_slis=["SLI-Z7", "SLI-Z6"],
        sample_floor_underages=[{"sli_id": "SLI-Z7", "observed_samples": 5, "required_samples": 30}],
        build_label="vY",
    )
    # Shape parity (same keys); content varies.
    assert set(env_a["details"]) == set(env_b["details"])
    # b's breached_slis is lex-sorted by the helper.
    assert env_b["details"]["breached_slis"] == ["SLI-Z6", "SLI-Z7"]
