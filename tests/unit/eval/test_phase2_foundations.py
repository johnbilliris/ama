"""Phase 2 foundational smoke tests (repos, evidence, role guard)."""

from __future__ import annotations

import os
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
for p in (
    _REPO_ROOT,
    _REPO_ROOT / "apps" / "eval-runner" / "src",
    _REPO_ROOT / "packages" / "eval-core" / "src",
):
    sys.path.insert(0, str(p))

# Force in-memory backends
os.environ.pop("COSMOS_ENDPOINT", None)

from ama_eval.evidence import build_evidence_bundle  # noqa: E402
from ama_eval_core.models import (  # noqa: E402
    ApprovalEntry,
    EvaluationCase,
    ExpectedAction,
    ExpectedBehaviour,
    HazardTag,
    Provenance,
    ProvenanceMeta,
    Severity,
    Tone,
)

from apps.api.app.repositories.eval.repositories import (  # noqa: E402
    AuditRepository,
    DatasetRepository,
    MetricRepository,
    RunRepository,
)


def _case(case_id: str = "case-001") -> EvaluationCase:
    return EvaluationCase(
        caseId=case_id,
        datasetId="d",
        version="1.0.0",
        inputs={"prompt": "p"},
        expectedBehaviour=ExpectedBehaviour(
            mustInclude=["call 000"],
            mustNotInclude=["enter"],
            expectedAction=ExpectedAction.answer,
            referToAuthority=True,
            tone=Tone.directive,
        ),
        sensitivityLabels=[],
        hazardTags=[HazardTag.flood],
        jurisdictionTags=["AU-NSW"],
        severity=Severity.medium,
        language="en-AU",
        provenance=Provenance.synthetic,
        provenanceMeta=ProvenanceMeta(author="a@b", reviewer="c@d"),
        approvalState="approved",
        approvalChain=[
            ApprovalEntry(
                role="reviewer",
                principal="c@d",
                action="approve",
                timestamp=datetime.now(UTC),
            )
        ],
    )


def test_dataset_repo_in_memory_roundtrip():
    repo = DatasetRepository()
    c = _case()
    repo.save_case(c)
    cases = repo.list_cases("d", version="1.0.0")
    assert len(cases) == 1 and cases[0].caseId == "case-001"


def test_run_repo_status_filter():
    repo = RunRepository()
    runs = repo.list_runs(status="queued")
    assert isinstance(runs, list)


def test_metric_repo_save_and_list():
    from ama_eval_core.models import (
        MetricDefinitionVersion,
        MetricFamily,
        MetricTier,
        ScoreScale,
    )

    repo = MetricRepository()
    m = MetricDefinitionVersion(
        metricId="must-include",
        version="1.0.0",
        family=MetricFamily.quality,
        scoreScale=ScoreScale(min=0.0, max=1.0),
        scoringMethod="rule-based",
        tier=MetricTier.rule_based,
        passThreshold=0.9,
    )
    repo.save_metric(m)
    metrics = repo.list_metrics()
    assert any(x.metricId == "must-include" for x in metrics)


def test_audit_repo_emit_action():
    from ama_eval_core.audit import AuditAction

    repo = AuditRepository()
    repo.emit_action(
        action=AuditAction.run_queued,
        principal="t",
        subject_type="run",
        subject_id="r1",
        run_id="r1",
    )
    evts = repo.list_for_run("r1")
    assert len(evts) == 1


def test_evidence_bundle_has_sha256_manifest():
    info = build_evidence_bundle(
        run={"runId": "r1"},
        scorecard={"runId": "r1"},
        audit_events=[],
        dataset_manifest={"datasetId": "d", "version": "1.0.0"},
        metric_set={"version": "1.0.0"},
        judge_set={"version": "1.0.0"},
        model_registry={"version": "1.0.0"},
    )
    assert info.manifest_sha256.startswith("sha256:")
    assert len(info.bundle_bytes) > 0
    import io

    with tarfile.open(fileobj=io.BytesIO(info.bundle_bytes), mode="r:gz") as t:
        assert "manifest.json" in t.getnames()
