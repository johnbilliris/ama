"""Cycle 3 / T-AA41 / A3-01 / FR-071 / Pass-1 Q3 — concurrency integration test.

Pass-1 Q3 (`spec.md:1016-1097`) no-coalescing invariant: two concurrent
:func:`tests.staging_gates.assert_sli_thresholds` invocations against the
same red fixture data MUST produce TWO distinct ``StagingPromotionRefused``
exceptions, TWO distinct ``staging_promotion.refused`` audit envelopes,
TWO distinct ``staging_promotion_correlation_id`` UUIDs, and (when the
helper is invoked via two subprocesses) TWO non-zero process exits.

Concurrent invocations on the SAME ref are queued by the workflow-level
``concurrency:`` block in ``.github/workflows/staging-promotion.yml``
(T-AA37); concurrent invocations on DIFFERENT refs (cross-ref races)
DO race — and that is the case this test exercises.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tests.staging_gates import (
    MIN_SAMPLES_PER_SLI_24H,
    StagingPromotionRefused,
    assert_sli_thresholds,
)

_UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _red_results() -> dict:
    """Red Z6 fixture (gpt-4o p95 over 5000 ms breach)."""

    return {
        "SLI-Z6": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "per_model": {
                "gpt-4o": {"p95_latency_ms": 5500},
                "gpt-4o-mini": {"p95_latency_ms": 1200},
            },
        },
        "SLI-Z7": {
            "sample_count": MIN_SAMPLES_PER_SLI_24H + 5,
            "drift_budget_pct": 99.7,
        },
    }


def _invoke_with_capturing_sink() -> tuple[Exception | None, list[dict]]:
    """Invoke ``assert_sli_thresholds`` once; return (exception, [envelope])."""

    captured: list[dict] = []

    def sink(envelope) -> None:  # type: ignore[no-untyped-def]
        captured.append(dict(envelope))

    try:
        assert_sli_thresholds(
            sli_results=_red_results(),
            envelope_sink=sink,
            build_label="v0.36.3-rc.concurrency",
        )
        return None, captured
    except StagingPromotionRefused as exc:
        return exc, captured


def test_two_concurrent_invocations_produce_distinct_envelopes() -> None:
    """Pass-1 Q3 — concurrent invocations → distinct exceptions + UUIDs."""

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(_invoke_with_capturing_sink)
        future_b = executor.submit(_invoke_with_capturing_sink)
        exc_a, captured_a = future_a.result(timeout=30)
        exc_b, captured_b = future_b.result(timeout=30)

    # Two distinct exception instances, both StagingPromotionRefused.
    assert exc_a is not exc_b
    assert isinstance(exc_a, StagingPromotionRefused)
    assert isinstance(exc_b, StagingPromotionRefused)

    # Two envelopes — one per call.
    assert len(captured_a) == 1
    assert len(captured_b) == 1

    # Two distinct staging_promotion_correlation_id values; both UUID4.
    uuid_a = captured_a[0]["details"]["staging_promotion_correlation_id"]
    uuid_b = captured_b[0]["details"]["staging_promotion_correlation_id"]
    assert uuid_a != uuid_b, (
        "Pass-1 Q3 no-coalescing — concurrent invocations MUST produce "
        f"distinct correlation_ids; got {uuid_a!r} == {uuid_b!r}"
    )
    assert _UUID4_RE.match(uuid_a)
    assert _UUID4_RE.match(uuid_b)

    # Top-level / nested correlation_id parity per §3.26.
    assert (
        captured_a[0]["correlation_id"]
        == captured_a[0]["details"]["staging_promotion_correlation_id"]
    )
    assert (
        captured_b[0]["correlation_id"]
        == captured_b[0]["details"]["staging_promotion_correlation_id"]
    )


def _subprocess_script() -> str:
    """Return the script run by the subprocess-exit-code test below."""

    return textwrap.dedent(
        """
        import importlib.util
        import json
        import pathlib
        import sys

        repo_root = pathlib.Path(sys.argv[0]).resolve().parent if sys.argv[0] else pathlib.Path.cwd()
        # Resolve from CWD instead — the test sets cwd=repo_root.
        repo_root = pathlib.Path.cwd()
        gates_path = repo_root / "tests" / "staging_gates.py"
        spec = importlib.util.spec_from_file_location("staging_gates", gates_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["staging_gates"] = module
        spec.loader.exec_module(module)

        results = {
            "SLI-Z6": {
                "sample_count": module.MIN_SAMPLES_PER_SLI_24H + 5,
                "per_model": {"gpt-4o": {"p95_latency_ms": 5500}},
            },
            "SLI-Z7": {
                "sample_count": module.MIN_SAMPLES_PER_SLI_24H + 5,
                "drift_budget_pct": 99.7,
            },
        }

        captured = []

        def sink(env):
            captured.append(env)

        try:
            module.assert_sli_thresholds(
                sli_results=results,
                envelope_sink=sink,
                build_label="v0.36.3-rc.subproc",
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


def test_two_concurrent_subprocesses_yield_two_non_zero_exits() -> None:
    """Two concurrent subprocesses exit non-zero with distinct correlation_ids."""

    script = _subprocess_script()
    repo_root = str(Path(__file__).resolve().parents[2])

    # Subprocess inherits PYTHONPATH but needs the repo root explicitly so
    # ``tests.staging_gates`` resolves. ``tests/`` lacks an ``__init__.py``,
    # but the implicit-namespace-package machinery picks it up when the
    # repo root is on ``sys.path``.
    import os as _os
    env = _os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        repo_root + (_os.pathsep + existing_path if existing_path else "")
    )

    def run_one() -> tuple[int, dict]:
        proc = subprocess.run(  # noqa: S603 — controlled stdin script, no shell
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
            cwd=repo_root,
            env=env,
        )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {
                "refused": False,
                "envelopes": [],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        return proc.returncode, payload

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(run_one)
        future_b = executor.submit(run_one)
        rc_a, payload_a = future_a.result(timeout=60)
        rc_b, payload_b = future_b.result(timeout=60)

    # Both subprocesses exit non-zero (workflow-boundary contract).
    assert rc_a != 0, f"subprocess A exit code expected non-zero; got {rc_a}; payload={payload_a!r}"
    assert rc_b != 0, f"subprocess B exit code expected non-zero; got {rc_b}; payload={payload_b!r}"

    # Both produced an envelope; the correlation_ids are distinct.
    assert payload_a["refused"] is True, f"payload_a={payload_a!r}"
    assert payload_b["refused"] is True, f"payload_b={payload_b!r}"
    uuid_a = payload_a["envelopes"][0]["details"]["staging_promotion_correlation_id"]
    uuid_b = payload_b["envelopes"][0]["details"]["staging_promotion_correlation_id"]
    assert uuid_a != uuid_b, (
        "subprocess concurrency — distinct correlation_ids required; "
        f"got {uuid_a!r} == {uuid_b!r}"
    )
