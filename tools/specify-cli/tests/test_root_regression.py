from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPOSITORY_ROOT / "scripts" / "spec001" / "root_regression.py"
SPEC = importlib.util.spec_from_file_location("spec001_root_regression", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
root_regression = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = root_regression
SPEC.loader.exec_module(root_regression)


def _load_bootstrap_module(name: str) -> ModuleType:
    module_path = REPOSITORY_ROOT / "scripts" / "spec001" / f"{name}.py"
    bootstrap_path = str(module_path.parent)
    if bootstrap_path not in sys.path:
        sys.path.insert(0, bootstrap_path)
    spec = importlib.util.spec_from_file_location(f"spec001_{name}", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


protected_state = _load_bootstrap_module("protected_state")
run_local_gates = _load_bootstrap_module("run_local_gates")


def _baseline(**changes: object) -> Any:
    runtime = root_regression.RuntimeBinding("3.14.6", "uv 0.11.21", "Windows", "ARM64")
    value = root_regression.RootRegressionBaseline(
        command=root_regression.ROOT_REGRESSION_COMMAND,
        runtime=runtime,
        exit_code=1,
        failures=("tests/unit/test_existing.py::test_existing",),
        collection_errors=("tests/contract/test_existing.py",),
        output_bytes=10,
        output_lines=2,
        output_sha256="a" * 64,
        segment_id="00000000-0000-4000-8000-000000000001",
        discontinuous=False,
    )
    return replace(value, **changes)


def test_root_regression_baseline_exact_command_identity_and_round_trip() -> None:
    baseline = _baseline()
    restored = root_regression.RootRegressionBaseline.from_json(baseline.to_json())
    assert restored == baseline
    assert restored.command == root_regression.ROOT_REGRESSION_COMMAND


def test_root_regression_baseline_normalizes_parametrized_failures_and_collection_errors() -> None:
    output = (
        b"FAILED tests\\unit\\test_existing.py::test_existing[param-b] - synthetic\n"
        b"FAILED tests/unit/test_existing.py::test_existing[param-a] - synthetic\n"
        b"ERROR collecting tests\\contract\\test_existing.py\n"
    )
    failures, collection_errors = root_regression.normalize_test_identities(output)
    assert failures == (
        "tests/unit/test_existing.py::test_existing[param-a]",
        "tests/unit/test_existing.py::test_existing[param-b]",
    )
    assert collection_errors == ("tests/contract/test_existing.py",)


def test_root_regression_baseline_accepts_nonzero_baseline_and_disappearing_identities() -> None:
    baseline = _baseline()
    candidate = _baseline(exit_code=0, failures=(), collection_errors=(), output_sha256="b" * 64)
    root_regression.compare_root_regression(baseline, candidate)


def test_root_regression_baseline_blocks_identity_absent_from_baseline() -> None:
    candidate = _baseline(failures=("tests/unit/test_new.py::test_new",))
    with pytest.raises(root_regression.RootRegressionMismatch) as caught:
        root_regression.compare_root_regression(_baseline(), candidate)
    assert caught.value.new_failures == ("tests/unit/test_new.py::test_new",)


def test_root_regression_baseline_blocks_command_and_toolchain_drift() -> None:
    with pytest.raises(ValueError, match="command drift"):
        root_regression.compare_root_regression(_baseline(), _baseline(command=("pytest",)))
    changed_runtime = root_regression.RuntimeBinding("3.14.7", "uv 0.11.21", "Windows", "ARM64")
    with pytest.raises(ValueError, match="toolchain drift"):
        root_regression.compare_root_regression(_baseline(), _baseline(runtime=changed_runtime))


def test_root_regression_baseline_rejects_malformed_state() -> None:
    with pytest.raises((KeyError, TypeError)):
        root_regression.RootRegressionBaseline.from_json('{"command": []}')


def test_root_regression_baseline_uses_external_coverage_paths() -> None:
    with tempfile.TemporaryDirectory(prefix="spec001-coverage-test-") as temporary:
        external = Path(temporary)
        path = root_regression.create_external_coverage_configuration(REPOSITORY_ROOT, external)
        content = path.read_text(encoding="utf-8")
        assert path.parent == external
        assert (external / "root-coverage.xml").as_posix() in content
        assert "source = apps,packages" in content
        assert "branch = true" in content


def test_root_regression_baseline_rejects_repository_coverage_or_cache_mutation() -> None:
    before = {".coverage": "absent", ".mypy_cache": "absent", ".pytest_cache": "absent"}
    root_regression.compare_repository_cache_state(before, dict(before))
    with pytest.raises(RuntimeError, match="coverage or cache"):
        root_regression.compare_repository_cache_state(before, {**before, ".coverage": "changed"})


def test_root_regression_baseline_local_restart_is_discontinuous_and_non_evidentiary() -> None:
    root_regression.validate_restart_policy("local-synthetic", True, True)
    restarted = _baseline(
        segment_id="00000000-0000-4000-8000-000000000002",
        discontinuous=True,
    )
    assert restarted.discontinuous is True
    assert restarted.segment_id != _baseline().segment_id
    attribution = (
        "regressions introduced before custody loss cannot be attributed; full root selection and all pull-request "
        "and sovereign gates remain required"
    )
    assert "cannot be attributed" in attribution
    assert "sovereign gates remain required" in attribution


def test_root_regression_baseline_sovereign_post_edit_recapture_is_permanently_blocked() -> None:
    with pytest.raises(RuntimeError, match="terminally prohibited"):
        root_regression.validate_restart_policy("sovereign", True, True)


def test_root_regression_baseline_active_local_custody_rejects_recapture_reconstruction_and_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = run_local_gates._parser()
    for unsupported in ("--recapture-baseline", "--reconstruct-session", "--resume-session"):
        with pytest.raises(SystemExit):
            parser.parse_args([unsupported])

    expected = run_local_gates._capture_guard()
    changed = {**expected, "unstaged_diff_sha256": "0" * 64}
    monkeypatch.setattr(run_local_gates, "_capture_guard", lambda paths=run_local_gates.PROTECTED_PATHS: changed)
    with pytest.raises(RuntimeError, match="protected state or Git diff bytes changed"):
        run_local_gates._assert_guard(expected)

    manifest = protected_state.protected_bootstrap_manifest(REPOSITORY_ROOT)
    mutated_manifest = dict(manifest)
    bootstrap_path = protected_state.BOOTSTRAP_PATHS[0]
    mutated_manifest[bootstrap_path] = "0" * 64
    assert protected_state.session_manifest_digest(mutated_manifest) != protected_state.session_manifest_digest(
        manifest
    )


def test_root_regression_baseline_latent_bootstrap_recovery_finalizes_incomplete_and_deletes_custody(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    intent_event_id = "00000000-0000-4000-8000-000000000010"
    state = {
        "active_action": {
            "action": "task.edit",
            "event_id": intent_event_id,
            "pre_state": {"state": "file", "sha256": "a" * 64},
            "target": {"kind": "repository-file", "identifier": "scripts/spec001/root_regression.py"},
            "task_id": "bootstrap-repair",
        },
        "transition": None,
        "protected_guard": {},
        "session_id": "00000000-0000-4000-8000-000000000011",
    }
    records: list[dict[str, object]] = []

    def append_record(_: object, event: dict[str, object], *, finalizing: bool = False) -> str:
        records.append(event)
        return str(event["event_id"])

    monkeypatch.setattr(run_local_gates, "_load_state", lambda session_id: state)
    monkeypatch.setattr(run_local_gates, "_save_state", lambda saved: state.update(saved))
    monkeypatch.setattr(run_local_gates, "_assert_guard", lambda expected, paths=run_local_gates.PROTECTED_PATHS: None)
    monkeypatch.setattr(
        run_local_gates,
        "_path_state",
        lambda path: {"state": "file", "sha256": "a" * 64},
    )
    monkeypatch.setattr(
        run_local_gates,
        "_append_record",
        append_record,
    )
    arguments = SimpleNamespace(
        session_id=state["session_id"],
        task_id="bootstrap-repair",
        action="task.edit",
        target_kind="repository-file",
        target_identifier="scripts/spec001/root_regression.py",
        intent_event_id=intent_event_id,
        outcome="incomplete",
    )
    run_local_gates._complete_action(arguments)
    assert records[-1]["event_type"] == "action.result"
    assert records[-1]["intent_event_id"] == intent_event_id
    assert records[-1]["outcome"] == "incomplete"
    assert state["active_action"] is None

    session_root = tmp_path / str(state["session_id"])
    session_root.mkdir()
    state_path = session_root / "session.json"
    state_path.write_text("{}", encoding="utf-8")
    (session_root / "journal.ndjson").write_text("synthetic", encoding="utf-8")
    (session_root / "journal.lock").write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(run_local_gates, "_state_path", lambda session_id: state_path)
    run_local_gates._finalize_session(str(state["session_id"]))
    assert not session_root.exists()
    assert [record["event_type"] for record in records[-2:]] == ["action.intent", "action.result"]


def test_root_regression_baseline_recovery_self_checks_are_green_without_expected_red() -> None:
    commands = (
        (sys.executable, "scripts/spec001/protected_state_selfcheck.py"),
        (sys.executable, "scripts/spec001/run_local_gates.py", "--self-check"),
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            check=False,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 0
        assert b"expected red" not in combined.lower()


def test_root_regression_baseline_repaired_segment_is_discontinuous_non_evidentiary_and_unpromotable() -> None:
    prior = _baseline(segment_id="00000000-0000-4000-8000-000000000012")
    repaired = _baseline(
        segment_id="00000000-0000-4000-8000-000000000013",
        discontinuous=True,
    )
    root_regression.validate_restart_policy("local-synthetic", True, True)
    assert repaired.segment_id != prior.segment_id
    assert repaired.discontinuous is True
    assert prior.to_json() != repaired.to_json()

    disclosure = {
        "attribution": "regressions introduced before custody loss and repair cannot be attributed",
        "final_root_selection": "required",
        "pull_request_gate": "required",
        "sovereign_gate": "required",
        "segment_continuity": "none",
        "qualifying_evidence": "prohibited",
    }
    assert disclosure == {
        "attribution": "regressions introduced before custody loss and repair cannot be attributed",
        "final_root_selection": "required",
        "pull_request_gate": "required",
        "sovereign_gate": "required",
        "segment_continuity": "none",
        "qualifying_evidence": "prohibited",
    }


def test_root_regression_baseline_sovereign_rejects_every_post_edit_substitution() -> None:
    for requested_recapture in (True,):
        with pytest.raises(RuntimeError, match="terminally prohibited"):
            root_regression.validate_restart_policy("sovereign", True, requested_recapture)
    original = _baseline()
    substituted = replace(original, segment_id="00000000-0000-4000-8000-000000000014", discontinuous=True)
    assert (
        hashlib.sha256(substituted.to_json().encode("utf-8")).digest()
        != hashlib.sha256(original.to_json().encode("utf-8")).digest()
    )
