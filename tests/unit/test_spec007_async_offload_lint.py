"""Spec-007 AUD-031 — the async simulation surface must offload blocking storage I/O."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.lint.check_spec007_async_offload import SURFACE, run

pytestmark = pytest.mark.spec007_isolation

ROOT = Path(__file__).resolve().parents[2]


def _module(tmp_path: Path, source: str) -> tuple[Path, tuple[str, ...]]:
    relative = "sample_module.py"
    (tmp_path / relative).write_text(source, encoding="utf-8")
    return tmp_path, (relative,)


def test_repository_surface_has_no_unoffloaded_storage_calls() -> None:
    assert run(ROOT) == []


def test_declared_surface_modules_all_exist() -> None:
    missing = [relative for relative in SURFACE if not (ROOT / relative).exists()]
    assert missing == []


def test_direct_cosmos_call_in_async_def_is_reported(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "async def save(container, doc):\n    container.upsert_item(doc)\n",
    )

    failures = run(root, surface)

    assert any("'upsert_item' is called on the event loop" in failure for failure in failures)


def test_blocking_repository_facade_in_async_def_is_reported(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "async def read(events, tenant_id):\n    return events.get_scheduler_state(tenant_id)\n",
    )

    failures = run(root, surface)

    assert any("'get_scheduler_state' is called on the event loop" in failure for failure in failures)


def test_nested_blocking_call_inside_list_is_reported(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "async def read(container):\n    return list(container.query_items('SELECT * FROM c'))\n",
    )

    failures = run(root, surface)

    assert any("'query_items' is called on the event loop" in failure for failure in failures)


def test_bare_to_thread_is_reported(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "import asyncio\n\n\nasync def read(container):\n    return await asyncio.to_thread(container.read_item, 'a')\n",  # noqa: E501
    )

    failures = run(root, surface)

    assert any("bare asyncio.to_thread escapes the shared bound" in failure for failure in failures)


def test_run_blocking_wrapper_is_accepted(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "from app.core.async_io import run_blocking\n\n\n"
        "async def save(container, doc):\n"
        "    await run_blocking(container.upsert_item, doc)\n"
        "    return await run_blocking(lambda: list(container.query_items('SELECT * FROM c')))\n",
    )

    assert run(root, surface) == []


def test_synchronous_helper_is_not_reported(tmp_path: Path) -> None:
    root, surface = _module(
        tmp_path,
        "def save(container, doc):\n    container.upsert_item(doc)\n",
    )

    assert run(root, surface) == []


def test_missing_surface_module_is_reported(tmp_path: Path) -> None:
    failures = run(tmp_path, ("apps/api/app/services/warp_scheduler.py",))

    assert any("no longer exists" in failure for failure in failures)
