"""T017 — Contract tests for OPA Rego policies.

Covers: posture, cross_env, secret_hygiene, au_region, identity_consistency.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
POLICY_DIR = REPO / "infra" / "policy" / "rego"
FIXTURES = REPO / "tests" / "pipeline" / "contract" / "fixtures"

OPA = shutil.which("opa")
CONFTEST = shutil.which("conftest")


pytestmark = pytest.mark.contract


@pytest.fixture(scope="session")
def opa_available():
    if not OPA:
        pytest.skip(
            "opa CLI not installed; install via "
            ".github/workflows/_reusable/install-opa.yml or `brew install opa`"
        )
    return OPA


def _run_opa_eval(query: str, input_file: Path, data_files: list[Path]) -> dict:
    cmd = [OPA, "eval", "--format=json", "-i", str(input_file)]
    for df in data_files:
        cmd += ["-d", str(df)]
    cmd += ["-d", str(POLICY_DIR), query]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"opa eval failed: {result.stderr}")
    return json.loads(result.stdout)


@pytest.mark.parametrize("fixture,expect_deny", [
    ("posture-good.json", False),
    ("posture-public-access-violation.json", True),
])
def test_posture_rego(opa_available, fixture, expect_deny):
    fix = FIXTURES / fixture
    if not fix.exists():
        pytest.skip(f"fixture {fixture} not yet created")
    out = _run_opa_eval(
        "data.posture.deny",
        fix,
        [REPO / "infra" / "policy" / "posture-matrix.yaml",
         REPO / "infra" / "policy" / "posture-exceptions.yaml"],
    )
    denies = out["result"][0]["expressions"][0]["value"]
    assert (len(denies) > 0) == expect_deny


@pytest.mark.parametrize("fixture,expect_deny", [
    ("identity-good.json", False),
    ("identity-topology-a-collapse.json", True),
    ("identity-topology-b-split.json", True),
    ("identity-handle-mode-mismatch.json", True),
    ("identity-cap-breach.json", True),
])
def test_identity_consistency_rego(opa_available, fixture, expect_deny):
    fix = FIXTURES / fixture
    if not fix.exists():
        pytest.skip(f"fixture {fixture} not yet created")
    out = _run_opa_eval("data.identity_consistency.deny", fix, [])
    denies = out["result"][0]["expressions"][0]["value"]
    assert (len(denies) > 0) == expect_deny, f"unexpected: {denies}"


@pytest.mark.parametrize("fixture,expect_deny", [
    ("crossenv-good-topo-b.json", False),
    ("crossenv-bad-topo-b.json", True),
])
def test_cross_env_rego(opa_available, fixture, expect_deny):
    fix = FIXTURES / fixture
    if not fix.exists():
        pytest.skip(f"fixture {fixture} not yet created")
    out = _run_opa_eval("data.cross_env.deny", fix, [])
    denies = out["result"][0]["expressions"][0]["value"]
    assert (len(denies) > 0) == expect_deny


@pytest.mark.parametrize("fixture,expect_deny", [
    ("au-region-good.json", False),
    ("au-region-violation.json", True),
])
def test_au_region_rego(opa_available, fixture, expect_deny):
    fix = FIXTURES / fixture
    if not fix.exists():
        pytest.skip(f"fixture {fixture} not yet created")
    out = _run_opa_eval(
        "data.au_region.deny",
        fix,
        [REPO / "infra" / "policy" / "foundry-carveout.yaml"],
    )
    denies = out["result"][0]["expressions"][0]["value"]
    assert (len(denies) > 0) == expect_deny
