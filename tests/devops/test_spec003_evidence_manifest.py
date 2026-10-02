from __future__ import annotations

import json
from pathlib import Path

from tools.lint.check_spec003_evidence_manifest import run

ROOT = Path(__file__).resolve().parents[2]


def _sample_entry(sc_id: str) -> dict[str, object]:
    return {
        "scId": sc_id,
        "outcome": "UNVERIFIED",
        "revisionSha": "5b44c249f00e0e4a13ea2579c8c33d06e2471d7a",
        "command": "n/a",
        "environment": "local-python3.14",
        "fixtureCohort": "external-gate",
        "denominator": "0/1 runs",
        "artifactPath": "",
        "artifactSha256": "",
        "reason": "External evidence not executed in this session.",
    }


def test_spec003_manifest_passes_repository_baseline() -> None:
    manifest = ROOT / "specs/003-rubric-gap-closure/evidence-manifest.json"
    violations = run(manifest, ROOT)
    assert violations == []


def test_spec003_manifest_fails_on_missing_sc_entry(tmp_path: Path) -> None:
    entries = [_sample_entry(f"SC-{index:03d}") for index in range(1, 13)]
    manifest_path = tmp_path / "evidence-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "feature": "003-rubric-gap-closure",
                "generatedAt": "2026-09-15",
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    violations = run(manifest_path, tmp_path)
    assert any("exactly 13 entries" in violation for violation in violations)
    assert any("Missing SC entries" in violation for violation in violations)


def test_spec003_manifest_fails_pass_row_without_artifact(tmp_path: Path) -> None:
    entries = [_sample_entry(f"SC-{index:03d}") for index in range(1, 14)]
    entries[4]["outcome"] = "PASS"
    entries[4]["command"] = "py -3.14 -m pytest tests/integration/test_handoff_chain.py -q"
    entries[4]["denominator"] = "4/4 tests"
    entries[4]["reason"] = ""

    manifest_path = tmp_path / "evidence-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "feature": "003-rubric-gap-closure",
                "generatedAt": "2026-09-15",
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    violations = run(manifest_path, tmp_path)
    assert any("PASS rows require artifactPath and artifactSha256" in violation for violation in violations)
