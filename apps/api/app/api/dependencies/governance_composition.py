from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.repositories.governance_repository import GovernanceRepository
from app.services.governance_cache import GovernanceCacheService
from app.services.governance_registry import GovernanceRegistryService
from fastapi import FastAPI, Request

from packages.domain.src.domain.models.data_source import DataSource
from packages.domain.src.domain.seed import bootstrap as seed_bootstrap

logger = logging.getLogger(__name__)

SeedRecordsLoader = Callable[[], list[dict[str, Any]]]
_DEFAULT_COMPOSITION: GovernanceComposition | None = None


@dataclass
class GovernanceSeedStatus:
    attempts: int = 0
    successful: bool = False
    outcomes: list[dict[str, str]] = field(default_factory=list)
    last_error: str | None = None


@dataclass
class GovernanceComposition:
    repository: GovernanceRepository
    registry: GovernanceRegistryService
    cache: GovernanceCacheService
    backend_mode: str
    seed_status: GovernanceSeedStatus = field(default_factory=GovernanceSeedStatus)


def _is_test_runtime() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST")) or os.environ.get("AMA_TEST_SUPPORT") == "1"


def _resolve_backend_mode() -> str:
    mode = os.environ.get("AMA_GOVERNANCE_BACKEND_MODE", "auto").strip().lower()
    if mode not in {"auto", "durable", "in_memory"}:
        raise RuntimeError("AMA_GOVERNANCE_BACKEND_MODE must be one of: auto, durable, in_memory")

    if mode == "durable" and not os.environ.get("COSMOS_ENDPOINT"):
        raise RuntimeError("Startup blocked: durable governance backend mode requires COSMOS_ENDPOINT.")

    settings = get_settings()
    env = settings.environment.strip().lower()
    if mode == "in_memory" and env in {"production", "staging"} and not _is_test_runtime():
        raise RuntimeError("Startup blocked: in_memory governance backend mode is not allowed in production/staging.")

    if mode == "auto" and env == "production" and not os.environ.get("COSMOS_ENDPOINT") and not _is_test_runtime():
        raise RuntimeError("Startup blocked: production governance runtime requires durable COSMOS_ENDPOINT backend.")

    return mode


def _default_seed_loader() -> list[dict[str, Any]]:
    seed_root = Path(seed_bootstrap.__file__).resolve().parent
    return list(seed_bootstrap.bootstrap_seed_data(seed_root).get("data_sources", []))


def _build_composition() -> GovernanceComposition:
    backend_mode = _resolve_backend_mode()
    repository = GovernanceRepository()
    registry = GovernanceRegistryService(repository)
    cache = GovernanceCacheService()
    registry.set_cache_invalidator(
        lambda data_source_id, tenant_id: cache.invalidate(data_source_id, tenant_id=tenant_id)
    )
    return GovernanceComposition(
        repository=repository,
        registry=registry,
        cache=cache,
        backend_mode=backend_mode,
    )


def get_governance_composition(app: FastAPI | None = None) -> GovernanceComposition:
    global _DEFAULT_COMPOSITION

    if app is not None and hasattr(app.state, "governance_composition"):
        return app.state.governance_composition

    if app is not None:
        composition = _build_composition()
        app.state.governance_composition = composition
        app.state.governance_repository = composition.repository
        app.state.governance_registry = composition.registry
        app.state.governance_cache = composition.cache
        _DEFAULT_COMPOSITION = composition
        return composition

    if _DEFAULT_COMPOSITION is None:
        _DEFAULT_COMPOSITION = _build_composition()
    return _DEFAULT_COMPOSITION


def ensure_governance_seed_loaded(
    composition: GovernanceComposition,
    seed_loader: SeedRecordsLoader | None = None,
) -> GovernanceSeedStatus:
    if composition.seed_status.successful:
        return composition.seed_status

    loader = seed_loader or _default_seed_loader
    status = composition.seed_status
    status.attempts += 1
    outcomes: list[dict[str, str]] = []

    try:
        records = loader()
    except Exception as exc:
        status.successful = False
        status.last_error = str(exc)
        status.outcomes = [{"data_source_id": "<loader>", "outcome": "error", "error": str(exc)}]
        logger.warning("governance.seed_loader_failure", exc_info=True)
        return status

    for raw in records:
        data_source_id = str(raw.get("data_source_id", "<unknown>"))
        try:
            source = DataSource(**raw)
            if composition.repository.get_source(source.data_source_id):
                outcomes.append({"data_source_id": source.data_source_id, "outcome": "skipped_existing"})
                continue
            composition.registry.register_source(source, actor_id="system")
            outcomes.append({"data_source_id": source.data_source_id, "outcome": "imported"})
        except Exception as exc:
            outcomes.append({"data_source_id": data_source_id, "outcome": "error", "error": str(exc)})

    errors = [item for item in outcomes if item["outcome"] == "error"]
    status.successful = len(errors) == 0
    status.last_error = None if status.successful else f"{len(errors)} seed records failed"
    status.outcomes = outcomes

    if errors:
        logger.warning("governance.seed_import_partial_failure", extra={"error_count": len(errors)})

    return status


def initialize_governance_composition(app: FastAPI) -> GovernanceComposition:
    composition = get_governance_composition(app)
    loader = getattr(app.state, "governance_seed_loader", None)
    ensure_governance_seed_loaded(composition, seed_loader=loader)
    return composition


def get_governance_registry(request: Request) -> GovernanceRegistryService:
    return get_governance_composition(request.app).registry


def get_governance_cache(request: Request) -> GovernanceCacheService:
    return get_governance_composition(request.app).cache


def get_governance_repository(request: Request) -> GovernanceRepository:
    return get_governance_composition(request.app).repository
