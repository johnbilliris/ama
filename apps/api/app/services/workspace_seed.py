"""Startup seeder for workspace coordination tasks (spec-035 follow-up).

The persona workspace UI
([`apps/web/src/app/workspaces/[personaId]/page.tsx`])
relies on coordination-task records to surface ``tasks[]`` and
``dependencies[]`` per persona. The seeder loads
``packages/domain/src/domain/seed/coordination_tasks_australia.json`` and
writes each entry through :class:`CoordinationTasksRepository`.

Storage path
------------
* When ``COSMOS_ENDPOINT`` is set the repository writes to the
  ``coordination_tasks`` Cosmos container AND mirrors into
  ``state_store.TASKS`` (in-process cache).
* When unset the repository uses ``state_store.TASKS`` directly.

The lifespan hook is best-effort: a malformed seed must NEVER prevent the
API from starting (see ``activation_mutex.py::_seed_workspace_tasks_safely``).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)

from packages.domain.src.domain.models.coordination_task import CoordinationTask

logger = logging.getLogger(__name__)

_SEED_RELATIVE: tuple[str, ...] = (
    "packages",
    "domain",
    "src",
    "domain",
    "seed",
    "coordination_tasks_australia.json",
)


def _resolve_seed_path() -> Path:
    """Locate the coordination-tasks seed for both repo and container layouts."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor.joinpath(*_SEED_RELATIVE)
        if candidate.exists():
            return candidate
    return here.parents[0] / "_missing_coordination_tasks_australia.json"


@lru_cache(maxsize=1)
def _load_raw_tasks() -> list[dict[str, object]]:
    path = _resolve_seed_path()
    if not path.exists():
        logger.warning(
            "coordination_tasks seed not found at %s; workspace tasks will be empty",
            path,
        )
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        logger.warning(
            "coordination_tasks seed at %s is not a list; ignoring",
            path,
        )
        return []
    return payload


def seed_workspace_tasks() -> int:
    """Idempotently upsert sample coordination tasks via the repository.

    Returns the number of tasks seeded so callers can log a single line at
    startup. The repository decides the destination — Cosmos when
    configured, in-memory otherwise — and always mirrors writes into
    ``state_store.TASKS`` for legacy read paths.
    """
    raw_tasks = _load_raw_tasks()
    repo = get_coordination_tasks_repository()
    seeded = 0
    for entry in raw_tasks:
        try:
            task = CoordinationTask.model_validate(entry)
        except Exception:  # noqa: BLE001 — seed entries are best-effort
            logger.exception(
                "Skipping malformed coordination task seed entry: %s",
                entry,
            )
            continue
        try:
            repo.upsert(task)
            seeded += 1
        except Exception:  # noqa: BLE001 — Cosmos hiccup must not block startup
            logger.exception(
                "Failed to upsert coordination task %s; continuing",
                task.task_id,
            )
    logger.info(
        "Workspace task seeder loaded %d coordination tasks (cosmos_backed=%s)",
        seeded,
        repo.is_cosmos_backed,
    )
    return seeded


def reset_seed_cache() -> None:
    """Test hook so each test run can re-read the seed file from disk."""
    _load_raw_tasks.cache_clear()


__all__ = ["seed_workspace_tasks", "reset_seed_cache"]
