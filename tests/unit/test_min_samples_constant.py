"""Wave C / T-AA17 — ``MIN_SAMPLES_PER_SLI_24H`` constant guard.

Asserts the constant exists, equals 30 (pass-2 Q4 CLT floor), and is
exported from ``tests.staging_gates``.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
"""

from __future__ import annotations

import tests.staging_gates as gates


def test_min_samples_constant_value() -> None:
    assert gates.MIN_SAMPLES_PER_SLI_24H == 30


def test_min_samples_constant_exported() -> None:
    assert "MIN_SAMPLES_PER_SLI_24H" in gates.__all__


def test_assert_sli_thresholds_exported() -> None:
    assert "assert_sli_thresholds" in gates.__all__
    assert callable(gates.assert_sli_thresholds)
