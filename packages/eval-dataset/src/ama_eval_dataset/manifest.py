"""Build EvaluationDatasetVersion manifest from a corpus of EvaluationCase instances."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from ama_eval_core.models import (
    ApprovalEntry,
    DatasetState,
    DistributionEntry,
    EvaluationCase,
    EvaluationDatasetVersion,
)

from .distribution import validate_distribution


def build_manifest(
    cases: list[EvaluationCase],
    dataset_id: str,
    version: str,
    published_by: str,
    blob_uri: str,
) -> EvaluationDatasetVersion:
    """Build an EvaluationDatasetVersion from a list of cases.

    Computes contentHash as sha256 over canonical (sorted, no-whitespace) JSON of all cases.
    """
    canonical = json.dumps(
        [json.loads(c.model_dump_json()) for c in cases],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    content_hash = f"sha256:{digest}"

    dist_raw = validate_distribution(cases)
    distribution: dict[str, DistributionEntry] = {}
    for dim_key, dim_val in dist_raw.items():
        for label, entry in dim_val.items():
            distribution[f"{dim_key}:{label}"] = DistributionEntry(
                count=entry["count"],
                percentage=entry["percentage"],
            )

    language_scope = sorted({c.language for c in cases})
    now = datetime.now(tz=UTC)

    return EvaluationDatasetVersion(
        datasetId=dataset_id,
        version=version,
        state=DatasetState.published,
        contentHash=content_hash,
        caseCount=len(cases),
        distribution=distribution,
        languageScope=language_scope,
        manifestBlobUri=blob_uri,
        publishedAt=now,
        publishedBy=published_by,
        approvalChain=[
            ApprovalEntry(
                role="eval-author",
                principal=published_by,
                action="approve",
                timestamp=now,
            )
        ],
    )
