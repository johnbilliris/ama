"""T-J23 — SC-005 post-exercise economic-loss harness (test entry-point).

Pytest discovery hook for ``tests.measurement.sc005_economic_loss``. The
harness logic lives in the sibling module to keep
``tests/measurement/`` a pure Python package (no pytest collision).

Per Assumption A9 — economic loss reduction is measured against the
synthetic AIDR-aligned profile in
:data:`tests.simulation.paired_exercise_harness.HAZARD_BASE_LOSS_M_PER_HOUR`.
"""

from __future__ import annotations

# Re-export the test functions from the harness module so pytest discovers
# them under tests/simulation/.
from tests.measurement.sc005_economic_loss import (  # noqa: F401
    test_sc005_30_pair_corpus_against_staging,
    test_sc005_local_30_pair_run_meets_threshold,
    test_sc005_ndjson_artefact_round_trips,
)
