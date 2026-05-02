"""Tests for the DORA metrics publishing script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "dora_metrics_publish.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("dora_metrics_publish", _SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_paged_reads_workflow_runs_from_github_collection_object(monkeypatch):
    script = _load_script()
    responses = [
        {
            "total_count": 1,
            "workflow_runs": [
                {
                    "head_branch": "main",
                    "updated_at": "2026-05-02T07:50:54Z",
                }
            ],
        }
    ]

    monkeypatch.setattr(script, "_get", lambda _url, _token: responses.pop(0))

    assert list(script._paged("https://api.github.com/repos/example/actions/runs", "token", "workflow_runs")) == [
        {
            "head_branch": "main",
            "updated_at": "2026-05-02T07:50:54Z",
        }
    ]


def test_paged_reads_issue_lists_without_item_key(monkeypatch):
    script = _load_script()
    responses = [[{"number": 1, "labels": [{"name": "incident"}]}]]

    monkeypatch.setattr(script, "_get", lambda _url, _token: responses.pop(0))

    assert list(script._paged("https://api.github.com/repos/example/issues", "token")) == [
        {"number": 1, "labels": [{"name": "incident"}]}
    ]
