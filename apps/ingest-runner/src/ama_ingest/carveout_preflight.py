"""Carve-out pre-flight (Spec 036 T057; FR-RAG-CV-01..02; ingest-pipeline.md §3.7).

Fail-closed gate that runs **before** the embedder issues its first call. Loads
``infra/parameters/foundry-carveout.yaml``, locates the row for the resolved
embedding deployment, and verifies:

- a row exists for ``(model_name, region)``;
- ``review_date`` is in the future and ≤ 12 months out;
- ``approver_identities`` contains ≥ 2 non-placeholder entries;
- ``data_minimisation_required`` and ``classification_filter_required``
  are both ``true`` (schema-bound but re-checked here for defence-in-depth).

The pre-flight either returns the row or raises ``CarveoutPreflightError`` —
the ingest-runner CLI surfaces the error and exits with code 1 (lint-failure)
**before** any embedding budget is touched.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #


REVIEW_HORIZON_DAYS: int = 365
MIN_APPROVERS: int = 2
PLACEHOLDER_TOKENS: frozenset[str] = frozenset({"TODO", "<approver-1>", "<approver-2>", "PLACEHOLDER", ""})
AU_REGIONS: frozenset[str] = frozenset({"australiaeast", "australiasoutheast"})


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class CarveoutPreflightError(RuntimeError):
    """Pre-flight check failed; ingest MUST abort before any embedding call."""


# --------------------------------------------------------------------------- #
# Result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CarveoutRow:
    model_name: str
    region: str
    purpose: str
    business_justification: str
    approver_identities: tuple[str, ...]
    review_date: date
    data_minimisation_required: bool
    classification_filter_required: bool


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #


def load_registry(path: Path) -> list[dict[str, Any]]:
    """Parse the registry YAML and return its ``deployments:`` list."""
    try:
        import yaml  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise CarveoutPreflightError("PyYAML not installed") from exc
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    deployments = raw.get("deployments")
    if not isinstance(deployments, list):
        raise CarveoutPreflightError(f"{path} has no 'deployments:' list")
    return [d for d in deployments if isinstance(d, dict)]


def find_row(
    deployments: list[dict[str, Any]],
    *,
    model_name: str,
    region: str,
) -> dict[str, Any] | None:
    """Locate a row by ``(model_name, region)`` (case-insensitive on region)."""
    region_l = region.lower()
    for row in deployments:
        if row.get("model_name") == model_name and str(row.get("region", "")).lower() == region_l:
            return row
    return None


# --------------------------------------------------------------------------- #
# Validate
# --------------------------------------------------------------------------- #


def validate_row(row: dict[str, Any], *, today: date | None = None) -> CarveoutRow:
    """Validate a single registry row; return a typed ``CarveoutRow`` on success."""
    today = today or datetime.now().date()
    review = row.get("review_date")
    if isinstance(review, str):
        review = date.fromisoformat(review)
    if not isinstance(review, date):
        raise CarveoutPreflightError(f"review_date missing or unparseable for {row.get('model_name')!r}")
    if review <= today:
        raise CarveoutPreflightError(f"review_date {review.isoformat()} expired for {row.get('model_name')!r}")
    if review > today + timedelta(days=REVIEW_HORIZON_DAYS):
        raise CarveoutPreflightError(
            f"review_date {review.isoformat()} > {REVIEW_HORIZON_DAYS} days out for {row.get('model_name')!r}"
        )

    approvers = row.get("approver_identities") or []
    real_approvers = [a for a in approvers if isinstance(a, str) and a not in PLACEHOLDER_TOKENS]
    if len(real_approvers) < MIN_APPROVERS:
        raise CarveoutPreflightError(
            f"approver_identities for {row.get('model_name')!r} has "
            f"{len(real_approvers)} non-placeholder entries; need ≥ {MIN_APPROVERS}"
        )

    region = str(row.get("region", "")).lower()
    if region not in AU_REGIONS:
        # Non-AU is permitted but only via the data-minimisation gateway path.
        # Pre-flight does not deny non-AU for embedding (the gateway handles the
        # data-minimisation rule); we just log a structured warning.
        logger.warning(
            "non-AU embedding deployment %s/%s — gateway path required",
            row.get("model_name"),
            region,
        )

    if not row.get("data_minimisation_required"):
        raise CarveoutPreflightError(f"data_minimisation_required must be true for {row.get('model_name')!r}")
    if not row.get("classification_filter_required"):
        raise CarveoutPreflightError(f"classification_filter_required must be true for {row.get('model_name')!r}")

    return CarveoutRow(
        model_name=str(row.get("model_name")),
        region=region,
        purpose=str(row.get("purpose", "")),
        business_justification=str(row.get("business_justification", "")),
        approver_identities=tuple(real_approvers),
        review_date=review,
        data_minimisation_required=bool(row.get("data_minimisation_required")),
        classification_filter_required=bool(row.get("classification_filter_required")),
    )


# --------------------------------------------------------------------------- #
# Public entry-point
# --------------------------------------------------------------------------- #


def preflight(
    *,
    registry_path: Path,
    model_name: str,
    region: str,
    today: date | None = None,
) -> CarveoutRow:
    """Run the full pre-flight; raise on any violation, return on success."""
    deployments = load_registry(registry_path)
    row = find_row(deployments, model_name=model_name, region=region)
    if row is None:
        raise CarveoutPreflightError(
            f"no carveout registry row for ({model_name!r}, {region!r}); "
            f"add a row to {registry_path} before re-running ingest"
        )
    return validate_row(row, today=today)


__all__ = [
    "AU_REGIONS",
    "CarveoutPreflightError",
    "CarveoutRow",
    "MIN_APPROVERS",
    "PLACEHOLDER_TOKENS",
    "REVIEW_HORIZON_DAYS",
    "find_row",
    "load_registry",
    "preflight",
    "validate_row",
]
