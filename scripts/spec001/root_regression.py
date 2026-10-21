from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
from typing import Iterable, Mapping, Sequence


ROOT_REGRESSION_COMMAND = (
    "uv",
    "run",
    "--no-sync",
    "pytest",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "tests/simulation",
    "-m",
    "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging "
    "and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust",
    "--cov=apps",
    "--cov=packages",
    "--cov-report=xml",
    "--cov-report=term",
)

_FAILURE_PATTERN = re.compile(r"^FAILED\s+([^\s]+)", re.MULTILINE)
_COLLECTION_PATTERN = re.compile(r"^ERROR collecting\s+([^\r\n]+)", re.MULTILINE)
_CACHE_PATHS = (Path(".mypy_cache"), Path(".pytest_cache"), Path("tools/specify-cli/.pytest_cache"))


@dataclass(frozen=True)
class RuntimeBinding:
    python_version: str
    uv_version: str
    os: str
    architecture: str


@dataclass(frozen=True)
class RootRegressionBaseline:
    command: tuple[str, ...]
    runtime: RuntimeBinding
    exit_code: int
    failures: tuple[str, ...]
    collection_errors: tuple[str, ...]
    output_bytes: int
    output_lines: int
    output_sha256: str
    segment_id: str
    discontinuous: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_json(cls, value: str) -> RootRegressionBaseline:
        data = json.loads(value)
        data["command"] = tuple(data["command"])
        data["failures"] = tuple(data["failures"])
        data["collection_errors"] = tuple(data["collection_errors"])
        data["runtime"] = RuntimeBinding(**data["runtime"])
        return cls(**data)


class RootRegressionMismatch(RuntimeError):
    def __init__(self, new_failures: Iterable[str], new_collection_errors: Iterable[str]) -> None:
        self.new_failures = tuple(sorted(new_failures))
        self.new_collection_errors = tuple(sorted(new_collection_errors))
        super().__init__("root regression introduced identities absent from the segment baseline")


