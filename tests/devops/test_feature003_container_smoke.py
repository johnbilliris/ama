from __future__ import annotations

from pathlib import Path

API_DOCKERFILE = Path("apps/api/Dockerfile")
AGENTS_DOCKERFILE = Path("apps/agents/Dockerfile")
DEPENDENCY_INSTALLER = Path("scripts/install_pyproject_dependencies.py")
WORKFLOW_RUNS_ROUTE = Path("apps/api/app/api/routes/workflow_runs.py")
QUICKSTART = Path("specs/003-rubric-gap-closure/quickstart.md")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_api_image_copies_maf_runtime_for_workflow_runs_imports() -> None:
    docker_text = _text(API_DOCKERFILE)
    route_text = _text(WORKFLOW_RUNS_ROUTE)
    assert "from maf_runtime.repositories.workflow_run_repository" in route_text
    assert "from maf_runtime.workflow.run_state import WorkflowRunStatus" in route_text
    assert "COPY apps/agents/ ./apps/agents/" in docker_text


def test_api_dockerfile_uses_manifest_first_install_order() -> None:
    text = _text(API_DOCKERFILE)
    idx_pyproject = text.index("COPY apps/api/pyproject.toml")
    idx_dep_install = text.index("python ./scripts/install_pyproject_dependencies.py ./apps/api/pyproject.toml")
    idx_app_copy = text.index("COPY apps/api/app/")
    assert idx_pyproject < idx_dep_install < idx_app_copy
    assert "python - <<'PY'" not in text


def test_agents_dockerfile_uses_manifest_first_install_order() -> None:
    text = _text(AGENTS_DOCKERFILE)
    idx_pyproject = text.index("COPY apps/agents/pyproject.toml")
    idx_dep_install = text.index("python ./scripts/install_pyproject_dependencies.py ./apps/agents/pyproject.toml")
    idx_source_copy = text.index("COPY apps/agents/common/")
    assert idx_pyproject < idx_dep_install < idx_source_copy
    assert "python - <<'PY'" not in text


def test_dependency_installer_is_copied_into_both_builders() -> None:
    assert DEPENDENCY_INSTALLER.is_file()
    for dockerfile in (API_DOCKERFILE, AGENTS_DOCKERFILE):
        assert "COPY scripts/install_pyproject_dependencies.py ./scripts/" in _text(dockerfile)


def test_container_images_preserve_nonroot_and_dispatcher_startup() -> None:
    api_text = _text(API_DOCKERFILE)
    agents_text = _text(AGENTS_DOCKERFILE)
    assert "USER appuser" in api_text
    assert "USER appuser" in agents_text
    assert 'CMD ["uvicorn", "app.main:app"' in api_text
    assert "python -m dispatcher" in agents_text
    assert "RUN python -m uvicorn --version" in api_text
    assert "RUN python -m uvicorn --version" in agents_text


def test_quickstart_uses_root_build_context() -> None:
    text = _text(QUICKSTART)
    assert "docker build -f apps/api/Dockerfile -t drh-api ." in text
    assert "docker build -f apps/agents/Dockerfile -t drh-agents ." in text


def test_api_health_and_workflow_routes_are_present() -> None:
    route_text = _text(WORKFLOW_RUNS_ROUTE)
    assert '@router.get("", response_model=WorkflowRunsListResponse)' in route_text
    assert '@router.get("/{run_id}", response_model=dict[str, Any])' in route_text
