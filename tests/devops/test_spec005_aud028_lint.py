from __future__ import annotations

from pathlib import Path

from tools.lint.check_spec005_aud028 import run

ROOT = Path(__file__).resolve().parents[2]


def test_spec005_aud028_passes_for_repository_feature() -> None:
    failures = run(ROOT / "specs/005-data-source-governance", ROOT / "specs")
    assert failures == []


def test_spec005_aud028_fails_if_hyp_status_not_tested(tmp_path: Path) -> None:
    src_feature = ROOT / "specs/005-data-source-governance"
    dst_feature = tmp_path / "specs/005-data-source-governance"
    for rel in (
        "spec.md",
        "checklists/requirements.md",
        "implementation-review-tasks.md",
        "contracts/readiness-manifest.schema.json",
        "evidence/readiness-manifest.template.json",
        "evidence/quickstart-rehearsal-manifest.template.json",
        "evidence/readiness-snapshot.generated.json",
        "evidence/HYP-043.md",
    ):
        target = dst_feature / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((src_feature / rel).read_text(encoding="utf-8"), encoding="utf-8")

    hyp = dst_feature / "evidence/HYP-043.md"
    text = hyp.read_text(encoding="utf-8")
    hyp.write_text(text.replace("Not tested", "Validated", 1), encoding="utf-8")

    failures = run(dst_feature, tmp_path / "specs")
    assert any("Status must be exactly 'Not tested'" in item for item in failures)
