"""Server-side `manual_row_ratio` recomputation (T033).

Walks the JSON sidecar's `rows[]` array and counts entries where
`provenance.tag == "manual"`. Emits the App Insights custom metric
`evidence_pack.manual_row_ratio` with dimensions
`{ artefact_id, publication_id, environment }`.

Citations: RES-05, FR-037, plan.md § Performance Goals.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RatioResult:
    manual_row_count: int
    total_row_count: int
    manual_row_ratio: float


def compute_ratio(rows: list[dict[str, Any]]) -> RatioResult:
    """Compute manual_row_ratio from a sidecar `rows[]` array."""
    total = len(rows)
    manual = sum(
        1
        for r in rows
        if isinstance(r, dict) and isinstance(r.get("provenance"), dict) and r["provenance"].get("tag") == "manual"
    )
    ratio = (manual / total) if total else 0.0
    return RatioResult(manual_row_count=manual, total_row_count=total, manual_row_ratio=ratio)


def emit_metric(artefact_id: str, publication_id: str, ratio: float) -> None:
    """Emit `evidence_pack.manual_row_ratio` via OpenTelemetry if available.

    Falls back to a structured log line when the OpenTelemetry SDK is not
    initialised (e.g., in unit tests). Honours NN-2 — no PII in dimensions.
    """
    environment = os.environ.get("AMA_ENV", "dev")
    try:
        from opentelemetry import metrics

        meter = metrics.get_meter("ama.evidence_pack")
        gauge = meter.create_gauge(
            name="evidence_pack.manual_row_ratio",
            description="Manual-row ratio per artefact per publication (FR-037, FR-038).",
            unit="1",
        )
        gauge.set(
            ratio,
            attributes={
                "artefact_id": artefact_id,
                "publication_id": publication_id,
                "environment": environment,
            },
        )
    except Exception:
        logger.info(
            "evidence_pack.manual_row_ratio",
            extra={
                "artefact_id": artefact_id,
                "publication_id": publication_id,
                "environment": environment,
                "manual_row_ratio": ratio,
            },
        )
