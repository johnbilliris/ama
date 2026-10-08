"""Spec-036 Wave 4 — T-Z02 staging-promotion blocking E2E gate.

Verifies the 5 ADR-036-008 SLIs are within threshold on the synthetic
30-minute staging scenario before promotion to production. Per Q5 /
FR-063 any breach blocks promotion.

This is a CONTRACT test — it loads the canonical KQL templates from
``infra/observability/sli-kql.json`` and asserts:

* the JSON file is well-formed and contains exactly 5 SLIs;
* every SLI has the canonical fields (id, name, window, kql, fr_refs);
* every SLI maps to one of the 5 ADR-036-008 categories;
* the 5 alert rules have matching ids in the Bicep module
  ``infra/bicep/modules/simulation-app-insights-alerts.bicep`` so
  what-if drift between KQL and alert rules is caught at CI time.

The release-gate procedure relies on this test as the static gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import uuid
from pathlib import Path

import pytest

# Cycle 3 / T-AA42 — staging_gates symbols for synthetic-canary tests
# (appended block below). Import here to keep imports consolidated at top-of-file.
from tests.staging_gates import (  # noqa: E402
    StagingPromotionRefused,
    assert_sli_thresholds,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SLI_JSON = REPO_ROOT / "infra" / "observability" / "sli-kql.json"
ALERTS_BICEP = REPO_ROOT / "infra" / "bicep" / "modules" / "simulation-app-insights-alerts.bicep"

CANONICAL_IDS = [
    "SLI-Z1",
    "SLI-Z2",
    "SLI-Z3",
    "SLI-Z4",
    "SLI-Z5",
    "SLI-Z6",  # Cycle 2 / T-AA16 / A2-02 — sub-agent reply latency (24 h)
    "SLI-Z7",  # Cycle 2 / T-AA16 / A2-02 — map-overlay drift error budget
]


@pytest.fixture(scope="module")
def sli_doc() -> dict:
    return json.loads(SLI_JSON.read_text(encoding="utf-8"))


def test_sli_json_exists() -> None:
    assert SLI_JSON.is_file(), f"missing {SLI_JSON}"


def test_sli_count_is_five(sli_doc: dict) -> None:
    assert len(sli_doc["slis"]) == 7, (
        "Cycle 2 / T-AA16 — exactly 7 SLIs (Z1..Z5 from ADR-036-008 + Z6/Z7 for staging promotion gates per A2-02)"
    )


@pytest.mark.parametrize("expected_id", CANONICAL_IDS)
def test_canonical_sli_id_present(sli_doc: dict, expected_id: str) -> None:
    ids = [s["id"] for s in sli_doc["slis"]]
    assert expected_id in ids, f"missing canonical SLI {expected_id}; got {ids}"


def test_each_sli_has_required_fields(sli_doc: dict) -> None:
    required = {"id", "name", "window", "kql", "fr_refs"}
    for s in sli_doc["slis"]:
        missing = required - set(s.keys())
        assert not missing, f"SLI {s.get('id', '?')} missing fields {missing}"


def test_kql_strings_reference_canonical_event_names(sli_doc: dict) -> None:
    """KQL templates must reference one of the canonical custom-event names."""
    canonical_events = (
        "inject_telemetry.fan_out_complete",
        "audit.sequence.uncertainty",
        "cascade.degraded_to_annotation",
        "cascade.fan_out_complete",
        "sub_agent.invocation.complete",  # Cycle 2 / T-AA16 — Z6 source event
        "sse.map_overlay.delivered",  # Cycle 2 / T-AA16 — Z7 source event
        "AuditEntries_CL",
        "AzureDiagnostics",
    )
    for s in sli_doc["slis"]:
        kql = s["kql"]
        assert any(name in kql for name in canonical_events), (
            f"SLI {s['id']} KQL does not reference a canonical event/source"
        )


def test_alerts_bicep_references_each_sli() -> None:
    """The Bicep module must declare a scheduledQueryRule per SLI."""
    assert ALERTS_BICEP.is_file(), f"missing {ALERTS_BICEP}"
    text = ALERTS_BICEP.read_text(encoding="utf-8")
    expected_resources = (
        "sliZ1Latency",
        "sliZ2GapFree",
        "sliZ3DlqDepth",
        "sliZ4RuHeadroom",
        "sliZ5DegradedRate",
    )
    for name in expected_resources:
        assert name in text, f"Bicep module missing resource {name}"


def test_thresholds_are_strict_for_life_safety_slis(sli_doc: dict) -> None:
    """SLI-Z2 (gap-free) MUST breach on ANY gap (zero-tolerance per FR-048)."""
    z2 = next(s for s in sli_doc["slis"] if s["id"] == "SLI-Z2")
    # Per ADR-036-008: 99.99% target, breach on any gap.
    assert z2["target_pct"] == pytest.approx(99.99)


def test_promotion_gate_blocks_on_any_sli_breach(sli_doc: dict) -> None:
    """Synthetic check — a single fabricated breach blocks promotion."""

    def _is_breach(sli: dict, sample_value: float) -> bool:
        # Cycle 2 / Z6 — model-specific thresholds; treat the gpt-4o
        # breach value (5000 ms) as the worst-case threshold.
        if "breach_threshold_ms_gpt4o" in sli:
            return sample_value > sli["breach_threshold_ms_gpt4o"]
        # Cycle 2 / Z7 — drift_budget_pct breach is "< 99.5"; check
        # before generic breach_threshold_ms so Z7 (which carries both
        # breach_pct AND breach_threshold_ms) is classified by drift pct.
        if sli.get("id") == "SLI-Z7":
            return sample_value < sli["breach_pct"]
        if "breach_threshold_ms" in sli:
            return sample_value > sli["breach_threshold_ms"]
        if "breach_pct_below" in sli:
            return sample_value < sli["breach_pct_below"]
        if "breach_pct" in sli:
            return sample_value > sli["breach_pct"]
        if "breach_threshold_count" in sli:
            return sample_value >= sli["breach_threshold_count"]
        return False

    fabricated_breaches = {
        "SLI-Z1": 2500,  # ms — over 2000 ms breach
        "SLI-Z2": 99.0,  # pct — under 99.99 target
        "SLI-Z3": 3,  # count — over zero
        "SLI-Z4": 95.0,  # pct — over 90 % breach
        "SLI-Z5": 12.0,  # pct — over 10 % breach
        "SLI-Z6": 5500,  # ms — over 5000 ms gpt-4o breach (Cycle 2 / T-AA16)
        "SLI-Z7": 95.0,  # pct — under 99.5 % drift budget (Cycle 2 / T-AA16)
    }
    for s in sli_doc["slis"]:
        sample = fabricated_breaches[s["id"]]
        assert _is_breach(s, sample), (
            f"SLI {s['id']} did not detect breach for fabricated value {sample}; check sli-kql.json thresholds"
        )


# ────────────────────────────────────────────────────────────────────────────
# Cycle 3 / T-AA42 — synthetic-canary refused-on-red SLI tests.
#
# These tests append to the existing T-Z02 contract suite and verify the
# four-invariant rubric for refused promotions per Pass-1 Q3 / FR-071:
#
#   (i)   ``assert_sli_thresholds()`` raises ``StagingPromotionRefused``
#   (ii)  Subprocess invocation exits non-zero
#   (iii) No ``promote/{build_label}`` git tag exists in the local repo
#   (iv)  Envelope written exactly once with expected breached_slis content
#
# The four red shapes exercised cover both threshold-breach paths and
# both sample-floor-underage paths for Z6 and Z7.
# Imports for this block are consolidated at the top of the file.
# ────────────────────────────────────────────────────────────────────────────

_RED_SHAPES = {
    "z6_p95_breach": {
        "expected_breached_slis": ["SLI-Z6"],
        "results": {
            "SLI-Z6": {
                "sample_count": 50,
                "per_model": {"gpt-4o": {"p95_latency_ms": 5500}},
            },
            "SLI-Z7": {
                "sample_count": 50,
                "drift_budget_pct": 99.7,
            },
        },
    },
    "z7_drift_breach": {
        "expected_breached_slis": ["SLI-Z7"],
        "results": {
            "SLI-Z6": {
                "sample_count": 50,
                "per_model": {"gpt-4o": {"p95_latency_ms": 1200}},
            },
            "SLI-Z7": {
                "sample_count": 50,
                "drift_budget_pct": 98.5,
            },
        },
    },
    "z6_sample_floor_underage": {
        "expected_breached_slis": [],  # underage flag carries the failure
        "expected_underages": ["SLI-Z6"],
        "results": {
            "SLI-Z6": {
                "sample_count": 17,  # < MIN_SAMPLES_PER_SLI_24H (24)
                "per_model": {"gpt-4o": {"p95_latency_ms": 1200}},
            },
            "SLI-Z7": {
                "sample_count": 50,
                "drift_budget_pct": 99.7,
            },
        },
    },
    "z7_sample_floor_underage": {
        "expected_breached_slis": [],
        "expected_underages": ["SLI-Z7"],
        "results": {
            "SLI-Z6": {
                "sample_count": 50,
                "per_model": {"gpt-4o": {"p95_latency_ms": 1200}},
            },
            "SLI-Z7": {
                "sample_count": 5,
                "drift_budget_pct": 99.7,
            },
        },
    },
}


def subprocess_script() -> str:
    """Subprocess wrapper that loads ``staging_gates`` via importlib."""

    return textwrap.dedent(
        """
        import importlib.util
        import json
        import pathlib
        import sys

        repo_root = pathlib.Path.cwd()
        gates_path = repo_root / "tests" / "staging_gates.py"
        spec = importlib.util.spec_from_file_location("staging_gates", gates_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["staging_gates"] = module
        spec.loader.exec_module(module)

        results = json.loads(sys.argv[1])
        captured = []

        def sink(env):
            captured.append(env)

        try:
            module.assert_sli_thresholds(
                sli_results=results,
                envelope_sink=sink,
                build_label=sys.argv[2],
            )
            sys.stdout.write(json.dumps({"refused": False, "envelopes": []}))
            sys.exit(0)
        except module.StagingPromotionRefused:
            sys.stdout.write(
                json.dumps({"refused": True, "envelopes": captured},
                           sort_keys=True, default=str)
            )
            sys.exit(1)
        """
    ).strip()


@pytest.mark.parametrize("shape_name", list(_RED_SHAPES.keys()))
def test_synthetic_canary_refused_red_sli_row(shape_name: str) -> None:
    """T-AA42 — four-invariant rubric per red shape."""

    shape = _RED_SHAPES[shape_name]
    # Use a unique build_label per shape to make the (iii) git-tag
    # assertion robust against any pre-existing tag noise.
    build_label = f"v0.36.3-rc.canary-{shape_name}-{uuid.uuid4().hex[:8]}"

    # ── invariant (i) — in-process raises StagingPromotionRefused ──────────
    captured: list[dict] = []

    def sink(envelope) -> None:
        captured.append(dict(envelope))

    with pytest.raises(StagingPromotionRefused):
        assert_sli_thresholds(
            sli_results=shape["results"],
            envelope_sink=sink,
            build_label=build_label,
        )

    # ── invariant (iv) — exactly one envelope, with expected content ──────
    assert len(captured) == 1, f"shape {shape_name!r} — expected exactly one envelope; got {len(captured)}"
    envelope = captured[0]
    details = envelope["details"]
    assert details["build_label"] == build_label
    assert sorted(details["breached_slis"]) == sorted(shape["expected_breached_slis"])
    if "expected_underages" in shape:
        underage_ids = sorted(row["sli_id"] for row in details["sample_floor_underages"])
        assert underage_ids == sorted(shape["expected_underages"]), (
            f"shape {shape_name!r} — expected underages {shape['expected_underages']}; got {underage_ids}"
        )

    # ── invariant (ii) — subprocess invocation exits non-zero ─────────────
    repo_root = str(REPO_ROOT)
    proc = subprocess.run(  # noqa: S603 — controlled stdin script
        [
            sys.executable,
            "-c",
            subprocess_script(),
            json.dumps(shape["results"]),
            build_label,
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        cwd=repo_root,
    )
    assert proc.returncode != 0, (
        f"shape {shape_name!r} — subprocess expected non-zero exit; "
        f"got {proc.returncode}; stdout={proc.stdout!r}; stderr={proc.stderr!r}"
    )
    payload = json.loads(proc.stdout)
    assert payload["refused"] is True
    assert len(payload["envelopes"]) == 1

    # ── invariant (iii) — no promote/{build_label} git tag exists ─────────
    # The helper itself does not tag — the workflow does, and only on
    # green outcomes. A refused canary shape must therefore leave the
    # repo tag-list untouched.
    tag_check = subprocess.run(  # noqa: S603 — read-only git tag query
        ["git", "tag", "--list", f"promote/{build_label}"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        cwd=repo_root,
    )
    assert tag_check.returncode == 0, f"git tag --list failed: stderr={tag_check.stderr!r}"
    assert tag_check.stdout.strip() == "", (
        f"shape {shape_name!r} — refused canary unexpectedly produced tag promote/{build_label}: {tag_check.stdout!r}"
    )