def normalize_test_identities(output: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    text = output.decode("utf-8", errors="replace").replace("\\", "/")
    failures = tuple(sorted(set(_FAILURE_PATTERN.findall(text))))
    collection_errors = tuple(sorted(value.strip() for value in _COLLECTION_PATTERN.findall(text)))
    return failures, collection_errors


def compare_root_regression(baseline: RootRegressionBaseline, candidate: RootRegressionBaseline) -> None:
    if candidate.command != baseline.command:
        raise ValueError("root regression command drift")
    if candidate.runtime != baseline.runtime:
        raise ValueError("root regression toolchain drift")
    new_failures = set(candidate.failures) - set(baseline.failures)
    new_collection_errors = set(candidate.collection_errors) - set(baseline.collection_errors)
    if new_failures or new_collection_errors:
        raise RootRegressionMismatch(new_failures, new_collection_errors)


def _hash_tree(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.exists():
        return "absent"
    if path.is_symlink():
        raise ValueError(f"guarded cache path is a symlink: {relative_path.as_posix()}")
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(path.rglob("*")):
        if child.is_symlink():
            raise ValueError(f"guarded cache child is a symlink: {child.relative_to(root).as_posix()}")
        if child.is_file():
            digest.update(child.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(child.read_bytes())
    return digest.hexdigest()


def capture_repository_cache_state(root: Path) -> dict[str, str]:
    paths = [*_CACHE_PATHS]
    paths.extend(path.relative_to(root) for path in root.glob(".coverage*"))
    paths.extend(path.relative_to(root) for path in root.glob("coverage.xml"))
    return {path.as_posix(): _hash_tree(root, path) for path in sorted(set(paths))}


def compare_repository_cache_state(before: Mapping[str, str], after: Mapping[str, str]) -> None:
    if dict(before) != dict(after):
        raise RuntimeError("repository coverage or cache state changed")


def create_external_coverage_configuration(root: Path, external_root: Path) -> Path:
    configuration = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    coverage = configuration.get("tool", {}).get("coverage", {})
    run = coverage.get("run", {})
    report = coverage.get("report", {})
    output = external_root / "root-coverage.xml"
    lines = ["[run]"]
    source = run.get("source", ["apps", "packages"])
    lines.append(f"source = {','.join(source)}")
    lines.append(f"branch = {'true' if run.get('branch', True) else 'false'}")
    omit = run.get("omit", [])
    if omit:
        lines.append("omit =")
        lines.extend(f"    {item}" for item in omit)
    lines.append("")
    lines.append("[report]")
    for key, value in report.items():
        rendered_key = key.replace("_", "-")
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, list):
            rendered = "\n".join(["", *(f"    {item}" for item in value)])
        else:
            rendered = str(value)
        lines.append(f"{rendered_key} = {rendered}")
    lines.extend(("", "[xml]", f"output = {output.as_posix()}", ""))
    path = external_root / ".coveragerc"
    path.write_text("\n".join(lines), encoding="utf-8")
    if os.name != "nt":
        os.chmod(path, 0o600)
    return path


def execute_root_regression(
    root: Path,
    runtime: RuntimeBinding,
    segment_id: str,
    *,
    discontinuous: bool = False,
) -> RootRegressionBaseline:
    before = capture_repository_cache_state(root)
    with tempfile.TemporaryDirectory(prefix="spec001-root-regression-") as temporary:
        external_root = Path(temporary)
        coverage_rc = create_external_coverage_configuration(root, external_root)
        environment = os.environ.copy()
        environment.update(
            {
                "COVERAGE_FILE": str(external_root / ".coverage"),
                "COVERAGE_RCFILE": str(coverage_rc),
                "MYPY_CACHE_DIR": str(external_root / "mypy-cache"),
                "PYTEST_ADDOPTS": "-pno:cacheprovider",
                "UV_FROZEN": "1",
            }
        )
        process = subprocess.run(
            ROOT_REGRESSION_COMMAND,
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        combined = process.stdout + process.stderr
    after = capture_repository_cache_state(root)
    compare_repository_cache_state(before, after)
    failures, collection_errors = normalize_test_identities(combined)
    return RootRegressionBaseline(
        command=ROOT_REGRESSION_COMMAND,
        runtime=runtime,
        exit_code=process.returncode,
        failures=failures,
        collection_errors=collection_errors,
        output_bytes=len(combined),
        output_lines=len(combined.splitlines()),
        output_sha256=hashlib.sha256(combined).hexdigest(),
        segment_id=segment_id,
        discontinuous=discontinuous,
    )


def validate_restart_policy(execution_mode: str, product_edits_started: bool, requested_recapture: bool) -> None:
    if execution_mode == "sovereign" and product_edits_started and requested_recapture:
        raise RuntimeError("sovereign post-edit baseline recapture is terminally prohibited")
    if execution_mode == "local-synthetic" and requested_recapture:
        return
    if requested_recapture:
        raise RuntimeError("baseline recapture is not authorized")


def root_regression_self_check() -> None:
    failures, collection_errors = normalize_test_identities(
        b"FAILED tests/unit/test_known.py::test_known - synthetic\n"
        b"ERROR collecting tests/contract/test_known.py\n"
    )
    if failures != ("tests/unit/test_known.py::test_known",):
        raise AssertionError("root failures were normalized incorrectly")
    if collection_errors != ("tests/contract/test_known.py",):
        raise AssertionError("collection errors were normalized incorrectly")
    runtime = RuntimeBinding("3.12.0", "uv 0.11.0", "synthetic", "x64")
    baseline = RootRegressionBaseline(
        ROOT_REGRESSION_COMMAND,
        runtime,
        1,
        ("tests/unit/test_known.py::test_known",),
        ("tests/contract/test_known.py",),
        10,
        1,
        "a" * 64,
        "00000000-0000-4000-8000-000000000001",
        False,
    )
    candidate = RootRegressionBaseline(
        ROOT_REGRESSION_COMMAND,
        runtime,
        0,
        (),
        (),
        0,
        0,
        "b" * 64,
        baseline.segment_id,
        False,
    )
    compare_root_regression(baseline, candidate)
    changed = RootRegressionBaseline(
        ROOT_REGRESSION_COMMAND,
        runtime,
        1,
        ("tests/unit/test_new.py::test_new",),
        (),
        1,
        1,
        "c" * 64,
        baseline.segment_id,
        False,
    )
    try:
        compare_root_regression(baseline, changed)
    except RootRegressionMismatch:
        pass
    else:
        raise AssertionError("new root failure was accepted")
    validate_restart_policy("local-synthetic", True, True)
    try:
        validate_restart_policy("sovereign", True, True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("sovereign post-edit recapture was accepted")