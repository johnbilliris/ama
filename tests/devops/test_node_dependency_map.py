from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "capture_node_dependency_map.mjs"


def _graph(root: str) -> list[dict[str, object]]:
    return [
        {"name": "ama", "path": root},
        {
            "name": "@ama/web",
            "version": "0.1.0",
            "path": f"{root}/apps/web",
            "dependencies": {
                "next": {
                    "version": "16.3.8",
                    "path": f"{root}/node_modules/.pnpm/next@16.3.8/node_modules/next",
                    "resolved": "https://packagefeedproxy.microsoft.io/npm/next/-/next-16.3.8.tgz",
                    "optionalDependencies": {
                        "sharp": {
                            "version": "0.35.5",
                            "path": f"{root}/node_modules/.pnpm/sharp@0.35.5/node_modules/sharp",
                        }
                    },
                }
            },
        },
    ]


def _capture(tmp_path: Path, graph: object, root: str, output: str = "map.tsv") -> subprocess.CompletedProcess[str]:
    source = tmp_path / "graph.json"
    source.write_text(json.dumps(graph), encoding="utf-8")
    destination = "-" if output == "-" else str(tmp_path / output)
    return subprocess.run(
        ["node", str(SCRIPT), str(source), destination, root],
        capture_output=True,
        text=True,
        check=False,
    )


def test_maps_preserve_nested_versions_and_ignore_copy_location(tmp_path: Path) -> None:
    first = _capture(tmp_path, _graph("/candidate-a"), "/candidate-a", "a.tsv")
    second = _capture(tmp_path, _graph("/candidate-b"), "/candidate-b", "b.tsv")
    assert first.returncode == second.returncode == 0, first.stderr + second.stderr
    assert (tmp_path / "a.tsv").read_bytes() == (tmp_path / "b.tsv").read_bytes()
    lines = (tmp_path / "a.tsv").read_text().splitlines()
    assert len(lines) == 4
    assert lines == sorted(lines)
    assert all(len(line.split("\t")) == 6 and line == line.rstrip() for line in lines)
    assert any("\tsharp\t0.35.5\t" in line for line in lines)
    assert "Installed dependency-map rows: 4" in first.stderr


def test_stdout_contains_only_the_exact_map(tmp_path: Path) -> None:
    result = _capture(tmp_path, _graph("/candidate"), "/candidate", "-")
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.splitlines()) == 4
    assert "Installed dependency-map rows" not in result.stdout


@pytest.mark.parametrize(
    "resolved",
    [
        "https://registry.npmjs.org/next/-/next-16.3.8.tgz",
        "https://packagefeedproxy.microsoft.io/npm/next/-/next-16.3.8.tgz?sig=fixture",
        "https://fixture:fixture@packagefeedproxy.microsoft.io/npm/next/-/next-16.3.8.tgz",
    ],
)
def test_unapproved_or_credential_bearing_sources_fail(tmp_path: Path, resolved: str) -> None:
    graph = _graph("/candidate")
    graph[1]["dependencies"] = {
        "next": {
            "version": "16.3.8",
            "path": "/candidate/node_modules/.pnpm/next@16.3.8/node_modules/next",
            "resolved": resolved,
        }
    }
    result = _capture(tmp_path, graph, "/candidate")
    assert result.returncode != 0
    assert "Unapproved or credential-bearing package resolution" in result.stderr
    assert not (tmp_path / "map.tsv").exists()


def test_incomplete_identity_fails_instead_of_emitting_a_partial_map(tmp_path: Path) -> None:
    result = _capture(
        tmp_path,
        [{"name": "ama", "path": "/candidate", "dependencies": {"next": {"version": "16.3.8"}}}],
        "/candidate",
    )
    assert result.returncode != 0
    assert "Incomplete installed package identity" in result.stderr
    assert not (tmp_path / "map.tsv").exists()


def test_windows_and_linux_copy_paths_have_the_same_installed_map(tmp_path: Path) -> None:
    windows = _capture(tmp_path, _graph(r"C:\candidate"), r"C:\candidate", "windows.tsv")
    linux = _capture(tmp_path, _graph("/candidate"), "/candidate", "linux.tsv")
    assert windows.returncode == linux.returncode == 0, windows.stderr + linux.stderr
    assert (tmp_path / "windows.tsv").read_bytes() == (tmp_path / "linux.tsv").read_bytes()


@pytest.mark.parametrize("graph", [[], {}, [{"name": "ama"}]])
def test_missing_importers_fail_explicitly(tmp_path: Path, graph: object) -> None:
    result = _capture(tmp_path, graph, "/candidate")
    assert result.returncode != 0
    assert not (tmp_path / "map.tsv").exists()
