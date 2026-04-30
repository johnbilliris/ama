"""Equivalence harness package (FR-023).

Per-agent equivalence between the legacy pipeline and the new MAF agent is the
per-agent cutover gate. The harness consists of:

- ``scorers``  — pure functions that score (legacy_outputs, maf_outputs) → ``EquivalenceReport``
- ``runner``   — CLI loading per-agent fixtures and invoking both implementations,
                  emitting Markdown + JSON reports under ``reports/``
"""

from .runner import main as runner_main
from .scorers import EquivalenceReport, EquivalenceVerdict, score

__all__ = ["EquivalenceReport", "EquivalenceVerdict", "score", "runner_main"]
